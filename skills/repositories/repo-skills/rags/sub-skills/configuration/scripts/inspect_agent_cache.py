#!/usr/bin/env python3
"""Inspect a RAGs agent cache directory without modifying it.

The default cache root is cache/agents relative to the current working
directory. Pass --cache-dir to inspect a specific checkout or copied cache.
The helper validates registry shape, listed agent IDs, per-agent cache.json,
and storage directories. It never deletes or rewrites cache files.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Read-only RAGs agent cache inspector.")
    parser.add_argument(
        "--cache-dir",
        default="cache/agents",
        help="Path to the RAGs cache/agents directory. Default: cache/agents",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit non-zero when listed agents are missing cache.json or storage/.",
    )
    parser.add_argument(
        "--json-indent",
        type=int,
        default=2,
        help="Indentation for JSON output. Use 0 for compact output.",
    )
    return parser


def _load_registry(path: Path) -> tuple[list[str], str | None]:
    registry_file = path / "agent_ids.json"
    if not registry_file.exists():
        return [], "agent_ids.json is absent; registry is empty"
    try:
        payload = json.loads(registry_file.read_text())
    except Exception as exc:  # noqa: BLE001 - report parse failure to user
        return [], f"agent_ids.json is not valid JSON: {exc}"
    ids = payload.get("agent_ids")
    if not isinstance(ids, list) or not all(isinstance(item, str) for item in ids):
        return [], "agent_ids.json must contain a list field named agent_ids"
    return ids, None


def inspect_cache(cache_dir: Path) -> dict[str, Any]:
    result: dict[str, Any] = {
        "cache_dir": str(cache_dir),
        "exists": cache_dir.exists(),
        "is_dir": cache_dir.is_dir(),
    }
    if not cache_dir.exists() or not cache_dir.is_dir():
        result.update(
            {
                "agent_ids": [],
                "agents": [],
                "warnings": ["cache directory is missing or not a directory"],
            }
        )
        return result

    agent_ids, registry_warning = _load_registry(cache_dir)
    id_set = set(agent_ids)
    dirs = sorted(p.name for p in cache_dir.iterdir() if p.is_dir())
    agents = []
    for agent_id in agent_ids:
        agent_dir = cache_dir / agent_id
        cache_json = agent_dir / "cache.json"
        storage_dir = agent_dir / "storage"
        cache_payload: dict[str, Any] | None = None
        cache_error: str | None = None
        if cache_json.exists():
            try:
                cache_payload = json.loads(cache_json.read_text())
            except Exception as exc:  # noqa: BLE001
                cache_error = str(exc)
        agents.append(
            {
                "agent_id": agent_id,
                "directory_exists": agent_dir.is_dir(),
                "cache_json_exists": cache_json.is_file(),
                "cache_json_valid": cache_payload is not None,
                "cache_json_error": cache_error,
                "storage_exists": storage_dir.is_dir(),
                "stored_builder_type": None if cache_payload is None else cache_payload.get("builder_type"),
                "stored_tools": None if cache_payload is None else cache_payload.get("tools"),
                "stored_rag_params": None if cache_payload is None else cache_payload.get("rag_params"),
            }
        )

    warnings = []
    if registry_warning:
        warnings.append(registry_warning)
    missing_dirs = [agent_id for agent_id in agent_ids if not (cache_dir / agent_id).is_dir()]
    extra_dirs = [name for name in dirs if name not in id_set]
    if missing_dirs:
        warnings.append("listed agent ID(s) without directories: " + ", ".join(missing_dirs))
    if extra_dirs:
        warnings.append("agent directories not listed in registry: " + ", ".join(extra_dirs))

    result.update(
        {
            "agent_ids": agent_ids,
            "agent_directories": dirs,
            "agents": agents,
            "missing_listed_directories": missing_dirs,
            "unlisted_directories": extra_dirs,
            "warnings": warnings,
        }
    )
    return result


def main() -> int:
    args = build_parser().parse_args()
    report = inspect_cache(Path(args.cache_dir).expanduser())
    indent = None if args.json_indent == 0 else args.json_indent
    print(json.dumps(report, indent=indent, sort_keys=True))

    if args.strict:
        for agent in report.get("agents", []):
            if not (
                agent.get("directory_exists")
                and agent.get("cache_json_exists")
                and agent.get("cache_json_valid")
                and agent.get("storage_exists")
            ):
                return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
