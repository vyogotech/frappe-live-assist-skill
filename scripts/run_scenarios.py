#!/usr/bin/env python3
"""Scenario runner and validator for assistant skills.

Scenarios define end-to-end conversation flows that test:
- User prompt
- Expected tools called
- Expected records manipulated
- Forbidden actions (e.g. guessed field, duplicate creation, password in args, missing confirmation)
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("Error: PyYAML is required. Run 'pip install pyyaml'.", file=sys.stderr)
    sys.exit(1)


REQUIRED_SCENARIO_KEYS = {"skill", "title", "user_prompt", "expected_tools", "forbidden_actions"}


def validate_scenario_file(path: Path, available_skills: set[str]) -> list[str]:
    errors: list[str] = []
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return [f"Malformed YAML: {exc}"]

    if not isinstance(data, dict):
        return ["Scenario file must be a YAML mapping"]

    for key in REQUIRED_SCENARIO_KEYS:
        if key not in data:
            errors.append(f"Missing required field: '{key}'")

    skill_name = data.get("skill")
    if skill_name and skill_name not in available_skills:
        errors.append(f"Scenario references unknown skill '{skill_name}'")

    expected_tools = data.get("expected_tools")
    if not isinstance(expected_tools, list) or not expected_tools:
        errors.append("'expected_tools' must be a non-empty list")

    forbidden = data.get("forbidden_actions")
    if not isinstance(forbidden, list) or not forbidden:
        errors.append("'forbidden_actions' must be a non-empty list of invariants")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate and run assistant skill scenarios")
    parser.add_argument("--live", action="store_true", help="Execute against a live agent endpoint")
    parser.add_argument("--agent-url", default="http://localhost:8000", help="AI agent base URL")
    args = parser.parse_args()

    root = Path(__file__).resolve().parent.parent
    skills_dir = root / "skills"
    scenarios_dir = root / "scenarios"

    if not scenarios_dir.is_dir():
        print(f"Error: {scenarios_dir} directory not found", file=sys.stderr)
        return 1

    available_skills = {
        p.name for p in skills_dir.iterdir() if p.is_dir() and not p.name.startswith(".")
    }

    all_ok = True
    count = 0
    for scenario_file in sorted(scenarios_dir.glob("*.yaml")):
        count += 1
        errors = validate_scenario_file(scenario_file, available_skills)
        if errors:
            all_ok = False
            print(f"FAIL: {scenario_file.name}")
            for err in errors:
                print(f"  - {err}")
        else:
            print(f"OK:   {scenario_file.name}")

    if count == 0:
        print("Warning: No scenarios found to validate", file=sys.stderr)
        return 1

    if all_ok:
        print(f"\nAll {count} scenarios passed validation.")
        return 0
    else:
        print(f"\nScenario validation failed.", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
