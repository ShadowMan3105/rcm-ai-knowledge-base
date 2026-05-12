#!/usr/bin/env python3
"""Query the KB from the terminal.

Examples:
    python _tools/query.py --tag n8n --status active
    python _tools/query.py --domain automations
    python _tools/query.py --search "claims dedupe"
    python _tools/query.py --id KB-2026-0001-n8n-datatable-idempotent-upsert-pdf-parser --show report

Output is JSON-friendly by default (one entry per line, condensed),
or use --show to print a specific file of a matched entry.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def load_index() -> dict:
    p = ROOT / "index.json"
    if not p.exists():
        sys.exit("index.json not found. Run: python _tools/rebuild_index.py")
    return json.loads(p.read_text(encoding="utf-8"))


STATUS_RANK = {"active": 0, "proposed": 1, "challenged": 2, "deprecated": 3, "superseded": 3}
CONF_RANK = {"high": 0, "medium": 1, "low": 2}


def rank(e: dict) -> tuple:
    return (
        STATUS_RANK.get(e.get("status", ""), 9),
        CONF_RANK.get(e.get("confidence", ""), 9),
        -(int((e.get("last_verified") or "0000-00-00").replace("-", ""))),
    )


def matches(e: dict, args) -> bool:
    if args.id and e.get("id") != args.id:
        return False
    if args.domain and e.get("domain") != args.domain:
        return False
    if args.kind and e.get("kind") != args.kind:
        return False
    if args.status and e.get("status") != args.status:
        return False
    if args.tag:
        tags = set(e.get("tags", []))
        wanted = set(t.lower() for t in args.tag)
        if not (tags & wanted):
            return False
    if args.search:
        hay = " ".join([
            e.get("title", ""),
            e.get("summary", ""),
            " ".join(e.get("tags", [])),
        ]).lower()
        if not all(term.lower() in hay for term in args.search.split()):
            return False
    return True


def show_file(entry: dict, which: str) -> None:
    fp = ROOT / entry["path"] / f"{which}.md"
    if which == "meta":
        fp = ROOT / entry["path"] / "meta.json"
    if not fp.exists():
        sys.exit(f"file not found: {fp}")
    print(fp.read_text(encoding="utf-8"))


def main() -> int:
    p = argparse.ArgumentParser(description="Query the RCM AI Knowledge Base")
    p.add_argument("--id")
    p.add_argument("--domain", choices=[
        "automations", "research", "rcm-operations",
        "billing-config", "executive-reports", "consulting",
    ])
    p.add_argument("--kind", choices=[
        "blueprint", "lesson", "sop", "analysis", "playbook", "reference", "meta"
    ])
    p.add_argument("--status", choices=["proposed", "active", "challenged", "deprecated", "superseded"])
    p.add_argument("--tag", action="append", help="repeatable; matches any (OR)")
    p.add_argument("--search", help="space-separated terms, all must appear in title/summary/tags")
    p.add_argument("--limit", type=int, default=10)
    p.add_argument("--show", choices=["meta", "report", "lessons"], help="print the chosen file of the FIRST matched entry")
    p.add_argument("--verbose", "-v", action="store_true")
    args = p.parse_args()

    idx = load_index()
    hits = [e for e in idx.get("entries", []) if matches(e, args)]
    hits.sort(key=rank)

    if args.show:
        if not hits:
            sys.exit("no entries match — nothing to show")
        show_file(hits[0], args.show)
        return 0

    if not hits:
        print("(no matches)")
        return 1

    for e in hits[: args.limit]:
        if args.verbose:
            print(json.dumps(e, indent=2, ensure_ascii=False))
            print("---")
        else:
            print(f"{e['id']}  [{e['status']}/{e['confidence']}]  {e['title']}")
            print(f"    path: {e['path']}")
            print(f"    tags: {', '.join(e.get('tags', []))}")
            print()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
