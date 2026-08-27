#!/usr/bin/env python3
"""Query the bundled vLLM-Omni model catalog.

This script is intentionally offline-only: it reads the adjacent static JSON
catalog, performs string filtering, and never imports vLLM, HuggingFace, torch,
or model code.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

CATALOG_PATH = Path(__file__).resolve().parents[1] / "references" / "model-catalog.json"


def _norm(value: str) -> str:
    return value.strip().lower().replace("_", "-")


def _load_catalog(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as fh:
        data = json.load(fh)
    if not isinstance(data, dict) or not isinstance(data.get("families"), list):
        raise SystemExit(f"Invalid catalog schema in {path}")
    return data


def _matches_any(needle: str | None, values: list[str]) -> bool:
    if not needle:
        return True
    n = _norm(needle)
    normalized = [_norm(v) for v in values]
    return any(n == v or n in v for v in normalized)


def _family_matches(family: dict[str, Any], task: str | None, backend: str | None, family_filter: str | None) -> bool:
    if backend:
        backends = [str(v) for v in family.get("backends", [])]
        if _norm(backend) not in {_norm(v) for v in backends}:
            return False

    if task:
        task_values: list[str] = []
        for key in ("tasks", "outputs", "inputs", "category"):
            value = family.get(key)
            if isinstance(value, list):
                task_values.extend(str(v) for v in value)
            elif isinstance(value, str):
                task_values.append(value)
        if not _matches_any(task, task_values):
            return False

    if family_filter:
        haystack = [
            str(family.get("id", "")),
            str(family.get("displayName", "")),
            str(family.get("category", "")),
            *(str(v) for v in family.get("representativeModels", [])),
            *(str(v) for v in family.get("architectures", [])),
        ]
        if not _matches_any(family_filter, haystack):
            return False

    return True


def _print_text(matches: list[dict[str, Any]]) -> None:
    if not matches:
        print("No matching model families.")
        return
    for family in matches:
        print(f"{family['id']} — {family.get('displayName', family['id'])}")
        reps = ", ".join(family.get("representativeModels", [])[:5])
        tasks = ", ".join(family.get("tasks", [])[:8])
        backends = ", ".join(family.get("backends", []))
        apis = ", ".join(family.get("apis", [])[:5])
        metrics = ", ".join(family.get("metrics", [])[:6])
        if reps:
            print(f"  models: {reps}")
        if tasks:
            print(f"  tasks: {tasks}")
        if backends:
            print(f"  backends: {backends}")
        if apis:
            print(f"  apis: {apis}")
        if metrics:
            print(f"  metrics: {metrics}")
        if family.get("notes"):
            print(f"  notes: {family['notes']}")
        print()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Filter the bundled vLLM-Omni model-family catalog without network or model loading.",
    )
    parser.add_argument("--task", help="Task/output filter, e.g. text-to-video, tts, action-policy, image.")
    parser.add_argument("--backend", help="Backend filter: cuda, rocm, npu, xpu, or musa.")
    parser.add_argument("--family", help="Family/model/architecture substring filter, e.g. qwen, cosmos, MiniMaxH3Pipeline.")
    parser.add_argument("--format", choices=("text", "json"), default="text", help="Output format.")
    parser.add_argument("--list-tasks", action="store_true", help="Print known task strings and exit.")
    parser.add_argument("--catalog", type=Path, default=CATALOG_PATH, help=argparse.SUPPRESS)
    args = parser.parse_args(argv)

    catalog = _load_catalog(args.catalog)
    families = [dict(f) for f in catalog["families"]]

    if args.list_tasks:
        tasks = sorted({str(t) for f in families for t in f.get("tasks", [])})
        print("\n".join(tasks))
        return 0

    matches = [
        f
        for f in families
        if _family_matches(f, task=args.task, backend=args.backend, family_filter=args.family)
    ]

    if args.format == "json":
        json.dump({"matches": matches, "count": len(matches)}, sys.stdout, indent=2, ensure_ascii=False)
        print()
    else:
        _print_text(matches)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
