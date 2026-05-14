#!/usr/bin/env python3
"""Publish a controlled Graphify snapshot into _graph/.

This copies only the allowed Graphify artifacts that are useful to cloud AI
agents. Raw Graphify working folders stay local and ignored.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

ALLOWED_GRAPH_FILES = {
    "GRAPH_REPORT.md": "GRAPH_REPORT.md",
    "graph.json": "graph.json",
}

SECRET_REGEXES = (
    ("classic_github_token", re.compile(r"ghp_[A-Za-z0-9_]{20,}")),
    ("fine_grained_github_token", re.compile(r"github_pat_[A-Za-z0-9_]{20,}")),
    ("openai_key", re.compile(r"sk-[A-Za-z0-9]{20,}")),
    ("private_key", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    ("possible_ssn", re.compile(r"\b\d{3}-\d{2}-\d{4}\b")),
)


def run_capture(cmd: list[str], cwd: Path, *, empty: str = "UNKNOWN") -> str:
    try:
        proc = subprocess.run(cmd, cwd=cwd, check=False, text=True, capture_output=True)
    except FileNotFoundError:
        return "UNKNOWN"
    if proc.returncode != 0:
        return "UNKNOWN"
    return proc.stdout.strip() or empty


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def scan_sensitive(path: Path) -> list[str]:
    text = read_text(path)
    hits = []
    for label, pattern in SECRET_REGEXES:
        if pattern.search(text):
            hits.append(label)
    return hits


def validate_graph_json(path: Path) -> tuple[int | None, int | None]:
    data = json.loads(read_text(path))
    if not isinstance(data, dict):
        return None, None
    nodes = data.get("nodes")
    edges = data["edges"] if "edges" in data else data.get("links")
    node_count = len(nodes) if isinstance(nodes, list) else None
    edge_count = len(edges) if isinstance(edges, list) else None
    return node_count, edge_count


def main() -> int:
    parser = argparse.ArgumentParser(description="Publish Graphify output to a controlled _graph snapshot.")
    parser.add_argument("--root", default=".", help="Repository root. Default: current directory.")
    parser.add_argument("--graph-out", default="graphify-out", help="Raw Graphify output folder.")
    parser.add_argument("--dest", default="_graph", help="Controlled published graph folder.")
    parser.add_argument("--backend", default="ollama", help="Model backend label recorded in manifest.")
    parser.add_argument("--model-label", default=None, help="Model label recorded in manifest.")
    parser.add_argument("--source-commit", default=None, help="Source commit. Default: git rev-parse HEAD.")
    parser.add_argument("--dry-run", action="store_true", help="Print planned publication without writing files.")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    graph_out = (root / args.graph_out).resolve()
    dest = (root / args.dest).resolve()

    if not (root / "AGENTS.md").exists() or not (root / "_tools").exists():
        print("This does not look like the RCM AI Knowledge Base root.", file=sys.stderr)
        return 2
    if not graph_out.is_dir():
        print(f"Graphify output folder not found: {graph_out}", file=sys.stderr)
        return 2
    if dest == root or root not in dest.parents:
        print(f"Refusing to publish outside repository root: {dest}", file=sys.stderr)
        return 2

    missing = [name for name in ALLOWED_GRAPH_FILES if not (graph_out / name).exists()]
    if missing:
        print(f"Missing required Graphify output files: {', '.join(missing)}", file=sys.stderr)
        return 2

    copied_files = []
    sensitive_hits = []
    graph_counts = {"nodes": None, "edges": None}

    for source_name, target_name in ALLOWED_GRAPH_FILES.items():
        source = graph_out / source_name
        target = dest / target_name
        hits = scan_sensitive(source)
        if hits:
            sensitive_hits.append({"file": source_name, "hits": hits})
        if source_name == "graph.json":
            try:
                node_count, edge_count = validate_graph_json(source)
                graph_counts = {"nodes": node_count, "edges": edge_count}
            except Exception as exc:
                print(f"Invalid graph.json: {exc}", file=sys.stderr)
                return 2
        copied_files.append(target_name)
        if not args.dry_run:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)

    if sensitive_hits:
        print("Sensitive patterns found in Graphify output:", file=sys.stderr)
        for hit in sensitive_hits:
            print(f"  - {hit['file']}: {', '.join(hit['hits'])}", file=sys.stderr)
        return 3

    source_commit = args.source_commit or run_capture(["git", "rev-parse", "HEAD"], root)
    source_branch = run_capture(["git", "branch", "--show-current"], root)
    source_status = run_capture(["git", "status", "--short"], root, empty="clean")
    graphify_version = run_capture(["graphify", "--version"], root)
    generated_at = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")

    manifest = {
        "schema_version": "1.0",
        "generated_at": generated_at,
        "source_commit": source_commit,
        "source_branch": source_branch,
        "source_worktree_status": source_status,
        "backend": args.backend,
        "model": args.model_label or "UNKNOWN - requires: OLLAMA_MODEL or explicit --model-label",
        "graphify_version": graphify_version,
        "published_files": copied_files,
        "graph_counts": graph_counts,
        "verification": {
            "raw_graphify_output_committed": False,
            "controlled_snapshot_only": True,
            "secret_scan": "passed",
            "source_of_truth": "AGENTS.md, AI_PROTOCOL.md, index.json, meta.json, report.md, lessons.md, challenges/, patches/",
        },
        "advisory_notice": (
            "_graph is a navigation cache generated from governed KB files. "
            "Verify every conclusion against source KB files before acting."
        ),
    }

    readme = """# Published Graph Snapshot

This folder is a controlled, commit-safe Graphify snapshot generated from the
RCM AI Knowledge Base.

Read order for AI agents:

1. `AGENTS.md`
2. `READ_PROTOCOL.md`
3. `AI_PROTOCOL.md`
4. `index.json`
5. `_graph/GRAPH_REPORT.md`
6. `_graph/graph.json` only for navigation
7. Source `meta.json`, `report.md`, `lessons.md`, `challenges/`, and `patches/`

Rules:

- `_graph/` is advisory only.
- Do not treat inferred graph edges as KB truth.
- Do not edit active KB entries based only on graph output.
- Convert substantive graph findings into a challenge, patch, or governed KB entry.
- Raw `graphify-out/` and `.graphify-kb-corpus/` stay local and ignored.
"""

    if args.dry_run:
        print(f"Would publish {', '.join(copied_files)} to {dest.relative_to(root).as_posix()}/")
        print(json.dumps(manifest, indent=2, ensure_ascii=False))
        return 0

    write_text(dest / "manifest.json", json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
    write_text(dest / "README.md", readme)
    print(f"Published Graphify snapshot to {dest.relative_to(root).as_posix()}/")
    print(f"Files: {', '.join(copied_files)}, manifest.json, README.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
