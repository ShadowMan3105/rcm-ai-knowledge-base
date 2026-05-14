#!/usr/bin/env python3
"""Build a curated Markdown corpus for Graphify from the RCM AI Knowledge Base.

The generated folder is intentionally derived and local-only. It gives Graphify a
clean Markdown-first view of JSON metadata, reports, lessons, challenges,
patches, schemas, and tooling without changing KB authority rules.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import shutil
import sys
from pathlib import Path
from typing import Any, Iterable

DOMAIN_DIRS = (
    "automations",
    "billing-config",
    "consulting",
    "executive-reports",
    "rcm-operations",
    "research",
)

PROTOCOL_FILES = (
    "README.md",
    "READ_PROTOCOL.md",
    "AI_PROTOCOL.md",
    "SETUP.md",
    "CHANGELOG.md",
    "GRAPHIFY_INTEGRATION.md",
)

EXCLUDED_DIR_NAMES = {
    ".git",
    ".github",
    ".graphify-kb-corpus",
    "graphify-out",
    "__pycache__",
    ".venv",
    "venv",
    "env",
    "node_modules",
}

SENSITIVE_REGEXES = (
    ("classic_github_token", re.compile(r"ghp_[A-Za-z0-9_]{20,}")),
    ("fine_grained_github_token", re.compile(r"github_pat_[A-Za-z0-9_]{20,}")),
    ("openai_key", re.compile(r"sk-[A-Za-z0-9]{20,}")),
    ("private_key", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    ("possible_ssn", re.compile(r"\b\d{3}-\d{2}-\d{4}\b")),
)


def rel(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def read_text(path: Path, *, max_bytes: int | None = None) -> str:
    data = path.read_bytes()
    truncated = False
    if max_bytes is not None and len(data) > max_bytes:
        data = data[:max_bytes]
        truncated = True
    text = data.decode("utf-8", errors="replace")
    if truncated:
        text += "\n\n[TRUNCATED BY build_graphify_corpus.py]\n"
    return text


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # pragma: no cover - CLI diagnostics
        raise SystemExit(f"Failed to parse JSON: {path}: {exc}") from exc


def dump_json_for_md(value: Any) -> str:
    return json.dumps(value, indent=2, ensure_ascii=False, sort_keys=True)


def scan_sensitive(path: Path, text: str) -> list[str]:
    hits: list[str] = []
    for name, pattern in SENSITIVE_REGEXES:
        if pattern.search(text):
            hits.append(name)
    return hits


def fence(label: str, body: str, language: str = "") -> str:
    return f"## {label}\n\n```{language}\n{body.rstrip()}\n```\n"


def iter_entry_dirs(root: Path) -> Iterable[tuple[str, Path]]:
    for domain in DOMAIN_DIRS:
        domain_path = root / domain
        if not domain_path.is_dir():
            continue
        for child in sorted(domain_path.iterdir(), key=lambda p: p.name.lower()):
            if child.is_dir() and (child / "meta.json").exists():
                yield domain, child


def build_index_summary(root: Path) -> str:
    index_path = root / "index.json"
    if not index_path.exists():
        return "# index.json summary\n\n`index.json` was not found. Run `_tools/rebuild_index.py`.\n"

    data = load_json(index_path)
    lines = ["# index.json summary", "", "Generated from authoritative `index.json`.", ""]

    if isinstance(data, dict):
        stats = data.get("stats") or data.get("summary") or {}
        if stats:
            lines.extend(["## Stats", "", "```json", dump_json_for_md(stats), "```", ""])

        entries = data.get("entries") or data.get("items") or []
        if isinstance(entries, dict):
            entries = list(entries.values())
        if isinstance(entries, list):
            lines.extend(["## Entries", ""])
            for item in entries:
                if not isinstance(item, dict):
                    continue
                entry_id = item.get("id") or item.get("kb_id") or item.get("slug") or "unknown-id"
                title = item.get("title") or item.get("name") or "Untitled"
                domain = item.get("domain") or item.get("folder") or "unknown-domain"
                status = item.get("status") or "unknown-status"
                kind = item.get("kind") or "unknown-kind"
                tags = item.get("tags") or []
                path = item.get("path") or item.get("entry_path") or ""
                lines.append(f"- `{entry_id}` — {title} | domain: `{domain}` | kind: `{kind}` | status: `{status}` | tags: `{tags}` | path: `{path}`")
            lines.append("")

        challenges = data.get("open_challenges") or data.get("challenges") or []
        if challenges:
            lines.extend(["## Challenges", "", "```json", dump_json_for_md(challenges), "```", ""])
    else:
        lines.extend(["## Raw index", "", "```json", dump_json_for_md(data), "```", ""])

    return "\n".join(lines).rstrip() + "\n"


def build_entry_file(root: Path, domain: str, entry_dir: Path, max_revision_bytes: int) -> str:
    meta_path = entry_dir / "meta.json"
    meta = load_json(meta_path)
    entry_id = meta.get("id") or entry_dir.name
    title = meta.get("title") or entry_dir.name

    parts = [
        f"# KB Entry: {entry_id}",
        "",
        f"Title: {title}",
        f"Domain: {domain}",
        f"Source folder: `{rel(entry_dir, root)}`",
        "",
        "This file is generated for Graphify navigation. The authoritative source remains the original KB entry files.",
        "",
        "## Metadata",
        "",
        "```json",
        dump_json_for_md(meta),
        "```",
        "",
    ]

    for filename in ("report.md", "lessons.md"):
        source = entry_dir / filename
        if source.exists():
            parts.extend([f"## {filename}", "", read_text(source), ""])

    revisions_dir = entry_dir / "revisions"
    if revisions_dir.is_dir():
        revision_files = sorted(p for p in revisions_dir.rglob("*") if p.is_file())
        if revision_files:
            parts.extend(["## Revisions", ""])
            for revision in revision_files:
                parts.extend([
                    f"### {rel(revision, root)}",
                    "",
                    read_text(revision, max_bytes=max_revision_bytes),
                    "",
                ])

    return "\n".join(parts).rstrip() + "\n"


def copy_markdown_collection(root: Path, source_dir: str, out_dir: Path, pattern: str = "*.md") -> int:
    src = root / source_dir
    if not src.is_dir():
        return 0
    count = 0
    for path in sorted(src.rglob(pattern), key=lambda p: rel(p, root)):
        if any(part in EXCLUDED_DIR_NAMES for part in path.parts):
            continue
        target = out_dir / source_dir / path.relative_to(src)
        write_text(target, read_text(path))
        count += 1
    return count


def copy_tooling(root: Path, out_dir: Path) -> int:
    count = 0
    tools_dir = root / "_tools"
    if tools_dir.is_dir():
        for path in sorted(tools_dir.glob("*.py"), key=lambda p: p.name.lower()):
            target = out_dir / "tools" / path.name
            write_text(target, read_text(path))
            count += 1
    schema_dir = root / "_schema"
    if schema_dir.is_dir():
        for path in sorted(schema_dir.rglob("*"), key=lambda p: rel(p, root)):
            if not path.is_file():
                continue
            if path.suffix.lower() not in {".md", ".json", ".txt", ".yaml", ".yml"}:
                continue
            target = out_dir / "schema" / path.relative_to(schema_dir)
            write_text(target, read_text(path))
            count += 1
    return count


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a Graphify-friendly corpus from the RCM AI KB.")
    parser.add_argument("--root", default=".", help="Repository root. Default: current directory.")
    parser.add_argument("--out", default=".graphify-kb-corpus", help="Output corpus folder.")
    parser.add_argument("--clean", action="store_true", default=True, help="Delete existing output first. Default: true.")
    parser.add_argument("--no-clean", dest="clean", action="store_false", help="Do not delete existing output first.")
    parser.add_argument("--max-revision-bytes", type=int, default=20000, help="Max bytes copied per revision file.")
    parser.add_argument("--strict-secrets", action="store_true", help="Fail if obvious secrets are detected in generated corpus.")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    out_dir = (root / args.out).resolve()

    if not (root / "README.md").exists() or not (root / "_tools").exists():
        print("This does not look like the RCM AI Knowledge Base root.", file=sys.stderr)
        return 2

    if out_dir == root or root not in out_dir.parents:
        print(f"Refusing to write outside repository root: {out_dir}", file=sys.stderr)
        return 2

    if args.clean and out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    generated_at = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
    write_text(
        out_dir / "README.md",
        "\n".join(
            [
                "# Graphify Corpus for RCM AI Knowledge Base",
                "",
                f"Generated at: `{generated_at}`",
                "",
                "This folder is derived from the KB and should not be edited directly.",
                "Run `_tools/build_graphify_corpus.py` to rebuild it.",
                "",
                "Authority reminder: Graphify is advisory only. `AI_PROTOCOL.md`, `index.json`, `meta.json`, `report.md`, `lessons.md`, challenges, and patches remain authoritative.",
                "",
            ]
        ),
    )

    protocol_count = 0
    for filename in PROTOCOL_FILES:
        path = root / filename
        if path.exists():
            write_text(out_dir / "protocol" / filename, read_text(path))
            protocol_count += 1

    write_text(out_dir / "index" / "index-summary.md", build_index_summary(root))

    entry_count = 0
    for domain, entry_dir in iter_entry_dirs(root):
        content = build_entry_file(root, domain, entry_dir, args.max_revision_bytes)
        target = out_dir / "entries" / domain / f"{entry_dir.name}.md"
        write_text(target, content)
        entry_count += 1

    challenge_count = copy_markdown_collection(root, "challenges", out_dir, "CH-*.md")
    patch_count = copy_markdown_collection(root, "patches", out_dir, "PA-*.md")
    tooling_count = copy_tooling(root, out_dir)

    secret_hits: list[str] = []
    for path in sorted(out_dir.rglob("*"), key=lambda p: p.as_posix()):
        if not path.is_file():
            continue
        text = read_text(path)
        hits = scan_sensitive(path, text)
        if hits:
            secret_hits.append(f"{path.relative_to(out_dir).as_posix()}: {', '.join(hits)}")

    manifest = {
        "generated_at": generated_at,
        "source_root": str(root),
        "protocol_files": protocol_count,
        "entries": entry_count,
        "challenges": challenge_count,
        "patches": patch_count,
        "tooling_files": tooling_count,
        "secret_scan_hits": secret_hits,
    }
    write_text(out_dir / "manifest.json", dump_json_for_md(manifest) + "\n")

    print(f"Built Graphify corpus: {out_dir.relative_to(root).as_posix()}")
    print(f"Entries: {entry_count}; challenges: {challenge_count}; patches: {patch_count}; tooling/schema files: {tooling_count}")
    if secret_hits:
        print("Sensitive-pattern warnings:", file=sys.stderr)
        for hit in secret_hits:
            print(f"  - {hit}", file=sys.stderr)
        if args.strict_secrets:
            return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
