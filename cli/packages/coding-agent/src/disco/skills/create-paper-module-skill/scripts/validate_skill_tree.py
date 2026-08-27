#!/usr/bin/env python3
"""Validate a generated DisCo operating skill tree."""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import re
import subprocess
import sys
import traceback
from pathlib import Path


FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)
SKILL_NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def parse_frontmatter(text: str) -> dict[str, str]:
    match = FRONTMATTER_RE.match(text)
    if not match:
        return {}
    fields: dict[str, str] = {}
    for line in match.group(1).splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        fields[key.strip()] = value.strip().strip("'\"")
    return fields


def frontmatter_block(text: str) -> str:
    match = FRONTMATTER_RE.match(text)
    return match.group(1) if match else ""


def has_double_quoted_description(text: str) -> bool:
    block = frontmatter_block(text)
    for line in block.splitlines():
        if line.startswith("description:"):
            value = line.split(":", 1)[1].strip()
            return len(value) >= 2 and value.startswith('"') and value.endswith('"')
    return False


def run_tests(skill_dir: Path) -> dict:
    tests_dir = skill_dir / "tests"
    if not tests_dir.exists() or not any(tests_dir.iterdir()):
        return {"attempted": False, "ok": True, "stdout": "", "stderr": "", "returncode": 0}
    env = os.environ.copy()
    scripts_dir = skill_dir / "scripts"
    env["PYTHONPATH"] = f"{scripts_dir}:{skill_dir}:{env.get('PYTHONPATH', '')}"
    if importlib.util.find_spec("pytest") is not None:
        cmd = [sys.executable, "-m", "pytest", str(tests_dir)]
        proc = subprocess.run(cmd, cwd=str(skill_dir), env=env, text=True, capture_output=True, timeout=120)
        return {
            "attempted": True,
            "ok": proc.returncode == 0,
            "runner": "pytest",
            "stdout": proc.stdout[-4000:],
            "stderr": proc.stderr[-4000:],
            "returncode": proc.returncode,
        }

    return run_simple_tests(skill_dir, tests_dir, scripts_dir)


def run_simple_tests(skill_dir: Path, tests_dir: Path, scripts_dir: Path) -> dict:
    """Run pytest-style test functions without requiring pytest."""
    old_path = list(sys.path)
    sys.path.insert(0, str(scripts_dir))
    sys.path.insert(0, str(skill_dir))
    failures: list[str] = []
    executed = 0
    try:
        for test_file in sorted(tests_dir.glob("test_*.py")):
            module_name = f"_skill_test_{test_file.stem}"
            spec = importlib.util.spec_from_file_location(module_name, test_file)
            if spec is None or spec.loader is None:
                failures.append(f"{test_file.name}: could not load module")
                continue
            module = importlib.util.module_from_spec(spec)
            try:
                spec.loader.exec_module(module)
            except Exception:
                failures.append(f"{test_file.name}: import failed\n{traceback.format_exc()}")
                continue
            for name in sorted(dir(module)):
                if not name.startswith("test_"):
                    continue
                obj = getattr(module, name)
                if not callable(obj):
                    continue
                executed += 1
                try:
                    obj()
                except Exception:
                    failures.append(f"{test_file.name}::{name}\n{traceback.format_exc()}")
    finally:
        sys.path[:] = old_path

    stdout = f"executed {executed} test functions with simple runner"
    stderr = "\n".join(failures)
    return {
        "attempted": True,
        "ok": not failures,
        "runner": "simple",
        "stdout": stdout,
        "stderr": stderr[-4000:],
        "returncode": 0 if not failures else 1,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("skill_dir", help="Skill directory.")
    parser.add_argument("--run-tests", action="store_true", help="Run pytest if tests exist.")
    args = parser.parse_args()

    skill_dir = Path(args.skill_dir).expanduser().resolve()
    errors: list[str] = []
    warnings: list[str] = []

    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        errors.append("missing SKILL.md")
        text = ""
        frontmatter = {}
    else:
        text = skill_md.read_text(encoding="utf-8", errors="replace")
        frontmatter = parse_frontmatter(text)
        if not frontmatter:
            errors.append("missing YAML frontmatter")
        name = frontmatter.get("name", "")
        description = frontmatter.get("description", "")
        if frontmatter.get("disco-role") != "operating":
            errors.append("frontmatter metadata.disco-role must be operating")
        if not has_double_quoted_description(text):
            errors.append("frontmatter description must be double-quoted")
        if not SKILL_NAME_RE.fullmatch(name) or len(name) > 64:
            errors.append("frontmatter name must be a canonical lowercase-hyphen skill id of at most 64 characters")
        if name != skill_dir.name:
            errors.append("frontmatter name must match the skill directory basename")
        if len(description.split()) < 8:
            errors.append("frontmatter description is too short to trigger reliably")
        if "TODO" in text or "TBD" in text:
            errors.append("SKILL.md contains TODO/TBD")
        if len(text.split()) < 120:
            warnings.append("SKILL.md is very short")

    scripts = sorted((skill_dir / "scripts").glob("*.py")) if (skill_dir / "scripts").exists() else []
    tests = sorted((skill_dir / "tests").glob("test_*.py")) if (skill_dir / "tests").exists() else []
    if scripts and not tests:
        warnings.append("scripts exist but no pytest tests were found")

    test_result = {"attempted": False, "ok": True, "stdout": "", "stderr": "", "returncode": 0}
    if args.run_tests:
        test_result = run_tests(skill_dir)
        if not test_result["ok"]:
            errors.append("tests failed")

    result = {
        "ok": not errors,
        "skill_dir": str(skill_dir),
        "frontmatter": frontmatter,
        "script_count": len(scripts),
        "test_count": len(tests),
        "warnings": warnings,
        "errors": errors,
        "tests": test_result,
    }
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
