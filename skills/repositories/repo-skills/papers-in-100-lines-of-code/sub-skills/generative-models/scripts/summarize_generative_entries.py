#!/usr/bin/env python3
"""Summarize implementation-index entries owned by the generative-models sub-skill.

The default index path follows the repo-skill layout expected when this helper is
run from the sub-skill root: ../../references/implementation-index.json.  The
script is intentionally stdlib-only and does not import ML frameworks.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

TARGET = "generative-models"


def _as_list(value: Any) -> List[Any]:
    if value is None:
        return []
    if isinstance(value, (list, tuple, set)):
        return list(value)
    return [value]


def _lower_strings(value: Any) -> List[str]:
    out: List[str] = []
    for item in _as_list(value):
        if isinstance(item, dict):
            out.extend(_lower_strings(item.get("id")))
            out.extend(_lower_strings(item.get("name")))
            out.extend(_lower_strings(item.get("owner")))
            out.extend(_lower_strings(item.get("group")))
        else:
            text = str(item).strip().lower()
            if text:
                out.append(text)
    return out


def _field(entry: Dict[str, Any], *names: str) -> Any:
    for name in names:
        if name in entry and entry[name] not in (None, "", []):
            return entry[name]
    metadata = entry.get("metadata")
    if isinstance(metadata, dict):
        for name in names:
            if name in metadata and metadata[name] not in (None, "", []):
                return metadata[name]
    return None


def default_index_path() -> Path:
    """Return the expected implementation-index path without requiring it to exist."""
    cwd_candidate = (Path.cwd() / "../../references/implementation-index.json").resolve()
    script_path = Path(__file__).resolve()
    script_candidate = None
    # scripts/summarize_generative_entries.py -> sub-skill -> sub-skills -> root skill
    if len(script_path.parents) >= 4:
        script_candidate = script_path.parents[3] / "references" / "implementation-index.json"
    if cwd_candidate.exists():
        return cwd_candidate
    if script_candidate is not None and script_candidate.exists():
        return script_candidate
    return cwd_candidate


def load_json(path: Path) -> Any:
    try:
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except FileNotFoundError:
        raise SystemExit(f"index not found: {path}")
    except json.JSONDecodeError as exc:
        raise SystemExit(f"invalid JSON in {path}: {exc}")


def iter_entries(data: Any) -> Iterable[Tuple[str, Dict[str, Any]]]:
    """Yield (key, entry) pairs from common implementation-index shapes."""
    if isinstance(data, list):
        for idx, item in enumerate(data):
            if isinstance(item, dict):
                yield str(idx), dict(item)
        return

    if not isinstance(data, dict):
        return

    for container_name in ("entries", "implementations", "items", "records", "papers"):
        container = data.get(container_name)
        if isinstance(container, list):
            for idx, item in enumerate(container):
                if isinstance(item, dict):
                    yield str(idx), dict(item)
            return
        if isinstance(container, dict):
            for key, item in container.items():
                if isinstance(item, dict):
                    entry = dict(item)
                    entry.setdefault("id", key)
                    yield str(key), entry
            return

    # Fallback: a mapping from implementation id/directory to entry object.
    for key, item in data.items():
        if isinstance(item, dict):
            entry = dict(item)
            entry.setdefault("id", key)
            yield str(key), entry


def owned_by_target(entry: Dict[str, Any], target: str) -> bool:
    target_l = target.lower()
    owner_values = _lower_strings(
        _field(entry, "owner", "owners", "subskill", "sub_skill", "subSkill", "skill", "skills")
    )
    group_values = _lower_strings(
        _field(entry, "group", "groups", "workflow_group", "workflowGroup", "routing_group")
    )
    return target_l in owner_values or target_l in group_values


def summarize_entry(key: str, entry: Dict[str, Any]) -> str:
    title = _field(entry, "title", "paper", "name", "directory", "id") or key
    directory = _field(entry, "directory", "dir", "path", "slug")
    owner = _field(entry, "owner", "owners", "subskill", "sub_skill", "subSkill")
    group = _field(entry, "group", "groups", "workflow", "category", "categories")
    scripts = _field(entry, "scripts", "source_scripts", "sourceScripts", "py_files", "files")
    symbols = _field(entry, "key_symbols", "keySymbols", "symbols", "functions", "classes")
    requirements = _field(entry, "requirements", "dependencies", "deps")
    safety = _field(entry, "safety", "safety_check", "check", "runtime_flags", "runtimeFlags")

    parts = [f"- {title}"]
    if directory and str(directory) != str(title):
        parts.append(f"  directory: {directory}")
    if owner:
        parts.append(f"  owner: {', '.join(map(str, _as_list(owner)))}")
    if group:
        parts.append(f"  group: {', '.join(map(str, _as_list(group)))}")
    if scripts:
        parts.append(f"  scripts: {', '.join(map(str, _as_list(scripts)))}")
    if symbols:
        parts.append(f"  key symbols: {', '.join(map(str, _as_list(symbols)))}")
    if requirements:
        parts.append(f"  requirements: {', '.join(map(str, _as_list(requirements)))}")
    if safety:
        parts.append(f"  safety: {', '.join(map(str, _as_list(safety)))}")
    return "\n".join(parts)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Summarize entries in ../../references/implementation-index.json "
            "whose owner or group is generative-models."
        )
    )
    parser.add_argument(
        "--index",
        type=Path,
        default=default_index_path(),
        help="Path to implementation-index.json (default: ../../references/implementation-index.json).",
    )
    parser.add_argument(
        "--target",
        default=TARGET,
        help="Owner/group id to select (default: generative-models).",
    )
    parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="Output format (default: text).",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Maximum number of selected entries to print; 0 means no limit.",
    )
    return parser


def main(argv: List[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    data = load_json(args.index)
    selected: List[Tuple[str, Dict[str, Any]]] = [
        (key, entry) for key, entry in iter_entries(data) if owned_by_target(entry, args.target)
    ]
    if args.limit and args.limit > 0:
        selected = selected[: args.limit]

    if args.format == "json":
        payload = [{"key": key, **entry} for key, entry in selected]
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0

    print(f"implementation index: {args.index}")
    print(f"target owner/group: {args.target}")
    print(f"selected entries: {len(selected)}")
    if not selected:
        print("No matching entries found. Check whether the index uses owner/group fields or pass --target.")
        return 0
    for key, entry in selected:
        print(summarize_entry(key, entry))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
