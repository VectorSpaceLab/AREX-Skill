#!/usr/bin/env python3
"""Extract selected Meshroom .mg node attributes into a small JSON file."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


def parseRequests(raw: str) -> list[tuple[str, str]]:
    requests = []
    for item in raw.split(";"):
        item = item.strip()
        if not item:
            continue
        if ":" not in item:
            raise ValueError(f"invalid request {item!r}; expected nodeInstance:paramPath")
        nodeName, paramPath = item.split(":", 1)
        if not nodeName or not paramPath:
            raise ValueError(f"invalid request {item!r}; node and parameter are required")
        requests.append((nodeName, paramPath))
    if not requests:
        raise ValueError("request list is empty")
    return requests


def main() -> int:
    parser = argparse.ArgumentParser(description="Extract Meshroom scene parameters into JSON.")
    parser.add_argument("--scene", required=True, type=Path, help="Source Meshroom .mg scene.")
    parser.add_argument("--request", required=True, help="Semicolon-separated nodeInstance:paramPath entries.")
    parser.add_argument("--output", required=True, type=Path, help="Output JSON path.")
    parser.add_argument("--fail-on-missing-scene", action="store_true")
    parser.add_argument("--fail-on-missing-params", action="store_true")
    parser.add_argument("--repo-root", help="Optional source checkout root to add to sys.path.")
    args = parser.parse_args()

    if args.repo_root:
        sys.path.insert(0, str(Path(args.repo_root).resolve()))

    if not args.scene.exists():
        if args.fail_on_missing_scene:
            print(f"scene does not exist: {args.scene}", file=sys.stderr)
            return 1
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text("[]\n")
        print(f"scene missing; wrote empty result to {args.output}")
        return 0

    try:
        requests = parseRequests(args.request)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    import meshroom
    meshroom.setupEnvironment()
    import meshroom.core
    meshroom.core.initPlugins()
    meshroom.core.initNodes()
    meshroom.core.initPipelines()
    from meshroom.core.graph import loadGraph

    graph = loadGraph(str(args.scene))
    result = []
    missing = []
    for nodeName, paramPath in requests:
        node = graph.node(nodeName)
        if node is None:
            missing.append(f"{nodeName}.{paramPath}")
            continue
        if not node.hasAttribute(paramPath):
            missing.append(f"{nodeName}.{paramPath}")
            continue
        value = node.attribute(paramPath).getValueStr(withQuotes=False)
        result.append({"node": nodeName, "parameter": paramPath, "value": value})

    if missing and args.fail_on_missing_params:
        print("missing parameters: " + ", ".join(missing), file=sys.stderr)
        return 1

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(f"wrote {len(result)} parameter values to {args.output}")
    if missing:
        print("skipped missing parameters: " + ", ".join(missing), file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
