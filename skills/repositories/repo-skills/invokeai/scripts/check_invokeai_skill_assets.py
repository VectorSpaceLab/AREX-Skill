#!/usr/bin/env python3
"""Check the bundled InvokeAI skill tree for required files and unsafe references."""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

REQUIRED = [
    "SKILL.md",
    "references/environment-and-install.md",
    "references/troubleshooting.md",
    "references/repo-provenance.md",
    "references/repo-routing-metadata.json",
    "sub-skills/operations-config/SKILL.md",
    "sub-skills/workflow-nodes/SKILL.md",
    "sub-skills/workflows-queues/SKILL.md",
    "sub-skills/model-management/SKILL.md",
]
SUB_SKILLS = ["operations-config", "workflow-nodes", "workflows-queues", "model-management"]
FORBIDDEN = [
    "/" + "root/",
    "/" + "share/",
    "github" + "-repos",
    "production" + "_batches",
    ".disco/" + "agent/envs",
    "skills/" + "tests/invokeai",
]


def parse_frontmatter(text: str) -> dict[str, str]:
    if not text.startswith("---\n"):
        return {}
    end = text.find("\n---\n", 4)
    if end == -1:
        return {}
    data: dict[str, str] = {}
    for line in text[4:end].splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        data[key.strip()] = value.strip().strip('"')
    return data


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("skill_root", nargs="?", default=Path(__file__).resolve().parents[1], type=Path)
    parser.add_argument("--json", action="store_true", help="Print JSON results")
    args = parser.parse_args()
    root = args.skill_root.resolve()
    errors: list[str] = []
    warnings: list[str] = []

    for rel in REQUIRED:
        if not (root / rel).exists():
            errors.append(f"missing required file: {rel}")

    root_fm = parse_frontmatter((root / "SKILL.md").read_text(encoding="utf-8")) if (root / "SKILL.md").exists() else {}
    if root_fm.get("name") != "invokeai":
        errors.append("root SKILL.md frontmatter name must be invokeai")
    if root_fm.get("disable-model-invocation") != "true":
        errors.append("root SKILL.md must include disable-model-invocation: true")

    for sub in SUB_SKILLS:
        path = root / "sub-skills" / sub / "SKILL.md"
        if not path.exists():
            continue
        fm = parse_frontmatter(path.read_text(encoding="utf-8"))
        if fm.get("name") != sub:
            errors.append(f"{sub} frontmatter name mismatch: {fm.get('name')!r}")
        if fm.get("disable-model-invocation") != "true":
            errors.append(f"{sub} missing disable-model-invocation: true")

    try:
        metadata = json.loads((root / "references" / "repo-routing-metadata.json").read_text(encoding="utf-8"))
        if "invokeai" not in metadata.get("skills", {}):
            errors.append("repo-routing-metadata.json missing skills.invokeai")
    except Exception as exc:
        errors.append(f"repo-routing-metadata.json invalid: {exc}")

    for path in root.rglob("*"):
        if not path.is_file() or path.suffix in {".pyc", ".png", ".jpg", ".jpeg", ".gif", ".webp"}:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for token in FORBIDDEN:
            if token in text:
                errors.append(f"forbidden local/artifact reference {token!r} in {path.relative_to(root)}")
        if re.search(r"\]\((?:/|file:|https://github.com/invoke-ai/InvokeAI/blob)", text):
            warnings.append(f"check external/absolute Markdown link in {path.relative_to(root)}")

    result = {"ok": not errors, "errors": errors, "warnings": warnings, "root": str(root)}
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print("OK" if result["ok"] else "FAILED")
        for item in errors:
            print(f"ERROR: {item}", file=sys.stderr)
        for item in warnings:
            print(f"WARNING: {item}", file=sys.stderr)
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
