#!/usr/bin/env python3
"""List Potpie's packaged agent-bundle skills without contacting the daemon."""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from importlib import resources
from typing import Iterable


PACKAGE = "potpie.cli"
BUNDLE_PARTS = ("templates", "agent_bundle", ".agents", "skills")
FALSE_VALUES = {"false", "no", "0", "off"}


@dataclass(frozen=True)
class SkillRow:
    skill_id: str
    title: str
    version: str
    recommended: bool
    description: str


def _strip_yaml_scalar(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        return value[1:-1]
    return value


def _front_matter(raw: str) -> tuple[dict[str, str], str]:
    if not raw.startswith("---\n"):
        return {}, raw
    end = raw.find("\n---\n", 4)
    if end < 0:
        return {}, raw
    meta: dict[str, str] = {}
    for line in raw[4:end].splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or ":" not in stripped:
            continue
        key, _, value = stripped.partition(":")
        meta[key.strip()] = _strip_yaml_scalar(value)
    return meta, raw[end + 5 :]


def _title_from_body(body: str, *, fallback: str) -> str:
    for line in body.splitlines():
        stripped = line.strip()
        if stripped.startswith("# "):
            return stripped[2:].strip()
    return fallback


def _recommended(value: str | None) -> bool:
    if value is None:
        return True
    return value.strip().lower() not in FALSE_VALUES


def load_rows() -> list[SkillRow]:
    root = resources.files(PACKAGE)
    for part in BUNDLE_PARTS:
        root = root.joinpath(part)
    rows: list[SkillRow] = []
    for child in sorted(root.iterdir(), key=lambda item: item.name):
        if not child.is_dir():
            continue
        skill_md = child.joinpath("SKILL.md")
        if not skill_md.is_file():
            continue
        raw = skill_md.read_text(encoding="utf-8")
        meta, body = _front_matter(raw)
        rows.append(
            SkillRow(
                skill_id=child.name,
                title=meta.get("title") or _title_from_body(body, fallback=child.name),
                version=meta.get("version", "1"),
                recommended=_recommended(meta.get("recommended")),
                description=meta.get("description", ""),
            )
        )
    return rows


def print_text(rows: Iterable[SkillRow]) -> None:
    for row in rows:
        rec = "recommended" if row.recommended else "optional"
        print(f"{row.skill_id}\tversion={row.version}\t{rec}\t{row.title}")
        if row.description:
            print(f"  {row.description}")


def print_markdown(rows: Iterable[SkillRow]) -> None:
    print("| Skill id | Version | Recommended | Title | Description |")
    print("| --- | --- | --- | --- | --- |")
    for row in rows:
        desc = row.description.replace("|", "\\|")
        title = row.title.replace("|", "\\|")
        print(
            f"| `{row.skill_id}` | `{row.version}` | "
            f"{'yes' if row.recommended else 'no'} | {title} | {desc} |"
        )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--markdown", action="store_true", help="print a Markdown table")
    args = parser.parse_args(argv)
    rows = load_rows()
    if args.markdown:
        print_markdown(rows)
    else:
        print_text(rows)
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
