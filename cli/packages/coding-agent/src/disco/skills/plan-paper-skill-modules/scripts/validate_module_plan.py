#!/usr/bin/env python3
"""Validate a paper module plan."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


REQUIRED_PLAN_FIELDS = ["schema_version", "paper_id", "title", "modules"]
REQUIRED_MODULE_FIELDS = [
    "id",
    "name",
    "skill_name",
    "summary",
    "inputs",
    "outputs",
    "insight",
    "test_strategy",
    "evidence",
]
SNAKE_RE = re.compile(r"^[a-z][a-z0-9_]*$")
SKILL_NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def require(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("module_plan", help="Path to module_plan.json.")
    parser.add_argument("--modules-dir", default="", help="Optional module docs directory.")
    args = parser.parse_args()

    plan_path = Path(args.module_plan).expanduser().resolve()
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    errors: list[str] = []

    for field in REQUIRED_PLAN_FIELDS:
        require(field in plan, f"missing top-level field: {field}", errors)

    modules = plan.get("modules", [])
    require(isinstance(modules, list), "modules must be a list", errors)
    require(1 <= len(modules) <= 5, "modules length must be between 1 and 5", errors)

    seen_ids: set[str] = set()
    seen_skills: set[str] = set()
    for idx, module in enumerate(modules):
        prefix = f"modules[{idx}]"
        require(isinstance(module, dict), f"{prefix} must be an object", errors)
        if not isinstance(module, dict):
            continue
        for field in REQUIRED_MODULE_FIELDS:
            require(field in module, f"{prefix} missing field: {field}", errors)
        module_id = str(module.get("id", ""))
        skill_name = str(module.get("skill_name", ""))
        require(bool(SNAKE_RE.match(module_id)), f"{prefix}.id must be snake_case", errors)
        require(
            bool(SKILL_NAME_RE.fullmatch(skill_name)) and len(skill_name) <= 64,
            f"{prefix}.skill_name must be a canonical lowercase-hyphen skill id of at most 64 characters",
            errors,
        )
        require(module_id not in seen_ids, f"duplicate module id: {module_id}", errors)
        require(skill_name not in seen_skills, f"duplicate skill name: {skill_name}", errors)
        seen_ids.add(module_id)
        seen_skills.add(skill_name)
        for list_field in ["inputs", "outputs", "evidence"]:
            value = module.get(list_field)
            require(isinstance(value, list) and bool(value), f"{prefix}.{list_field} must be a non-empty list", errors)
        for text_field in ["summary", "insight", "test_strategy"]:
            value = str(module.get(text_field, "")).strip()
            require(len(value) >= 20, f"{prefix}.{text_field} is too short", errors)

    if args.modules_dir:
        modules_dir = Path(args.modules_dir).expanduser().resolve()
        for module in modules if isinstance(modules, list) else []:
            if isinstance(module, dict) and module.get("id"):
                doc = modules_dir / f"{module['id']}.md"
                require(doc.exists(), f"missing module doc: {doc}", errors)

    result = {
        "ok": not errors,
        "module_plan": str(plan_path),
        "module_count": len(modules) if isinstance(modules, list) else 0,
        "errors": errors,
    }
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
