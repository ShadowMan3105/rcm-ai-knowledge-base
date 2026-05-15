#!/usr/bin/env python3
"""Build, publish, and optionally commit the local Graphify snapshot.

Designed for local Docker or n8n-triggered jobs:

    python _tools/update_graph_snapshot.py --backend ollama --commit --push
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path


def run(cmd: list[str], *, cwd: Path, dry_run: bool = False) -> int:
    print("+ " + " ".join(cmd))
    if dry_run:
        return 0
    proc = subprocess.run(cmd, cwd=cwd, check=False)
    if proc.returncode != 0:
        raise SystemExit(proc.returncode)
    return proc.returncode


def capture(cmd: list[str], *, cwd: Path) -> str:
    proc = subprocess.run(cmd, cwd=cwd, check=False, text=True, capture_output=True)
    if proc.returncode != 0:
        return ""
    return proc.stdout.strip()


def has_changes(root: Path) -> bool:
    return bool(capture(["git", "status", "--short", "_graph", "index.json"], cwd=root))


def main() -> int:
    parser = argparse.ArgumentParser(description="Update the published _graph snapshot.")
    parser.add_argument("--root", default=".", help="Repository root. Default: current directory.")
    parser.add_argument("--backend", default="ollama", help="Graphify backend for extract workflow.")
    parser.add_argument("--model-label", default=None, help="Model label for _graph/manifest.json.")
    parser.add_argument("--corpus", default=None, help="Generated corpus folder. Default: graphify-kb-corpus or graphify-kb-corpus-incremental.")
    parser.add_argument("--graph-out", default=None, help="Raw Graphify output folder. Default: <corpus>/graphify-out.")
    parser.add_argument("--dest", default=None, help="Published graph snapshot folder. Default: _graph or _graph/incremental-latest.")
    parser.add_argument("--workflow", choices=("extract", "map"), default="extract", help="Graphify workflow.")
    parser.add_argument("--max-concurrency", default=None, help="Graphify extract max concurrency. Default for ollama: 1.")
    parser.add_argument("--token-budget", default=None, help="Graphify extract token budget. Default for ollama: 4000.")
    parser.add_argument("--changed-since", default=None, help="Build and publish an incremental graph from files changed since this git date, for example: '24 hours ago'.")
    parser.add_argument("--protocol-mode", choices=("full", "minimal", "changed", "none"), default=None, help="Protocol copy mode. Default for incremental: none; otherwise full.")
    parser.add_argument("--skip-index-summary", action="store_true", help="Do not include index-summary.md in the Graphify corpus.")
    parser.add_argument("--tooling-mode", choices=("full", "changed", "none"), default=None, help="Tool/schema copy mode. Default for incremental: changed; otherwise full.")
    parser.add_argument("--commit", action="store_true", help="Commit _graph and index.json changes.")
    parser.add_argument("--push", action="store_true", help="Push current branch after committing.")
    parser.add_argument("--message", default="graph: update published knowledge map", help="Commit message.")
    parser.add_argument("--skip-graphify", action="store_true", help="Publish existing raw graph output without running Graphify.")
    parser.add_argument("--dry-run", action="store_true", help="Print commands without changing files.")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    if not (root / "AGENTS.md").exists() or not (root / "_tools").exists():
        print("This does not look like the RCM AI Knowledge Base root.", file=sys.stderr)
        return 2

    py = sys.executable or "python3"
    incremental = bool(args.changed_since)
    corpus = args.corpus or ("graphify-kb-corpus-incremental" if incremental else "graphify-kb-corpus")
    dest = args.dest or ("_graph/incremental-latest" if incremental else "_graph")
    graph_out = args.graph_out or str(Path(corpus) / "graphify-out")
    max_concurrency = args.max_concurrency or ("1" if args.backend == "ollama" else None)
    token_budget = args.token_budget or ("4000" if args.backend == "ollama" else None)
    protocol_mode = args.protocol_mode or ("none" if incremental else "full")
    skip_index_summary = args.skip_index_summary or incremental
    tooling_mode = args.tooling_mode or ("changed" if incremental else "full")
    model_label = args.model_label or (
        f"{args.backend}:{os.environ['OLLAMA_MODEL']}" if args.backend == "ollama" and os.environ.get("OLLAMA_MODEL") else None
    )

    run([py, "_tools/validate.py"], cwd=root, dry_run=args.dry_run)
    run([py, "_tools/rebuild_index.py"], cwd=root, dry_run=args.dry_run)
    build_cmd = [
        py,
        "_tools/build_graphify_corpus.py",
        "--root",
        str(root),
        "--out",
        corpus,
        "--protocol-mode",
        protocol_mode,
        "--tooling-mode",
        tooling_mode,
        "--strict-secrets",
    ]
    if skip_index_summary:
        build_cmd.append("--skip-index-summary")
    if args.changed_since:
        build_cmd.extend(["--changed-since", args.changed_since])
    run(build_cmd, cwd=root, dry_run=args.dry_run)

    if not args.skip_graphify:
        if not shutil.which("graphify") and not args.dry_run:
            print(
                "Graphify CLI was not found. Install graphifyy in the runner container or host.",
                file=sys.stderr,
            )
            return 127
        graph_cmd = [py, "_tools/run_graphify_kb.py", "--skip-validate", "--skip-build", "--corpus", corpus, "--workflow", args.workflow]
        if args.workflow == "extract":
            graph_cmd.extend(["--backend", args.backend])
            if model_label:
                model_name = model_label.split(":", 1)[1] if ":" in model_label else model_label
                graph_cmd.extend(["--model", model_name])
            if max_concurrency:
                graph_cmd.extend(["--max-concurrency", max_concurrency])
            if token_budget:
                graph_cmd.extend(["--token-budget", token_budget])
        else:
            graph_cmd.extend(["--no-viz", "--wiki"])
        run(graph_cmd, cwd=root, dry_run=args.dry_run)

    publish_cmd = [
        py,
        "_tools/publish_graph_snapshot.py",
        "--graph-out",
        graph_out,
        "--dest",
        dest,
        "--backend",
        args.backend,
    ]
    if model_label:
        publish_cmd.extend(["--model-label", model_label])
    run(publish_cmd, cwd=root, dry_run=args.dry_run)

    if args.commit:
        run(["git", "add", "index.json", dest], cwd=root, dry_run=args.dry_run)
        if args.dry_run:
            print("+ git commit skipped in dry-run")
        elif has_changes(root):
            run(["git", "commit", "-m", args.message], cwd=root)
        else:
            print("No _graph or index.json changes to commit.")

    if args.push:
        if not args.commit:
            print("--push requires --commit so the published snapshot is auditable.", file=sys.stderr)
            return 2
        run(["git", "push"], cwd=root, dry_run=args.dry_run)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
