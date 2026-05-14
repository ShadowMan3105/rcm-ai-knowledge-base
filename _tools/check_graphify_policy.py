#!/usr/bin/env python3
"""Check that the Graphify integration follows the RCM KB policy."""

from __future__ import annotations

import re
import sys
from pathlib import Path

REQUIRED_FILES = (
    "AGENTS.md",
    "GRAPHIFY_INTEGRATION.md",
    ".graphifyignore",
    ".env.example",
    "compose.local-ai.yml",
    "compose.existing-n8n.yml",
    "docker/graphify-runner.Dockerfile",
    "docs/local-graphify-n8n.md",
    "_graph/README.md",
    "_tools/build_graphify_corpus.py",
    "_tools/run_graphify_kb.py",
    "_tools/publish_graph_snapshot.py",
    "_tools/update_graph_snapshot.py",
    "_tools/check_graphify_policy.py",
    "_schema/graphify-agent-prompt.md",
)

REQUIRED_GITIGNORE_LINES = (
    ".graphify-kb-corpus/",
    "graphify-out/",
    ".graphify/",
    ".graphify_cache/",
    ".graphify_labels.json",
    ".env",
    ".env.*",
    "!.env.example",
)

REQUIRED_GRAPHIFYIGNORE_LINES = (
    "_graph/",
)

SECRET_REGEXES = (
    ("classic GitHub token", re.compile(r"ghp_[A-Za-z0-9_]{20,}")),
    ("fine-grained GitHub token", re.compile(r"github_pat_[A-Za-z0-9_]{20,}")),
    ("OpenAI-like key", re.compile(r"sk-[A-Za-z0-9]{20,}")),
    ("private key", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
)


def main() -> int:
    root = Path.cwd()
    errors: list[str] = []
    warnings: list[str] = []

    for filename in REQUIRED_FILES:
        if not (root / filename).exists():
            errors.append(f"Missing required Graphify integration file: {filename}")

    gitignore = root / ".gitignore"
    if gitignore.exists():
        lines = [line.strip() for line in gitignore.read_text(encoding="utf-8", errors="replace").splitlines()]
        for required in REQUIRED_GITIGNORE_LINES:
            if required not in lines:
                errors.append(f".gitignore must include: {required}")
    else:
        errors.append(".gitignore not found.")

    graphifyignore = root / ".graphifyignore"
    if graphifyignore.exists():
        lines = [line.strip() for line in graphifyignore.read_text(encoding="utf-8", errors="replace").splitlines()]
        for required in REQUIRED_GRAPHIFYIGNORE_LINES:
            if required not in lines:
                errors.append(f".graphifyignore must include: {required}")
    else:
        errors.append(".graphifyignore not found.")

    scan_names = set(REQUIRED_FILES) | {
        ".gitignore",
        ".graphifyignore",
        "README.md",
        "GRAPHIFY_INTEGRATION.md",
        "READ_PROTOCOL.md",
        "AI_PROTOCOL.md",
        "SETUP.md",
    }
    scan_paths = [root / filename for filename in sorted(scan_names) if (root / filename).exists()]
    for path in scan_paths:
        text = path.read_text(encoding="utf-8", errors="replace")
        for label, pattern in SECRET_REGEXES:
            if pattern.search(text):
                errors.append(f"Potential secret in {path}: {label}")

    for warning in warnings:
        print(f"WARN: {warning}")
    for error in errors:
        print(f"ERROR: {error}", file=sys.stderr)

    if errors:
        return 1
    print("Graphify policy check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
