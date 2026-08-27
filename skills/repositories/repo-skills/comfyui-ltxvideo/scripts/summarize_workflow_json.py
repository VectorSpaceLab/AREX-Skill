#!/usr/bin/env python3
"""Summarize ComfyUI workflow JSON files without running them.

The script prints node type counts and basic graph metadata for exported ComfyUI
workflow JSONs. It is useful for mapping user-supplied workflows to the
ComfyUI-LTXVideo node catalog.
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

UUID_RE = re.compile(
    r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Summarize node types in ComfyUI workflow JSON files without running generation."
    )
    parser.add_argument(
        "paths",
        nargs="+",
        type=Path,
        help="Workflow JSON file(s) or directories to scan recursively for .json files.",
    )
    parser.add_argument("--top", type=int, default=30, help="Number of top node types to show per workflow (default: 30).")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON instead of text.")
    return parser


def expand_paths(paths: list[Path]) -> list[Path]:
    out: list[Path] = []
    for path in paths:
        if path.is_dir():
            out.extend(sorted(p for p in path.rglob("*.json") if p.is_file()))
        elif path.is_file():
            out.append(path)
        else:
            raise FileNotFoundError(f"path does not exist: {path}")
    return out


def summarize_file(path: Path, top: int) -> dict[str, Any]:
    result: dict[str, Any] = {
        "path": str(path),
        "ok": False,
        "workflow_id": None,
        "revision": None,
        "node_count": 0,
        "link_count": 0,
        "unique_type_count": 0,
        "uuid_like_type_count": 0,
        "top_types": [],
        "ltxvideo_types": [],
        "errors": [],
    }
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        result["errors"].append(f"failed to parse JSON: {type(exc).__name__}: {exc}")
        return result

    nodes = data.get("nodes")
    if not isinstance(nodes, list):
        result["errors"].append("workflow JSON has no top-level list field 'nodes'")
        return result

    types: list[str] = []
    for node in nodes:
        if not isinstance(node, dict):
            continue
        node_type = node.get("type")
        if isinstance(node_type, str):
            types.append(node_type)

    counts = Counter(types)
    ltx_types = sorted(
        t
        for t in counts
        if t.startswith("LTX") or t.startswith("STG") or t in {"MultimodalGuider", "GuiderParameters", "APGGuider", "DynamicConditioning", "GemmaAPITextEncode"}
    )

    result.update(
        {
            "ok": True,
            "workflow_id": data.get("id"),
            "revision": data.get("revision"),
            "node_count": len(nodes),
            "link_count": len(data.get("links", []) or []),
            "unique_type_count": len(counts),
            "uuid_like_type_count": sum(1 for t in counts if UUID_RE.match(t)),
            "top_types": [{"type": t, "count": c} for t, c in counts.most_common(top)],
            "ltxvideo_types": ltx_types,
        }
    )
    return result


def print_text(report: dict[str, Any]) -> None:
    for item in report["workflows"]:
        print(item["path"])
        if not item["ok"]:
            for error in item["errors"]:
                print(f"  error: {error}")
            continue
        print(
            f"  nodes={item['node_count']} unique_types={item['unique_type_count']} "
            f"links={item['link_count']} uuid_like_types={item['uuid_like_type_count']}"
        )
        if item["ltxvideo_types"]:
            print("  LTXVideo-related types: " + ", ".join(item["ltxvideo_types"]))
        print("  top types:")
        for entry in item["top_types"]:
            print(f"    {entry['count']:>3}  {entry['type']}")
    if report["aggregate_top_types"]:
        print("\nAggregate top types:")
        for entry in report["aggregate_top_types"]:
            print(f"  {entry['count']:>3}  {entry['type']}")


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    paths = expand_paths(args.paths)
    workflows = [summarize_file(path, args.top) for path in paths]
    aggregate = Counter()
    for item in workflows:
        if item["ok"]:
            for entry in item["top_types"]:
                aggregate[entry["type"]] += entry["count"]
    report = {
        "workflow_count": len(workflows),
        "ok_count": sum(1 for item in workflows if item["ok"]),
        "workflows": workflows,
        "aggregate_top_types": [{"type": t, "count": c} for t, c in aggregate.most_common(args.top)],
    }
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_text(report)
    return 0 if all(item["ok"] for item in workflows) else 2


if __name__ == "__main__":
    raise SystemExit(main())
