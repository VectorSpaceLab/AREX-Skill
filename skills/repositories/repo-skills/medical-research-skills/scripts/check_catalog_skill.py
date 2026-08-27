#!/usr/bin/env python3
"""Validate the bundled medical-research-skills operating graph.

The check is offline and read-only. It validates the catalog index, skill
frontmatter contracts, canonical ids, and local Markdown links. It intentionally
does not execute any specialist medical workflow.

Example:
    python scripts/check_catalog_skill.py
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


SKILL_NAME = re.compile(r"^[a-z0-9][a-z0-9-]{0,63}$")
LOCAL_LINK = re.compile(r"\[[^\]]*\]\(([^)]+)\)")


def frontmatter(path: Path) -> dict[str, object]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        raise ValueError("missing YAML frontmatter")
    try:
        block = text.split("---", 2)[1]
    except IndexError as exc:
        raise ValueError("unterminated YAML frontmatter") from exc
    result: dict[str, object] = {}
    metadata: dict[str, str] = {}
    in_metadata = False
    for raw in block.splitlines():
        if raw.strip() == "metadata:":
            in_metadata = True
            continue
        if in_metadata and raw.startswith("  ") and ":" in raw:
            key, value = raw.strip().split(":", 1)
            metadata[key.strip()] = value.strip().strip('"')
            continue
        in_metadata = False
        if ":" in raw:
            key, value = raw.split(":", 1)
            result[key.strip()] = value.strip().strip('"')
    result["metadata"] = metadata
    return result


def validate(root: Path) -> list[str]:
    errors: list[str] = []
    skill_files = [root / "SKILL.md", *sorted((root / "sub-skills").glob("*/SKILL.md"))]
    for path in skill_files:
        if not path.is_file():
            errors.append(f"missing required skill file: {path.relative_to(root)}")
            continue
        try:
            data = frontmatter(path)
        except ValueError as exc:
            errors.append(f"{path.relative_to(root)}: {exc}")
            continue
        expected = root.name if path == root / "SKILL.md" else path.parent.name
        name = str(data.get("name", ""))
        if name != expected:
            errors.append(f"{path.relative_to(root)}: name {name!r} does not match {expected!r}")
        if not SKILL_NAME.fullmatch(name):
            errors.append(f"{path.relative_to(root)}: invalid canonical skill id {name!r}")
        if not data.get("description"):
            errors.append(f"{path.relative_to(root)}: missing description")
        raw_description = next((line.split(":", 1)[1].strip() for line in path.read_text(encoding="utf-8").split("---", 2)[1].splitlines() if line.startswith("description:")), "")
        if not (raw_description.startswith('"') and raw_description.endswith('"')):
            errors.append(f"{path.relative_to(root)}: description must be double-quoted")
        if str(data.get("disable-model-invocation", "")).lower() != "true":
            errors.append(f"{path.relative_to(root)}: disable-model-invocation must be true")
        metadata = data.get("metadata", {})
        if not isinstance(metadata, dict) or metadata.get("disco-role") != "operating":
            errors.append(f"{path.relative_to(root)}: metadata.disco-role must be operating")

    index_path = root / "references" / "catalog-index.json"
    try:
        index = json.loads(index_path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError) as exc:
        errors.append(f"catalog index unavailable or invalid: {exc}")
        index = {}
    metadata_path = root / "references" / "repo-routing-metadata.json"
    try:
        routing = json.loads(metadata_path.read_text(encoding="utf-8"))
        skill_metadata = routing.get("skills", {}).get(root.name, {})
        scenarios = skill_metadata.get("scenarios", [])
        if not scenarios or not all(isinstance(item, dict) for item in scenarios):
            errors.append("repo-routing-metadata.json: missing structured skill scenarios")
        for item in scenarios:
            for field in ("id", "title", "when_to_read", "role", "read_when", "best_for", "avoid_when", "useful_entry_points", "selection_guidance"):
                if not item.get(field):
                    errors.append(f"repo-routing-metadata.json: scenario missing {field}")
    except (FileNotFoundError, json.JSONDecodeError, AttributeError) as exc:
        errors.append(f"repo-routing-metadata.json unavailable or invalid: {exc}")

    records: list[dict[str, object]] = []
    for collection_data in index.get("collections", {}).values() if isinstance(index, dict) else []:
        for category_data in collection_data.get("categories", {}).values():
            records.extend(category_data.get("skills", []))
    stated_total = index.get("counts", {}).get("total") if isinstance(index, dict) else None
    if stated_total != len(records):
        errors.append(f"catalog count mismatch: stated {stated_total!r}, found {len(records)}")
    for record in records:
        skill_id = str(record.get("id", ""))
        # Source entry ids are catalog identifiers, not generated frontmatter
        # ids. A few public source ids exceed the generated skill-id length
        # limit, so validate their safe character shape without applying the
        # runtime frontmatter limit.
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._+-]*", skill_id):
            errors.append(f"catalog contains invalid/empty source id: {skill_id!r}")
        if not record.get("category") or not record.get("collection"):
            errors.append(f"catalog record lacks category or collection: {skill_id!r}")

    for markdown in root.rglob("*.md"):
        text = markdown.read_text(encoding="utf-8")
        for raw_target in LOCAL_LINK.findall(text):
            target = raw_target.split("#", 1)[0].strip()
            if not target or "://" in target or target.startswith("mailto:"):
                continue
            candidate = (markdown.parent / target).resolve()
            try:
                candidate.relative_to(root.resolve())
            except ValueError:
                errors.append(f"{markdown.relative_to(root)}: link escapes skill root: {raw_target}")
                continue
            if not candidate.exists():
                errors.append(f"{markdown.relative_to(root)}: broken local link: {raw_target}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate the bundled operating graph and catalog index.")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1], help=argparse.SUPPRESS)
    args = parser.parse_args()
    errors = validate(args.root.resolve())
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print("PASS: catalog index, frontmatter, identifiers, and local links are consistent")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
