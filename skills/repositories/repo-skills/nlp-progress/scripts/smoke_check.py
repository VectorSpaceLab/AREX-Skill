#!/usr/bin/env python3
"""Smoke-check the bundled nlp-progress repo skill runtime files.

This script validates metadata files and bundled helper syntax/help without
requiring the original NLP-progress repository checkout.

Example:
  python3 scripts/smoke_check.py --skill-root /path/to/repo-skills/nlp-progress
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

REQUIRED_FILES = [
    "SKILL.md",
    "references/repo-provenance.md",
    "references/repo-routing-metadata.json",
    "references/corpus-overview.md",
    "references/troubleshooting.md",
    "sub-skills/benchmark-catalog/SKILL.md",
    "sub-skills/benchmark-catalog/scripts/index_nlp_progress.py",
    "sub-skills/structured-export/SKILL.md",
    "sub-skills/structured-export/scripts/export_nlp_progress.py",
    "sub-skills/content-maintenance/SKILL.md",
    "sub-skills/content-maintenance/scripts/check_nlp_progress_markdown.py",
]

SKILL_FILES = [
    "SKILL.md",
    "sub-skills/benchmark-catalog/SKILL.md",
    "sub-skills/structured-export/SKILL.md",
    "sub-skills/content-maintenance/SKILL.md",
]

HELP_SCRIPTS = [
    "sub-skills/benchmark-catalog/scripts/index_nlp_progress.py",
    "sub-skills/structured-export/scripts/export_nlp_progress.py",
    "sub-skills/content-maintenance/scripts/check_nlp_progress_markdown.py",
]


def check_frontmatter(path: Path, expected_name: str) -> list[str]:
    text = path.read_text(encoding="utf-8")
    errors: list[str] = []
    if not text.startswith("---\n"):
        return [f"{path}: missing YAML frontmatter fence"]
    front = text.split("---", 2)[1]
    required = [
        f"name: {expected_name}",
        "description: \"",
        "disable-model-invocation: true",
        "metadata:",
        "disco-role: operating",
    ]
    for needle in required:
        if needle not in front:
            errors.append(f"{path}: frontmatter missing {needle!r}")
    return errors


def run_help(script: Path) -> tuple[bool, str]:
    proc = subprocess.run(
        [sys.executable, str(script), "--help"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=20,
        check=False,
    )
    ok = proc.returncode == 0 and "usage:" in proc.stdout.lower()
    detail = (proc.stdout + proc.stderr).strip().splitlines()[:3]
    return ok, " | ".join(detail)


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate nlp-progress skill metadata and bundled helper scripts.")
    parser.add_argument("--skill-root", type=Path, default=Path(__file__).resolve().parents[1], help="Generated nlp-progress skill root")
    args = parser.parse_args()

    root = args.skill_root.resolve()
    errors: list[str] = []
    warnings: list[str] = []

    for rel in REQUIRED_FILES:
        if not (root / rel).is_file():
            errors.append(f"missing required file: {rel}")

    for rel in SKILL_FILES:
        expected = "nlp-progress" if rel == "SKILL.md" else Path(rel).parent.name
        path = root / rel
        if path.is_file():
            errors.extend(check_frontmatter(path, expected))

    routing_path = root / "references/repo-routing-metadata.json"
    if routing_path.is_file():
        try:
            metadata = json.loads(routing_path.read_text(encoding="utf-8"))
            if "nlp-progress" not in metadata.get("skills", {}):
                errors.append("routing metadata missing skills.nlp-progress")
        except json.JSONDecodeError as exc:
            errors.append(f"routing metadata is invalid JSON: {exc}")

    for rel in HELP_SCRIPTS:
        script = root / rel
        if script.is_file():
            ok, detail = run_help(script)
            if not ok:
                errors.append(f"helper --help failed for {rel}: {detail}")

    result = {
        "skill_root": root.name,
        "checked_required_files": len(REQUIRED_FILES),
        "checked_skill_frontmatter": len(SKILL_FILES),
        "checked_helper_help": len(HELP_SCRIPTS),
        "warnings": warnings,
        "errors": errors,
        "ok": not errors,
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
