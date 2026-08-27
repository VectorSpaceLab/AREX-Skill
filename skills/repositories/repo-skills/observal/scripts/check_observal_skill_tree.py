#!/usr/bin/env python3
"""Validate the generated Observal repo-skill tree.

This is a read-only helper for future agents. It checks runtime skill files,
frontmatter conventions, required references, routing metadata JSON, script
executability markers, and internal Markdown links. It does not import Observal
source code or write files.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

ROOT_REQUIRED = {
    "SKILL.md",
    "references/repo-provenance.md",
    "references/repo-routing-metadata.json",
    "references/overview.md",
    "references/quick-commands.md",
    "references/troubleshooting.md",
}

EXPECTED_SUBSKILLS = {
    "cli": ["references/cli-architecture.md", "references/command-workflows.md", "references/bundled-skills.md", "references/troubleshooting.md", "scripts/check_cli_contract.py"],
    "server": ["references/server-architecture.md", "references/api-data-workflows.md", "references/migrations-and-settings.md", "references/troubleshooting.md", "scripts/check_server_routes.py"],
    "harness-telemetry": ["references/harness-support.md", "references/telemetry-pipeline.md", "references/session-parsers.md", "references/troubleshooting.md", "scripts/check_harness_registry.py"],
    "web": ["references/frontend-architecture.md", "references/api-hooks-and-types.md", "references/ui-testing.md", "references/troubleshooting.md", "scripts/check_web_contract.py"],
    "repo-development": ["references/development-workflow.md", "references/testing-and-quality.md", "references/repo-scripts.md", "references/troubleshooting.md", "scripts/inspect_observal_repo.py"],
}

LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
CANONICAL_ID = re.compile(r"^[a-z0-9][a-z0-9-]{0,63}$")


@dataclass
class Result:
    ok: bool
    label: str
    detail: str


def add(results: list[Result], ok: bool, label: str, detail: str) -> None:
    results.append(Result(ok, label, detail))


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def parse_frontmatter(path: Path) -> dict[str, str | bool]:
    text = read_text(path)
    if not text.startswith("---\n"):
        return {}
    try:
        block = text.split("---\n", 2)[1]
    except IndexError:
        return {}
    data: dict[str, str | bool] = {}
    lines = block.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        if not line.strip() or line.startswith("#"):
            i += 1
            continue
        if line.startswith("metadata:"):
            i += 1
            while i < len(lines) and lines[i].startswith("  "):
                key, _, value = lines[i].strip().partition(":")
                if key == "disco-role":
                    data["metadata.disco-role"] = value.strip()
                i += 1
            continue
        key, sep, value = line.partition(":")
        if sep:
            raw = value.strip()
            if raw == "true":
                data[key] = True
            elif raw == "false":
                data[key] = False
            else:
                data[key] = raw.strip('"')
                if key == "description":
                    data["description_raw"] = raw
        i += 1
    return data


def check_skill_md(results: list[Result], path: Path, expected_name: str) -> None:
    if not path.is_file():
        add(results, False, str(path), "missing")
        return
    fm = parse_frontmatter(path)
    add(results, fm.get("name") == expected_name, f"{path}: name", f"found {fm.get('name')!r}, expected {expected_name!r}")
    add(results, bool(CANONICAL_ID.match(str(fm.get("name", "")))), f"{path}: canonical name", "lowercase-hyphen id")
    raw_desc = str(fm.get("description_raw", ""))
    add(results, raw_desc.startswith('"') and raw_desc.endswith('"'), f"{path}: description quotes", raw_desc or "missing")
    add(results, fm.get("metadata.disco-role") == "operating", f"{path}: disco role", str(fm.get("metadata.disco-role")))
    add(results, fm.get("disable-model-invocation") is True, f"{path}: disable model invocation", str(fm.get("disable-model-invocation")))


def iter_markdown_files(root: Path) -> Iterable[Path]:
    yield from sorted(root.rglob("*.md"))


def check_links(results: list[Result], skill_root: Path) -> None:
    for md in iter_markdown_files(skill_root):
        text = read_text(md)
        for match in LINK_RE.finditer(text):
            target = match.group(1).split("#", 1)[0].strip()
            if not target or "://" in target or target.startswith("mailto:"):
                continue
            if target.startswith("/"):
                add(results, False, f"{md}: absolute link", target)
                continue
            resolved = (md.parent / target).resolve()
            try:
                resolved.relative_to(skill_root.resolve())
            except ValueError:
                add(results, False, f"{md}: outside link", target)
                continue
            if not resolved.exists():
                add(results, False, f"{md}: missing link", target)


def check_required_files(results: list[Result], skill_root: Path) -> None:
    for rel in sorted(ROOT_REQUIRED):
        add(results, (skill_root / rel).is_file(), f"root file {rel}", "present" if (skill_root / rel).is_file() else "missing")
    for sub, rels in sorted(EXPECTED_SUBSKILLS.items()):
        sub_root = skill_root / "sub-skills" / sub
        check_skill_md(results, sub_root / "SKILL.md", sub)
        for rel in rels:
            add(results, (sub_root / rel).is_file(), f"{sub}/{rel}", "present" if (sub_root / rel).is_file() else "missing")


def check_routing_metadata(results: list[Result], skill_root: Path) -> None:
    path = skill_root / "references" / "repo-routing-metadata.json"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        add(results, False, "repo-routing-metadata.json", f"invalid JSON: {exc}")
        return
    skill = data.get("skills", {}).get("observal")
    scenarios = skill.get("scenarios", []) if isinstance(skill, dict) else []
    add(results, bool(scenarios), "routing metadata scenarios", f"count={len(scenarios)}")
    for index, scenario in enumerate(scenarios):
        for key in ("id", "title", "when_to_read", "role", "read_when", "best_for", "avoid_when", "useful_entry_points", "selection_guidance"):
            add(results, bool(scenario.get(key)), f"scenario[{index}].{key}", "present" if scenario.get(key) else "missing")
        for entry in scenario.get("useful_entry_points", []) or []:
            add(results, (skill_root.parent / entry).is_file(), f"entry point {entry}", "present")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate generated Observal repo-skill tree.")
    parser.add_argument("--skill-root", type=Path, default=Path("."), help="Path to generated observal skill root")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output")
    args = parser.parse_args(argv)

    skill_root = args.skill_root.resolve()
    results: list[Result] = []
    add(results, skill_root.is_dir(), "skill root", "present" if skill_root.is_dir() else "missing")
    if skill_root.is_dir():
        check_skill_md(results, skill_root / "SKILL.md", "observal")
        check_required_files(results, skill_root)
        check_routing_metadata(results, skill_root)
        check_links(results, skill_root)

    failures = [r for r in results if not r.ok]
    payload = {
        "ok": not failures,
        "checked": len(results),
        "failure_count": len(failures),
        "failures": [r.__dict__ for r in failures],
        "results": [r.__dict__ for r in results],
    }
    print(json.dumps(payload, indent=2 if args.pretty else None, sort_keys=True))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
