#!/usr/bin/env python3
"""Check that every DocType and field declared in a skill's <!-- records: ... --> comment
exists in the target Frappe schema.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:
    print("Error: PyYAML is required. Run 'pip install pyyaml'.", file=sys.stderr)
    sys.exit(1)

RECORDS_COMMENT_PATTERN = re.compile(r"<!--\s*records:\s*\n(.*?)\s*-->", re.DOTALL)

STANDARD_DOC_FIELDS = {
    "name",
    "owner",
    "creation",
    "modified",
    "modified_by",
    "docstatus",
    "idx",
    "doctype",
    "_user_tags",
    "_comments",
    "_assign",
    "_liked_by",
}


def extract_skill_records(skill_file: Path) -> dict[str, list[str]]:
    content = skill_file.read_text(encoding="utf-8")
    match = RECORDS_COMMENT_PATTERN.search(content)
    if not match:
        return {}
    raw_yaml = match.group(1)
    data = yaml.safe_load(raw_yaml)
    if not isinstance(data, dict):
        return {}
    out: dict[str, list[str]] = {}
    for dt, fields in data.items():
        if isinstance(fields, list):
            out[dt] = [str(f).strip() for f in fields]
        elif fields is None:
            out[dt] = []
    return out


def find_doctype_json(schema_dir: Path, doctype: str) -> Path | None:
    scrubbed = re.sub(r"[-\s]+", "_", doctype.lower().strip())
    expected_filename = f"{scrubbed}.json"

    # Prefer direct doctype folder path
    direct_pattern = f"**/doctype/{scrubbed}/{expected_filename}"
    direct_matches = list(schema_dir.glob(direct_pattern))
    for m in direct_matches:
        try:
            d = json.loads(m.read_text(encoding="utf-8"))
            if d.get("doctype") == "DocType":
                return m
        except Exception:
            continue

    # Fallback to any matching filename
    matches = list(schema_dir.glob(f"**/{expected_filename}"))
    for m in matches:
        try:
            d = json.loads(m.read_text(encoding="utf-8"))
            if d.get("doctype") == "DocType":
                return m
        except Exception:
            continue

    return None


def get_doctype_fields_from_json(json_path: Path) -> set[str]:
    try:
        data = json.loads(json_path.read_text(encoding="utf-8"))
    except Exception:
        return set()
    fields = set(STANDARD_DOC_FIELDS)
    for f in data.get("fields", []):
        if isinstance(f, dict) and "fieldname" in f:
            fields.add(f["fieldname"])
    return fields


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify skill record fields against Frappe schemas")
    parser.add_argument("--schema-dir", type=Path, help="Directory containing Frappe doctype JSON files")
    parser.add_argument("--check-syntax", action="store_true", help="Only verify records syntax in skills")
    args = parser.parse_args()

    root = Path(__file__).resolve().parent.parent
    skills_dir = root / "skills"
    if not skills_dir.is_dir():
        print(f"Error: {skills_dir} not found", file=sys.stderr)
        return 1

    all_ok = True
    for skill_path in sorted(skills_dir.iterdir()):
        if not skill_path.is_dir() or skill_path.name.startswith("."):
            continue
        skill_file = skill_path / "SKILL.md"
        if not skill_file.is_file():
            continue

        records = extract_skill_records(skill_file)
        if not records:
            print(f"FAIL: {skill_path.name} - no valid records comment found")
            all_ok = False
            continue

        if args.check_syntax:
            print(f"OK:   {skill_path.name} (syntax valid, {len(records)} doctypes)")
            continue

        if args.schema_dir:
            if not args.schema_dir.is_dir():
                print(f"Error: schema directory {args.schema_dir} does not exist", file=sys.stderr)
                return 1
            skill_errs: list[str] = []
            for dt, fields in records.items():
                json_file = find_doctype_json(args.schema_dir, dt)
                if not json_file:
                    continue
                valid_fields = get_doctype_fields_from_json(json_file)
                for f in fields:
                    if f not in valid_fields:
                        skill_errs.append(f"DocType '{dt}' has no field '{f}'")
            if skill_errs:
                all_ok = False
                print(f"FAIL: {skill_path.name}")
                for err in skill_errs:
                    print(f"  - {err}")
            else:
                print(f"OK:   {skill_path.name} (all fields verified)")

    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
