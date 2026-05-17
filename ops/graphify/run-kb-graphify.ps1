param(
    [string]$RepoRoot = "",
    [string]$LabRoot = "",
    [string]$EnvFile = "",
    [string]$Model = "claude-sonnet-4-5",
    [int]$TokenBudget = 1200,
    [int]$MaxOutputTokens = 8192,
    [string]$ChangedSince = "24 hours ago",
    [string]$NotifyUrl = "http://localhost:5800/webhook/graphify-status-rcm-kb",
    [string]$NotificationRoot = "",
    [int]$NotificationAttempts = 5,
    [ValidateSet("", "success", "failure")]
    [string]$NotifyOnlyStatus = "",
    [switch]$FlushNotificationsOnly,
    [switch]$CommitPush
)

$ErrorActionPreference = "Stop"

$ScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path

function Resolve-RequiredPath {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path,
        [Parameter(Mandatory = $true)]
        [string]$Label
    )

    if ([string]::IsNullOrWhiteSpace($Path)) {
        throw "$Label is empty"
    }
    if (!(Test-Path -LiteralPath $Path)) {
        throw "$Label not found: $Path"
    }
    return (Resolve-Path -LiteralPath $Path).Path
}

function Assert-ChildPath {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Child,
        [Parameter(Mandatory = $true)]
        [string]$Parent
    )

    $parentFull = [System.IO.Path]::GetFullPath($Parent).TrimEnd('\', '/')
    $childFull = [System.IO.Path]::GetFullPath($Child).TrimEnd('\', '/')
    $comparison = [System.StringComparison]::OrdinalIgnoreCase
    if (!$childFull.StartsWith($parentFull + [System.IO.Path]::DirectorySeparatorChar, $comparison)) {
        throw "Refusing filesystem operation outside expected parent. child=$childFull parent=$parentFull"
    }
}

if ([string]::IsNullOrWhiteSpace($RepoRoot)) {
    $RepoRoot = Join-Path $ScriptRoot "..\.."
}
$RepoRoot = Resolve-RequiredPath -Path $RepoRoot -Label "RepoRoot"

if ([string]::IsNullOrWhiteSpace($LabRoot)) {
    if (![string]::IsNullOrWhiteSpace($env:GRAPHIFY_LAB_ROOT)) {
        $LabRoot = $env:GRAPHIFY_LAB_ROOT
    } else {
        $LabRoot = $ScriptRoot
    }
}
$LabRoot = Resolve-RequiredPath -Path $LabRoot -Label "LabRoot"

if ([string]::IsNullOrWhiteSpace($EnvFile) -and ![string]::IsNullOrWhiteSpace($env:GRAPHIFY_ENV_FILE)) {
    $EnvFile = $env:GRAPHIFY_ENV_FILE
}

if ([string]::IsNullOrWhiteSpace($NotificationRoot)) {
    if (![string]::IsNullOrWhiteSpace($env:GRAPHIFY_NOTIFICATION_ROOT)) {
        $NotificationRoot = $env:GRAPHIFY_NOTIFICATION_ROOT
    } else {
        $NotificationRoot = Join-Path $LabRoot "out\notifications"
    }
}

$RunId = (Get-Date -Format "yyyyMMdd-HHmmss") + "-" + ([guid]::NewGuid().ToString("N").Substring(0, 8))
$PendingNotificationRoot = Join-Path $NotificationRoot "pending"
$SentNotificationRoot = Join-Path $NotificationRoot "sent"
$NotificationHistory = Join-Path $NotificationRoot "history.jsonl"

function Write-NotificationHistory {
    param([hashtable]$Event)

    New-Item -ItemType Directory -Path $NotificationRoot -Force | Out-Null
    $Event["recorded_at"] = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
    Add-Content -Path $NotificationHistory -Value ($Event | ConvertTo-Json -Compress -Depth 8) -Encoding UTF8
}

function New-GraphifyNotificationRecord {
    param(
        [Parameter(Mandatory = $true)]
        [ValidateSet("success", "failure")]
        [string]$Status,
        [string]$ErrorText = ""
    )

    New-Item -ItemType Directory -Path $PendingNotificationRoot -Force | Out-Null
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $statusText = if ($Status -eq "success") { "ejecucion exitosa" } else { "ejecucion fallida" }
    $message = "Graphify activado - $statusText - $timestamp"
    $record = [ordered]@{
        id = $RunId
        status = $Status
        timestamp = $timestamp
        message = $message
        notify_url = $NotifyUrl
        error = $ErrorText
        created_at = (Get-Date).ToString("o")
    }
    $path = Join-Path $PendingNotificationRoot "$RunId-$Status.json"
    $record | ConvertTo-Json -Depth 8 | Set-Content -Path $path -Encoding UTF8
    Write-NotificationHistory @{ event = "queued"; id = $RunId; status = $Status; path = $path }
    return $path
}

function Send-GraphifyNotificationRecord {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path
    )

    if ([string]::IsNullOrWhiteSpace($NotifyUrl)) {
        throw "NotifyUrl is empty"
    }

    $record = Get-Content -LiteralPath $Path -Raw | ConvertFrom-Json
    $payload = @{
        status = $record.status
        timestamp = $record.timestamp
    } | ConvertTo-Json -Compress

    $response = Invoke-RestMethod -Method Post -Uri $NotifyUrl -ContentType "application/json" -Body $payload -TimeoutSec 20
    if ($response.ok -ne $true) {
        throw "n8n webhook did not return ok=true"
    }
    if ($response.message -and $response.message.text -and $response.message.text.Trim() -ne $record.message.Trim()) {
        throw "Slack text mismatch. Expected '$($record.message)' but got '$($response.message.text.Trim())'"
    }
    return $response
}

function Flush-GraphifyNotificationOutbox {
    New-Item -ItemType Directory -Path $PendingNotificationRoot -Force | Out-Null
    New-Item -ItemType Directory -Path $SentNotificationRoot -Force | Out-Null

    $pending = Get-ChildItem -LiteralPath $PendingNotificationRoot -Filter "*.json" -File | Sort-Object LastWriteTime
    foreach ($item in $pending) {
        $sent = $false
        $lastError = ""
        for ($attempt = 1; $attempt -le $NotificationAttempts; $attempt++) {
            try {
                Send-GraphifyNotificationRecord -Path $item.FullName | Out-Null
                $dest = Join-Path $SentNotificationRoot $item.Name
                Move-Item -LiteralPath $item.FullName -Destination $dest -Force
                Write-NotificationHistory @{ event = "sent"; file = $item.Name; attempt = $attempt; destination = $dest }
                Write-Host "GRAPHIFY_NOTIFICATION_SENT file=$($item.Name) attempt=$attempt"
                $sent = $true
                break
            } catch {
                $lastError = $_.Exception.Message
                Write-Warning "Graphify Slack notification attempt $attempt failed for $($item.Name): $lastError"
                if ($attempt -lt $NotificationAttempts) {
                    Start-Sleep -Seconds ([Math]::Min(60, [Math]::Pow(2, $attempt)))
                }
            }
        }
        if (!$sent) {
            Write-NotificationHistory @{ event = "pending_after_retries"; file = $item.Name; error = $lastError }
            Write-Warning "Graphify notification remains pending: $($item.FullName)"
        }
    }
}

function Invoke-Native {
    param(
        [Parameter(Mandatory = $true)]
        [string]$FilePath,
        [Parameter(ValueFromRemainingArguments = $true)]
        [string[]]$ArgumentList
    )

    & $FilePath @ArgumentList
    if ($LASTEXITCODE -ne 0) {
        throw "Command failed with exit code ${LASTEXITCODE}: $FilePath $($ArgumentList -join ' ')"
    }
}

function Invoke-GitSyncBeforeRun {
    if (!$CommitPush) {
        return
    }
    $dirty = & git status --porcelain --untracked-files=no
    if ($LASTEXITCODE -ne 0) {
        throw "Unable to inspect git status"
    }
    if ($dirty) {
        throw "Tracked worktree is dirty before Graphify run. Requires clean repo before unattended publish."
    }
    Invoke-GitFetchWithRetry
    $behind = & git rev-list --count "HEAD..origin/main"
    if ($LASTEXITCODE -ne 0) {
        throw "Unable to compare local main to origin/main"
    }
    $ahead = & git rev-list --count "origin/main..HEAD"
    if ($LASTEXITCODE -ne 0) {
        throw "Unable to compare origin/main to local main"
    }
    if ([int]$behind -gt 0 -and [int]$ahead -eq 0) {
        Invoke-Native git "merge" "--ff-only" "origin/main"
    } elseif ([int]$behind -gt 0 -and [int]$ahead -gt 0) {
        throw "Local main and origin/main diverged before run. Refusing unattended publish."
    }
}

function Invoke-GitFetchWithRetry {
    $lastError = ""
    for ($attempt = 1; $attempt -le 3; $attempt++) {
        try {
            Invoke-Native git "fetch" "origin" "main:refs/remotes/origin/main"
            return
        } catch {
            $lastError = $_.Exception.Message
            Write-Warning "git fetch attempt $attempt failed: $lastError"
            if ($attempt -lt 3) {
                Start-Sleep -Seconds ([Math]::Min(30, [Math]::Pow(2, $attempt)))
            }
        }
    }
    throw "git fetch failed after 3 attempts. Last error: $lastError"
}

function Invoke-GitPushOnce {
    Invoke-Native git "push" "origin" "main"
}

try {
    if (!(Test-Path (Join-Path $RepoRoot "AGENTS.md")) -or !(Test-Path (Join-Path $RepoRoot "_tools"))) {
        throw "RepoRoot does not look like the RCM AI Knowledge Base root: $RepoRoot"
    }

    if ($FlushNotificationsOnly) {
        Flush-GraphifyNotificationOutbox
        return
    }

    if (![string]::IsNullOrWhiteSpace($NotifyOnlyStatus)) {
        New-GraphifyNotificationRecord -Status $NotifyOnlyStatus | Out-Null
        Flush-GraphifyNotificationOutbox
        return
    }

    $EnvFile = Resolve-RequiredPath -Path $EnvFile -Label "EnvFile"
    $ComposeFile = Resolve-RequiredPath -Path (Join-Path $LabRoot "compose.claude-graphify-lab.yml") -Label "Lab compose file"

    $env:LAB_CLAUDE_MODEL_ALIAS = $Model
    $env:LAB_TOKEN_BUDGET = "$TokenBudget"
    $env:GRAPHIFY_MAX_OUTPUT_TOKENS = "$MaxOutputTokens"

    Set-Location $RepoRoot
    Invoke-GitSyncBeforeRun
    Flush-GraphifyNotificationOutbox

    Invoke-Native python "_tools\validate.py"
    Invoke-Native python "_tools\rebuild_index.py"
    Invoke-Native python "_tools\build_graphify_corpus.py" `
        "--root" $RepoRoot `
        "--out" "graphify-kb-corpus-incremental" `
        "--changed-since" $ChangedSince `
        "--protocol-mode" "minimal" `
        "--tooling-mode" "changed" `
        "--skip-index-summary" `
        "--strict-secrets"

    Set-Location $LabRoot
    Invoke-Native docker "compose" "--env-file" $EnvFile "-f" $ComposeFile "up" "-d" "litellm-sonnet"

    $health = "http://localhost:4001/health/liveness"
    for ($i = 1; $i -le 30; $i++) {
        try {
            Invoke-RestMethod -Uri $health -TimeoutSec 3 | Out-Null
            break
        } catch {
            if ($i -eq 30) {
                throw "LiteLLM did not become healthy at $health"
            }
            Start-Sleep -Seconds 2
        }
    }

    $SourceCorpusPath = Join-Path $RepoRoot "graphify-kb-corpus-incremental"
    $WorkRoot = Join-Path $LabRoot "out\kb-real"
    Assert-ChildPath -Child $WorkRoot -Parent $LabRoot
    $WorkCorpus = Join-Path $WorkRoot "corpus"
    $WorkOut = Join-Path $WorkRoot "graph-output"
    if (Test-Path $WorkRoot) {
        Remove-Item -LiteralPath $WorkRoot -Recurse -Force
    }
    New-Item -ItemType Directory -Path $WorkRoot | Out-Null
    Copy-Item -LiteralPath $SourceCorpusPath -Destination $WorkCorpus -Recurse
    New-Item -ItemType Directory -Path $WorkOut | Out-Null

    Invoke-Native docker "compose" "--env-file" $EnvFile "-f" $ComposeFile "run" "--rm" "--no-deps" `
        "-v" "${WorkCorpus}:/kb-corpus" `
        "-v" "${WorkOut}:/kb-out" `
        "graphify-sonnet" `
        "graphify" "extract" "/kb-corpus" `
        "--backend" "ollama" `
        "--model" $Model `
        "--max-concurrency" "1" `
        "--token-budget" "$TokenBudget" `
        "--out" "/kb-out"

    $GraphOut = @(
        (Join-Path $WorkOut "graphify-out"),
        (Join-Path $WorkCorpus "graphify-out")
    ) | Where-Object { Test-Path (Join-Path $_ "graph.json") } | Select-Object -First 1
    if ([string]::IsNullOrWhiteSpace($GraphOut) -or !(Test-Path (Join-Path $GraphOut "graph.json"))) {
        throw "Graphify did not produce graph.json in $WorkOut or $WorkCorpus"
    }

    Set-Location $RepoRoot
    Invoke-Native python "_tools\publish_graph_snapshot.py" `
        "--graph-out" $GraphOut `
        "--dest" "_graph/incremental-latest" `
        "--backend" "bedrock-via-litellm-ollama-transport" `
        "--model-label" "bedrock:$Model"

    Invoke-Native python "_tools\validate.py"
    Invoke-Native python "_tools\check_graphify_policy.py"

    $graphStatus = git status --short -- _graph\incremental-latest index.json
    if ($CommitPush -and $graphStatus) {
        Invoke-Native git "add" "index.json" "_graph\incremental-latest"
        Invoke-Native git "commit" "-m" "graph: update incremental Claude snapshot"
        try {
            Invoke-GitPushOnce
        } catch {
            Write-Warning "Initial git push failed: $($_.Exception.Message)"
            Invoke-Native git "fetch" "origin" "main:refs/remotes/origin/main"
            $remoteAdvanced = & git rev-list --count "HEAD..origin/main"
            if ($LASTEXITCODE -ne 0) {
                throw "Unable to compare remote after push failure"
            }
            if ([int]$remoteAdvanced -gt 0) {
                throw "origin/main advanced during Graphify run. Snapshot was not pushed to avoid publishing stale graph output; next scheduled run will rebuild from latest main."
            }
            throw
        }
    } elseif ($CommitPush) {
        Write-Host "No _graph or index.json changes to commit."
    } else {
        Write-Host "Commit/push skipped; pass -CommitPush to publish to GitHub."
    }

    $graph = Get-Content (Join-Path $GraphOut "graph.json") -Raw | ConvertFrom-Json
    $nodes = @($graph.nodes).Count
    $edges = if ($graph.edges) { @($graph.edges).Count } elseif ($graph.links) { @($graph.links).Count } else { 0 }
    Write-Host "GRAPHIFY_KB_OK nodes=$nodes edges=$edges changed_since='$ChangedSince'"

    New-GraphifyNotificationRecord -Status "success" | Out-Null
    Flush-GraphifyNotificationOutbox
} catch {
    try {
        New-GraphifyNotificationRecord -Status "failure" -ErrorText $_.Exception.Message | Out-Null
        Flush-GraphifyNotificationOutbox
    } catch {
        Write-Warning "Unable to queue or flush Graphify failure notification: $($_.Exception.Message)"
    }
    throw
} finally {
    if (Test-Path -LiteralPath $LabRoot) {
        Set-Location $LabRoot
    }
}
