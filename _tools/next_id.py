#!/usr/bin/env python3
"""Print the next available KB entry ID for the current year.

Usage:
    python _tools/next_id.py <slug>
    python _tools/next_id.py n8n-retry-policy-pattern
"""
from __future__ import annotations

import json
import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOMAINS = ["automations", "research", "rcm-operations", "billing-config", "executive-reports", "consulting"]


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: next_id.py <kebab-slug>", file=sys.stderr)
        return 2
    slug = sys.argv[1].lower()
    if not re.match(r"^[a-z0-9][a-z0-9-]*$", slug):
        print(f"slug must be kebab-case: {slug}", file=sys.stderr)
        return 2

    year = date.today().year
    pattern = re.compile(rf"^KB-{year}-(\d{{4}})-")
    max_n = 0
    for dom in DOMAINS:
        d = ROOT / dom
        if not d.is_dir():
            continue
        for meta in d.glob("*/meta.json"):
            try:
                data = json.loads(meta.read_text(encoding="utf-8"))
            except Exception:
                continue
            m = pattern.match(data.get("id", ""))
            if m:
                max_n = max(max_n, int(m.group(1)))

    new_id = f"KB-{year}-{max_n + 1:04d}-{slug}"
    print(new_id)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
