#!/usr/bin/env python3
"""Run the standard RCM KB -> Graphify workflow.

This script intentionally keeps Graphify advisory: it validates the KB,
creates a curated corpus, then invokes Graphify against that corpus. Dry-run
mode prints the planned commands and does not require Graphify to be installed.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path


def python_executable() -> str:
    return sys.executable or "python3"


def run(cmd: list[str], *, dry_run: bool = False, check: bool = True) -> int:
    print("+ " + " ".join(cmd))
    if dry_run:
        return 0
    proc = subprocess.run(cmd, check=False)
    if check and proc.returncode != 0:
        raise SystemExit(proc.returncode)
    return proc.returncode


def main() -> int:
    parser = argparse.ArgumentParser(description="Build and query the RCM KB Graphify layer.")
    parser.add_argument("--root", default=".", help="Repository root. Default: current directory.")
    parser.add_argument("--corpus", default="graphify-kb-corpus", help="Generated corpus folder.")
    parser.add_argument(
        "--workflow",
        choices=("extract", "map"),
        default="extract",
        help=(
            "Graphify command style. 'extract' uses headless `graphify extract` for CI/API backends. "
            "'map' uses `graphify <corpus>` for assistant/interactive flags such as --no-viz and --wiki."
        ),
    )
    parser.add_argument("--backend", default=None, help="Graphify backend: openai, gemini, claude, claude-cli, ollama, bedrock, etc.")
    parser.add_argument("--model", default=None, help="Optional backend model name.")
    parser.add_argument("--max-concurrency", default=None, help="Extract workflow only: parallel semantic chunks. Use 1 for local LLMs.")
    parser.add_argument("--token-budget", default=None, help="Extract workflow only: per-chunk token cap. Use a smaller value for local LLMs.")
    parser.add_argument("--mode", default=None, help="Optional Graphify mode, for example: deep.")
    parser.add_argument("--update", action="store_true", help="Re-extract only changed files.")
    parser.add_argument("--force", action="store_true", help="Pass --force to Graphify.")
    parser.add_argument("--no-viz", action="store_true", help="Map workflow only: skip HTML visualization.")
    parser.add_argument("--wiki", action="store_true", help="Map workflow only: ask Graphify to generate a markdown wiki.")
    parser.add_argument("--skip-validate", action="store_true", help="Skip validate.py and rebuild_index.py.")
    parser.add_argument("--skip-build", action="store_true", help="Use an existing corpus without rebuilding it.")
    parser.add_argument("--dry-run", action="store_true", help="Print commands only.")
    args = parser.parse_args()

    if args.workflow == "extract" and (args.no_viz or args.wiki):
        print("--no-viz and --wiki are only valid with --workflow map.", file=sys.stderr)
        return 2
    if args.workflow == "map" and (args.backend or args.model):
        print("--backend and --model are only valid with --workflow extract.", file=sys.stderr)
        return 2
    if args.workflow == "map" and args.max_concurrency:
        print("--max-concurrency is only valid with --workflow extract.", file=sys.stderr)
        return 2
    if args.workflow == "map" and args.token_budget:
        print("--token-budget is only valid with --workflow extract.", file=sys.stderr)
        return 2

    root = Path(args.root).resolve()
    if not (root / "README.md").exists() or not (root / "_tools").exists():
        print("This does not look like the RCM AI Knowledge Base root.", file=sys.stderr)
        return 2

    py = python_executable()

    if not args.skip_validate:
        validate = root / "_tools" / "validate.py"
        rebuild = root / "_tools" / "rebuild_index.py"
        if validate.exists():
            run([py, str(validate)], dry_run=args.dry_run)
        if rebuild.exists():
            run([py, str(rebuild)], dry_run=args.dry_run)

    if not args.skip_build:
        builder = root / "_tools" / "build_graphify_corpus.py"
        run([py, str(builder), "--root", str(root), "--out", args.corpus], dry_run=args.dry_run)

    graphify = shutil.which("graphify")
    if not graphify:
        if args.dry_run:
            graphify = "graphify"
        else:
            print(
                "Graphify CLI was not found. Install it with one of:\n"
                "  uv tool install graphifyy\n"
                "  pipx install graphifyy\n",
                file=sys.stderr,
            )
            return 127

    corpus_path = str((root / args.corpus).resolve())
    if not args.dry_run and not Path(corpus_path).is_dir():
        print(f"Corpus folder not found: {corpus_path}", file=sys.stderr)
        return 2
    cmd = [graphify]
    if args.workflow == "extract":
        cmd.extend(["extract", corpus_path])
        if args.backend:
            cmd.extend(["--backend", args.backend])
        if args.model:
            cmd.extend(["--model", args.model])
        if args.max_concurrency:
            cmd.extend(["--max-concurrency", args.max_concurrency])
        if args.token_budget:
            cmd.extend(["--token-budget", args.token_budget])
    else:
        cmd.append(corpus_path)
    if args.mode:
        cmd.extend(["--mode", args.mode])
    if args.update:
        cmd.append("--update")
    if args.force:
        cmd.append("--force")
    if args.no_viz:
        cmd.append("--no-viz")
    if args.wiki:
        cmd.append("--wiki")

    return run(cmd, dry_run=args.dry_run)


if __name__ == "__main__":
    raise SystemExit(main())
