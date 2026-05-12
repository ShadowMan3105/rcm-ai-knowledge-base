#!/usr/bin/env python3
"""Validate all KB entries and challenges against their schemas.

Uses jsonschema if available; falls back to a built-in minimal validator
covering required fields, enums, and patterns from entry.schema.json /
challenge.schema.json. This keeps the tool runnable with stdlib only.

Exit code: 0 if all valid, 1 otherwise.

Usage:  python _tools/validate.py [--strict]
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCHEMA_DIR = ROOT / "_schema"

try:
    import jsonschema  # type: ignore
    HAVE_JSONSCHEMA = True
except Exception:
    HAVE_JSONSCHEMA = False


def load_json(p: Path) -> dict:
    with p.open("r", encoding="utf-8") as f:
        return json.load(f)


def validate_with_jsonschema(instance: dict, schema: dict) -> list[str]:
    v = jsonschema.Draft7Validator(schema)
    return [f"{'.'.join(map(str, e.path)) or '<root>'}: {e.message}" for e in v.iter_errors(instance)]


def validate_manual(instance: dict, schema: dict) -> list[str]:
    """Minimal validator: required, enum, pattern, type (str/array/null)."""
    errors: list[str] = []
    required = schema.get("required", [])
    props = schema.get("properties", {})

    for key in required:
        if key not in instance:
            errors.append(f"missing required field: {key}")

    additional = schema.get("additionalProperties", True)
    if additional is False:
        for k in instance.keys():
            if k not in props and k != "path":
                errors.append(f"unknown field: {k}")

    for key, val in instance.items():
        if key not in props:
            continue
        rule = props[key]
        types = rule.get("type")
        if types:
            if isinstance(types, str):
                types = [types]
            ok = False
            for t in types:
                if t == "string" and isinstance(val, str): ok = True
                elif t == "array" and isinstance(val, list): ok = True
                elif t == "object" and isinstance(val, dict): ok = True
                elif t == "null" and val is None: ok = True
                elif t == "integer" and isinstance(val, int) and not isinstance(val, bool): ok = True
                elif t == "boolean" and isinstance(val, bool): ok = True
            if not ok:
                errors.append(f"{key}: wrong type (expected {types}, got {type(val).__name__})")
                continue
        if "enum" in rule and val not in rule["enum"]:
            errors.append(f"{key}: value '{val}' not in enum {rule['enum']}")
        if "pattern" in rule and isinstance(val, str):
            if not re.match(rule["pattern"], val):
                errors.append(f"{key}: '{val}' does not match pattern {rule['pattern']}")
        if rule.get("type") == "array" and isinstance(val, list):
            item_rule = rule.get("items", {})
            if "pattern" in item_rule:
                for i, x in enumerate(val):
                    if isinstance(x, str) and not re.match(item_rule["pattern"], x):
                        errors.append(f"{key}[{i}]: '{x}' does not match pattern {item_rule['pattern']}")

    return errors


def validate(instance: dict, schema: dict) -> list[str]:
    return validate_with_jsonschema(instance, schema) if HAVE_JSONSCHEMA else validate_manual(instance, schema)


def parse_frontmatter(md_path: Path) -> dict | None:
    text = md_path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return None
    end = text.find("\n---", 3)
    if end < 0:
        return None
    block = text[3:end].strip()
    meta: dict = {}
    for line in block.splitlines():
        line = line.strip()
        if not line or ":" not in line:
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
    entry_schema = load_json(SCHEMA_DIR / "entry.schema.json")
    ch_schema = load_json(SCHEMA_DIR / "challenge.schema.json")

    n_ok = n_fail = 0
    ids_seen: dict[str, Path] = {}

    domains = ["automations", "research", "rcm-operations", "billing-config", "executive-reports", "consulting"]
    for dom in domains:
        for meta_path in sorted((ROOT / dom).glob("*/meta.json")) if (ROOT / dom).is_dir() else []:
            try:
                instance = load_json(meta_path)
            except Exception as e:
                print(f"FAIL  {meta_path.relative_to(ROOT)}: cannot parse json: {e}")
                n_fail += 1
                continue
            errs = validate(instance, entry_schema)
            entry_id = instance.get("id", "")
            if entry_id in ids_seen:
                errs.append(f"duplicate id: also seen in {ids_seen[entry_id].relative_to(ROOT)}")
            else:
                ids_seen[entry_id] = meta_path
            slug_expected = entry_id.split("-", 3)[-1] if entry_id.count("-") >= 3 else ""
            if slug_expected and meta_path.parent.name != slug_expected:
                errs.append(f"folder name '{meta_path.parent.name}' != id slug '{slug_expected}'")

            if errs:
                n_fail += 1
                print(f"FAIL  {meta_path.relative_to(ROOT)}")
                for e in errs:
                    print(f"      - {e}")
            else:
                n_ok += 1
                print(f"OK    {meta_path.relative_to(ROOT)}")

    ch_dir = ROOT / "challenges"
    if ch_dir.is_dir():
        for ch_file in sorted(ch_dir.glob("CH-*.md")):
            meta = parse_frontmatter(ch_file)
            if meta is None:
                print(f"FAIL  {ch_file.relative_to(ROOT)}: no frontmatter")
                n_fail += 1
                continue
            errs = validate(meta, ch_schema)
            if errs:
                n_fail += 1
                print(f"FAIL  {ch_file.relative_to(ROOT)}")
                for e in errs:
                    print(f"      - {e}")
            else:
                n_ok += 1
                print(f"OK    {ch_file.relative_to(ROOT)}")

    print(f"\n{n_ok} OK, {n_fail} FAIL  (validator: {'jsonschema' if HAVE_JSONSCHEMA else 'built-in'})")
    return 0 if n_fail == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
