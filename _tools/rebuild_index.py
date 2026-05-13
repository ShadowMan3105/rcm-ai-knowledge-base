#!/usr/bin/env python3
"""Rebuild index.json by walking domain folders.

AI agents must run this after creating/modifying any entry.
Never hand-edit index.json.

Usage:  python _tools/rebuild_index.py
"""
from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOMAINS = [
    ("automations",       "Automations",          "Workflow automations, AI agents, API integrations, Monday.com, n8n"),
    ("research",          "Research",             "Payer analysis, timely filing, taxonomy, NPI, regulatory"),
    ("rcm-operations",    "RCM Operations",       "SOPs, onboarding, biller maturation, denial management"),
    ("billing-config",    "Billing Configuration","eCW v12, 837P, clearinghouse, ERA/EFT"),
    ("executive-reports", "Executive Reports",    "Strategic summaries for ownership and management"),
    ("consulting",        "Consulting",           "Advisory engagements, gap analyses, roadmaps"),
]

PROJECTION_FIELDS = [
    "id", "title", "domain", "kind", "status", "confidence",
    "created_at", "created_by", "last_verified", "last_verified_by",
    "tags", "summary", "related", "supersedes", "superseded_by",
    "challenged_by", "human_approved_by",
]


def load_entry(meta_path: Path) -> dict | None:
    try:
        with meta_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"  ! skip {meta_path}: {e}", file=sys.stderr)
        return None
    data["path"] = meta_path.parent.relative_to(ROOT).as_posix() + "/"
    return data


def project(entry: dict) -> dict:
    out = {k: entry.get(k) for k in PROJECTION_FIELDS if k in entry}
    out["path"] = entry["path"]
    return out


def collect_challenges() -> list[dict]:
    ch_dir = ROOT / "challenges"
    if not ch_dir.is_dir():
        return []
    out = []
    for f in sorted(ch_dir.glob("CH-*.md")):
        meta = parse_frontmatter(f)
        if meta:
            meta["path"] = f.relative_to(ROOT).as_posix()
            out.append(meta)
    return out


def collect_patches() -> list[dict]:
    pa_dir = ROOT / "patches"
    if not pa_dir.is_dir():
        return []
    out = []
    for f in sorted(pa_dir.glob("PA-*.md")):
        meta = parse_frontmatter(f)
        if meta:
            meta["path"] = f.relative_to(ROOT).as_posix()
            out.append(meta)
    return out


def parse_frontmatter(md_path: Path) -> dict | None:
    """Minimal YAML frontmatter parser (key: value only, no nesting)."""
    try:
        text = md_path.read_text(encoding="utf-8")
    except Exception:
        return None
    if not text.startswith("---"):
        return None
    end = text.find("\n---", 3)
    if end < 0:
        return None
    block = text[3:end].strip()
    meta: dict = {}
    for line in block.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if ":" not in line:
            continue
        k, _, v = line.partition(":")
        v = v.strip()
        if v in ("null", "~", ""):
            meta[k.strip()] = None
        elif v.startswith("[") and v.endswith("]"):
            inner = v[1:-1].strip()
            meta[k.strip()] = [x.strip().strip('"').strip("'") for x in inner.split(",")] if inner else []
        else:
            meta[k.strip()] = v.strip('"').strip("'")
    return meta


def main() -> int:
    entries: list[dict] = []
    for dom_id, _, _ in DOMAINS:
        dom = ROOT / dom_id
        if not dom.is_dir():
            continue
        for meta in sorted(dom.glob("*/meta.json")):
            e = load_entry(meta)
            if e is None:
                continue
            entries.append(project(e))

    entries.sort(key=lambda e: e.get("id", ""))

    patches = collect_patches()

    index = {
        "kb_version": "2.1",
        "schema": "_schema/entry.schema.json",
        "protocol": "AI_PROTOCOL.md",
        "last_built": date.today().isoformat(),
        "maintainer": "Dr. Seidel",
        "description": "RCM AI Knowledge Base — multi-agent safe blueprints, lessons, and analyses.",
        "stats": {
            "total_entries": len(entries),
            "by_status": _count(entries, "status"),
            "by_domain": _count(entries, "domain"),
            "by_kind":   _count(entries, "kind"),
            "open_challenges": sum(1 for c in collect_challenges() if c.get("status") == "open"),
            "open_patches":    sum(1 for p in patches if p.get("status") == "open"),
        },
        "domains": [
            {"id": i, "label": l, "path": f"{i}/", "description": d}
            for i, l, d in DOMAINS
        ],
        "entries": entries,
        "challenges": collect_challenges(),
        "patches": patches,
    }

    out_path = ROOT / "index.json"
    out_path.write_text(json.dumps(index, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"index.json rebuilt: {len(entries)} entries, {len(index['challenges'])} challenges, {len(patches)} patches")
    return 0


def _count(entries: list[dict], field: str) -> dict[str, int]:
    out: dict[str, int] = {}
    for e in entries:
        v = e.get(field) or "unknown"
        out[v] = out.get(v, 0) + 1
    return dict(sorted(out.items()))


if __name__ == "__main__":
    raise SystemExit(main())
