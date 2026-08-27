#!/usr/bin/env python3
"""Static checks for the bundled AI-Optimizer repo skill and target checkouts.

This helper is safe by default: it checks file existence, YAML-ish frontmatter,
relative Markdown links inside a skill tree, and optional target checkout layout.
It never imports reinforcement-learning packages, downloads data, or launches
training.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

REQUIRED_SKILL_FILES = [
    "SKILL.md",
    "references/repo-provenance.md",
    "references/repo-routing-metadata.json",
    "references/repository-map.md",
    "references/troubleshooting.md",
    "sub-skills/model-based-rl/SKILL.md",
    "sub-skills/model-based-rl/scripts/build_muzero_command.py",
    "sub-skills/multi-agent-rl/SKILL.md",
    "sub-skills/multi-agent-rl/scripts/build_easy_marl_command.py",
    "sub-skills/offline-rl/SKILL.md",
    "sub-skills/offline-rl/scripts/build_offline_rl_command.py",
    "sub-skills/offline-rl/scripts/build_pex_command.py",
    "sub-skills/offline-rl/scripts/validate_mdp_dataset_npz.py",
]

EXPECTED_SUBSKILLS = ["model-based-rl", "multi-agent-rl", "offline-rl"]

TARGET_CHECKOUT_PATHS = [
    "README.md",
    "modelbased-rl/README.md",
    "multiagent-rl/README.md",
    "multiagent-rl/easy-marl/README.md",
    "offline-rl-algorithms/README.md",
    "modelbased-rl/MuZero/main.py",
    "multiagent-rl/easy-marl/main_dqn.py",
    "offline-rl-algorithms/E2O/PEX-main/main_offline.py",
]

MARKDOWN_LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+)\)")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run safe static checks for the AI-Optimizer repo skill.")
    parser.add_argument("--skill-root", default=None, help="generated ai-optimizer skill root; default is parent of this script")
    parser.add_argument("--source-root", default=None, help="optional target AI-Optimizer checkout to check for expected files")
    parser.add_argument("--json", action="store_true", help="emit JSON instead of text")
    return parser.parse_args()


def default_skill_root() -> Path:
    return Path(__file__).resolve().parents[1]


def frontmatter(path: Path) -> Dict[str, str]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        raise ValueError("missing opening frontmatter marker")
    try:
        header = text.split("---\n", 2)[1]
    except IndexError as exc:
        raise ValueError("missing closing frontmatter marker") from exc
    values: Dict[str, str] = {}
    for line in header.splitlines():
        if ":" in line and not line.startswith(" "):
            key, value = line.split(":", 1)
            values[key.strip()] = value.strip().strip('"')
    return values


def check_frontmatter(skill_root: Path) -> List[str]:
    errors: List[str] = []
    skill_files = [skill_root / "SKILL.md"] + [skill_root / "sub-skills" / sid / "SKILL.md" for sid in EXPECTED_SUBSKILLS]
    for path in skill_files:
        try:
            values = frontmatter(path)
        except Exception as exc:
            errors.append(f"{path.relative_to(skill_root)}: {exc}")
            continue
        expected_name = skill_root.name if path == skill_root / "SKILL.md" else path.parent.name
        if values.get("name") != expected_name:
            errors.append(f"{path.relative_to(skill_root)}: name {values.get('name')!r} != {expected_name!r}")
        if values.get("disable-model-invocation") != "true":
            errors.append(f"{path.relative_to(skill_root)}: missing disable-model-invocation: true")
        text = path.read_text(encoding="utf-8")
        if "disco-role: operating" not in text:
            errors.append(f"{path.relative_to(skill_root)}: missing metadata.disco-role operating")
    return errors


def iter_markdown_files(root: Path) -> Iterable[Path]:
    yield from root.rglob("*.md")


def check_links(skill_root: Path) -> List[str]:
    errors: List[str] = []
    for path in iter_markdown_files(skill_root):
        text = path.read_text(encoding="utf-8")
        for match in MARKDOWN_LINK_RE.finditer(text):
            target = match.group(1).split("#", 1)[0]
            if not target or "://" in target or target.startswith("mailto:"):
                continue
            if target.startswith("/"):
                errors.append(f"{path.relative_to(skill_root)}: absolute link {target}")
                continue
            resolved = (path.parent / target).resolve()
            try:
                resolved.relative_to(skill_root.resolve())
            except ValueError:
                errors.append(f"{path.relative_to(skill_root)}: link leaves skill tree: {target}")
                continue
            if not resolved.exists():
                errors.append(f"{path.relative_to(skill_root)}: missing link target {target}")
    return errors


def check_required_files(skill_root: Path) -> List[str]:
    return [rel for rel in REQUIRED_SKILL_FILES if not (skill_root / rel).exists()]


def check_source_root(source_root: Path) -> Tuple[List[str], List[str]]:
    missing = [rel for rel in TARGET_CHECKOUT_PATHS if not (source_root / rel).exists()]
    present_submodules = []
    for rel in ["cornerstone", "self-supervised-rl", "transfer-and-multi-task-reinforcement-learning", "multiagent-rl/core"]:
        path = source_root / rel
        if path.exists() and any(path.iterdir()):
            present_submodules.append(rel)
    return missing, present_submodules


def main() -> int:
    args = parse_args()
    skill_root = Path(args.skill_root).resolve() if args.skill_root else default_skill_root()
    report: Dict[str, object] = {"skill_root": str(skill_root), "ok": True, "errors": [], "warnings": []}

    if not skill_root.exists():
        report["errors"].append(f"skill root does not exist: {skill_root}")
    else:
        missing = check_required_files(skill_root)
        if missing:
            report["errors"].append({"missing_required_files": missing})
        report["errors"].extend(check_frontmatter(skill_root))
        report["errors"].extend(check_links(skill_root))

    if args.source_root:
        source_root = Path(args.source_root).resolve()
        if not source_root.exists():
            report["errors"].append(f"source root does not exist: {source_root}")
        else:
            missing_source, initialized_submodules = check_source_root(source_root)
            report["source_root"] = str(source_root)
            if missing_source:
                report["warnings"].append({"missing_expected_source_paths": missing_source})
            if initialized_submodules:
                report["warnings"].append({"submodules_now_initialized_refresh_recommended": initialized_submodules})

    report["ok"] = not report["errors"]
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print("AI-Optimizer static check")
        print("ok:", "yes" if report["ok"] else "no")
        for warning in report["warnings"]:
            print("warning:", warning, file=sys.stderr)
        for error in report["errors"]:
            print("error:", error, file=sys.stderr)
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
