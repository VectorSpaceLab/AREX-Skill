#!/usr/bin/env python3
"""Run a deterministic PandasAI skill-registry smoke.

This helper validates custom-skill decoration, duplicate-name protection, and
missing-docstring failure behavior without requiring any LLM provider.

Examples:
  python sub-skills/custom-skills/scripts/skill_registry_smoke.py
"""

from __future__ import annotations

import argparse
import json
from typing import Any


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate PandasAI skill registry behavior")
    parser.add_argument("--skill-name", default="demo_skill", help="custom name to register")
    args = parser.parse_args()

    report: dict[str, Any] = {"ok": False, "skill_name": args.skill_name}

    try:
        from pandasai.ee.skills import SkillType, skill
        from pandasai.ee.skills.manager import SkillsManager
    except Exception as exc:  # noqa: BLE001
        report.update({"stage": "import", "error": f"{type(exc).__name__}: {exc}"})
        print(json.dumps(report, indent=2, sort_keys=True))
        return 1

    SkillsManager.clear_skills()

    @skill(args.skill_name)
    def registered(value: int) -> int:
        """Return the input value unchanged."""
        return value

    duplicate_error = None
    try:
        SkillsManager.add_skills(SkillType(registered.func, name=args.skill_name, description=registered.description))
    except Exception as exc:  # noqa: BLE001
        duplicate_error = f"{type(exc).__name__}: {exc}"

    missing_docstring_error = None
    try:

        def no_docstring(value: int) -> int:
            return value

        SkillType(no_docstring)
    except Exception as exc:  # noqa: BLE001
        missing_docstring_error = f"{type(exc).__name__}: {exc}"

    report.update(
        {
            "ok": SkillsManager.skill_exists(args.skill_name) and duplicate_error is not None and missing_docstring_error is not None,
            "registry_size": len(SkillsManager.get_skills()),
            "registered_name": SkillsManager.get_skills()[0].name if SkillsManager.get_skills() else None,
            "duplicate_error": duplicate_error,
            "missing_docstring_error": missing_docstring_error,
            "skill_str": str(registered),
        }
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
