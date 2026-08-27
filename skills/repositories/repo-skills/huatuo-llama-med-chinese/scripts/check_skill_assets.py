#!/usr/bin/env python3
"""Check the Huatuo-Llama-Med-Chinese generated skill asset tree.

This is a safe static check. It does not inspect the original source checkout,
import model libraries, download weights, run inference, train, or export models.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

REQUIRED_FILES = [
    "SKILL.md",
    "references/repo-provenance.md",
    "references/repo-routing-metadata.json",
    "references/model-overview.md",
    "references/installation.md",
    "references/troubleshooting.md",
    "scripts/check_skill_assets.py",
    "sub-skills/inference/SKILL.md",
    "sub-skills/inference/references/workflows.md",
    "sub-skills/inference/references/cli-reference.md",
    "sub-skills/inference/references/troubleshooting.md",
    "sub-skills/inference/scripts/build_inference_command.py",
    "sub-skills/finetuning/SKILL.md",
    "sub-skills/finetuning/references/workflows.md",
    "sub-skills/finetuning/references/api-reference.md",
    "sub-skills/finetuning/references/troubleshooting.md",
    "sub-skills/finetuning/scripts/build_finetune_command.py",
    "sub-skills/prompt-data-formats/SKILL.md",
    "sub-skills/prompt-data-formats/references/prompt-templates.md",
    "sub-skills/prompt-data-formats/references/data-formats.md",
    "sub-skills/prompt-data-formats/references/benchmark.md",
    "sub-skills/prompt-data-formats/references/troubleshooting.md",
    "sub-skills/prompt-data-formats/scripts/validate_assets.py",
    "sub-skills/checkpoint-export/SKILL.md",
    "sub-skills/checkpoint-export/references/workflows.md",
    "sub-skills/checkpoint-export/references/troubleshooting.md",
    "sub-skills/checkpoint-export/scripts/build_export_command.py",
]

SUBSKILLS = ["inference", "finetuning", "prompt-data-formats", "checkpoint-export"]


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Static check for the generated Huatuo repo skill tree.")
    parser.add_argument("--skill-root", default=".", help="Generated skill root to check. Default: current directory.")
    return parser.parse_args(argv)


def frontmatter_block(text: str) -> str:
    if not text.startswith("---\n"):
        return ""
    try:
        return text.split("---\n", 2)[1]
    except IndexError:
        return ""


def check_frontmatter(path: Path, expected_name: str, errors: list[str]) -> None:
    text = path.read_text(encoding="utf-8")
    fm = frontmatter_block(text)
    if not fm:
        errors.append(f"{path}: missing YAML frontmatter")
        return
    required = [
        f"name: {expected_name}",
        "disable-model-invocation: true",
        "metadata:",
        "  disco-role: operating",
    ]
    for item in required:
        if item not in fm:
            errors.append(f"{path}: frontmatter missing {item!r}")
    if "description: \"" not in fm:
        errors.append(f"{path}: description must be double-quoted")


def main(argv: Sequence[str]) -> int:
    args = parse_args(argv)
    root = Path(args.skill_root).expanduser().resolve()
    errors: list[str] = []

    if not root.exists():
        print(f"error: skill root does not exist: {args.skill_root}", file=sys.stderr)
        return 2
    if not root.is_dir():
        print(f"error: skill root is not a directory: {args.skill_root}", file=sys.stderr)
        return 2

    for rel in REQUIRED_FILES:
        path = root / rel
        if not path.exists():
            errors.append(f"missing required file: {rel}")
        elif not path.is_file():
            errors.append(f"required path is not a file: {rel}")

    if (root / "SKILL.md").exists():
        check_frontmatter(root / "SKILL.md", "huatuo-llama-med-chinese", errors)
    for sid in SUBSKILLS:
        path = root / "sub-skills" / sid / "SKILL.md"
        if path.exists():
            check_frontmatter(path, sid, errors)

    metadata_path = root / "references" / "repo-routing-metadata.json"
    if metadata_path.exists():
        try:
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
            entry = metadata["skills"]["huatuo-llama-med-chinese"]["scenarios"]
            if not isinstance(entry, list) or not entry:
                errors.append("repo-routing-metadata.json: scenarios must be a non-empty list")
        except Exception as exc:  # noqa: BLE001 - user-facing validator
            errors.append(f"repo-routing-metadata.json: invalid structure: {exc}")

    pycache_dirs = [p for p in root.rglob("__pycache__") if p.is_dir()]
    if pycache_dirs:
        errors.append("runtime skill tree must not contain __pycache__ directories")

    private_fragments = ["/" + "root" + "/", "skills" + "/" + "tests"]
    for path in root.rglob("*"):
        if path.is_file() and path.suffix in {".md", ".json", ".py"}:
            text = path.read_text(encoding="utf-8", errors="ignore")
            if any(fragment in text for fragment in private_fragments):
                errors.append(f"private path leak candidate in {path.relative_to(root).as_posix()}")

    if errors:
        print("skill asset check failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    print("skill asset check passed")
    print(f"checked {len(REQUIRED_FILES)} required file(s) under {root.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
