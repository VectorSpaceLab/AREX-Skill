#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from typing import Any

from boxmot.native.registry import (
    has_native_live_backend,
    has_native_replay_backend,
    supported_native_live_trackers,
    supported_native_replay_trackers,
)
from boxmot.trackers.registry import TRACKER_DEFINITIONS


def _tool_info(name: str) -> dict[str, Any]:
    path = shutil.which(name)
    if path is None:
        return {"available": False, "path": None, "version": None}
    try:
        proc = subprocess.run(
            [name, "--version"],
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
        )
        version = (proc.stdout or proc.stderr or "").strip().splitlines()[0] if (proc.stdout or proc.stderr) else None
    except Exception:
        version = None
    return {"available": True, "path": path, "version": version}


def build_summary(tracker: str, check_tools: bool = False) -> dict[str, Any]:
    tracker_name = tracker.lower().strip()
    definition = TRACKER_DEFINITIONS.get(tracker_name)
    summary: dict[str, Any] = {
        "tracker": tracker_name,
        "has_native_live_backend": has_native_live_backend(tracker_name),
        "has_native_replay_backend": has_native_replay_backend(tracker_name),
        "supported_native_live_trackers": list(supported_native_live_trackers()),
        "supported_native_replay_trackers": list(supported_native_replay_trackers()),
        "tracker_needs_reid": None if definition is None else bool(definition.needs_reid),
        "tracker_class_path": None if definition is None else definition.class_path,
        "tracker_config_path": None if definition is None else str(definition.config_path),
    }
    if check_tools:
        summary["tools"] = {
            "cmake": _tool_info("cmake"),
            "c++": _tool_info("c++"),
            "g++": _tool_info("g++"),
            "pkg-config": _tool_info("pkg-config"),
        }
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Probe BoxMOT native backend availability safely.")
    parser.add_argument("--tracker", required=True, help="Tracker name to inspect")
    parser.add_argument("--check-tools", action="store_true", help="Also check local build-tool availability")
    parser.add_argument("--json", action="store_true", help="Print JSON instead of text")
    args = parser.parse_args()

    summary = build_summary(args.tracker, check_tools=args.check_tools)
    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print(f"tracker: {summary['tracker']}")
        print(f"native live: {summary['has_native_live_backend']}")
        print(f"native replay: {summary['has_native_replay_backend']}")
        print(f"needs reid: {summary['tracker_needs_reid']}")
        print(f"class path: {summary['tracker_class_path']}")
        if args.check_tools:
            print(f"tools: {summary['tools']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
