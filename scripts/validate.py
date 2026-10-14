#!/usr/bin/env python3
"""Validation script for assistant skills.

Enforces:
1. Frontmatter: valid YAML with name, description, and risk.
2. Naming: folder name must equal skill name.
3. Description: present, concise (<= 200 chars).
4. Risk classification: one of 'read-only', 'writes', 'always-ask'.
5. File size: <= 8192 bytes (8 KB).
6. Machine-readable record comment: <!-- records: ... --> present and valid YAML.
7. Safe invented data: no real emails or addresses outside test domains.
8. Credential safety: no passwords or password fields in instructions or examples.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("Error: PyYAML is required. Run 'pip install pyyaml'.", file=sys.stderr)
    sys.exit(1)

MAX_SIZE_BYTES = 8192
MAX_DESC_CHARS = 200
ALLOWED_RISKS = {"read-only", "writes", "always-ask"}
ALLOWED_EMAIL_DOMAINS = (".test", "example.com", "example.org", "example.net")

FRONTMATTER_PATTERN = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
RECORDS_COMMENT_PATTERN = re.compile(r"<!--\s*records:\s*\n(.*?)\s*-->", re.DOTALL)
EMAIL_PATTERN = re.compile(r"[\w\.-]+@([\w\.-]+\.\w+)")
PASSWORD_FIELD_PATTERN = re.compile(r'["\']?(?:new_password|password)["\']?\s*[:=]', re.IGNORECASE)


def validate_skill(skill_dir: Path) -> list[str]:
    errors: list[str] = []
    skill_file = skill_dir / "SKILL.md"

    if not skill_file.is_file():
        return [f"Missing SKILL.md in {skill_dir.name}"]

    raw_bytes = skill_file.read_bytes()
    if len(raw_bytes) > MAX_SIZE_BYTES:
        errors.append(
            f"File size {len(raw_bytes)} bytes exceeds limit of {MAX_SIZE_BYTES} bytes"
        )

    try:
        content = raw_bytes.decode("utf-8")
    except UnicodeDecodeError as exc:
        return [f"File is not valid UTF-8: {exc}"]

    # Frontmatter check
    fm_match = FRONTMATTER_PATTERN.match(content)
    if not fm_match:
        errors.append("Missing or malformed YAML frontmatter (must start with ---)")
        return errors

    fm_raw = fm_match.group(1)
    try:
        fm = yaml.safe_load(fm_raw)
    except Exception as exc:
        errors.append(f"Invalid YAML in frontmatter: {exc}")
        return errors

    if not isinstance(fm, dict):
        errors.append("Frontmatter must be a YAML mapping")
        return errors

    name = fm.get("name")
    if not name:
        errors.append("Frontmatter missing 'name'")
    elif name != skill_dir.name:
        errors.append(f"Skill name '{name}' does not match folder name '{skill_dir.name}'")

    desc = fm.get("description", "")
    if not desc:
        errors.append("Frontmatter missing 'description'")
    elif len(str(desc).strip()) > MAX_DESC_CHARS:
        errors.append(
            f"Description length ({len(str(desc))} chars) exceeds limit of {MAX_DESC_CHARS} chars"
        )

    risk = fm.get("risk")
    if not risk:
        errors.append(f"Frontmatter missing 'risk' (must be one of {sorted(ALLOWED_RISKS)})")
    elif risk not in ALLOWED_RISKS:
        errors.append(f"Invalid risk '{risk}'; must be one of {sorted(ALLOWED_RISKS)}")

    # Machine-readable records comment check
    body = content[fm_match.end() :]
    records_match = RECORDS_COMMENT_PATTERN.search(body)
    if not records_match:
        errors.append("Missing machine-readable '<!-- records: ... -->' comment")
    else:
        records_raw = records_match.group(1)
        try:
            records_data = yaml.safe_load(records_raw)
            if not isinstance(records_data, dict):
                errors.append("The 'records' comment must contain a YAML mapping of DocType to fields")
        except Exception as exc:
            errors.append(f"Invalid YAML in records comment: {exc}")

    # No password fields in examples/prompts
    if PASSWORD_FIELD_PATTERN.search(content):
        errors.append("Prohibited password field pattern detected in content")

    # Email domains check
    for email_match in EMAIL_PATTERN.finditer(content):
        domain = email_match.group(1).lower()
        if not any(domain == d.lstrip(".") or domain.endswith(d) for d in ALLOWED_EMAIL_DOMAINS):
            errors.append(
                f"Email address '{email_match.group(0)}' uses non-test domain '{domain}'"
            )

    return errors


def main() -> int:
    root = Path(__file__).resolve().parent.parent
    skills_dir = root / "skills"
    if not skills_dir.is_dir():
        print(f"Error: {skills_dir} directory not found", file=sys.stderr)
        return 1

    all_ok = True
    count = 0
    for skill_path in sorted(skills_dir.iterdir()):
        if not skill_path.is_dir() or skill_path.name.startswith("."):
            continue
        count += 1
        errors = validate_skill(skill_path)
        if errors:
            all_ok = False
            print(f"FAIL: {skill_path.name}")
            for err in errors:
                print(f"  - {err}")
        else:
            print(f"OK:   {skill_path.name}")

    if count == 0:
        print("Warning: No skills found to validate", file=sys.stderr)
        return 1

    if all_ok:
        print(f"\nAll {count} skills passed validation.")
        return 0
    else:
        print(f"\nValidation failed for one or more skills.", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
