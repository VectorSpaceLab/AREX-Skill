#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from typing import Any

import boxmot
from boxmot.configs import list_training_recipes
from boxmot.native.registry import supported_native_live_trackers, supported_native_replay_trackers
from boxmot.reid.backbones import registered_backbone_names
from boxmot.reid.core.config import REID_EXPORT_FORMATS
from boxmot.trackers.registry import TRACKER_MAPPING


def _help_check(*args: str) -> dict[str, Any]:
    cmd = [sys.executable, "-m", "boxmot.engine.cli", *args, "--help"]
    proc = subprocess.run(cmd, check=False, capture_output=True, text=True, timeout=90)
    return {
        "command": " ".join(args) if args else "boxmot",
        "ok": proc.returncode == 0,
        "returncode": proc.returncode,
        "first_line": (proc.stdout or proc.stderr or "").strip().splitlines()[0] if (proc.stdout or proc.stderr) else None,
    }


def build_summary(check_cli_help: bool = True) -> dict[str, Any]:
    summary: dict[str, Any] = {
        "package_name": "boxmot",
        "package_version": boxmot.__version__,
        "python_version": sys.version.split()[0],
        "trackers": sorted(TRACKER_MAPPING),
        "training_recipes": list_training_recipes(),
        "reid_backbones": list(registered_backbone_names()),
        "reid_export_formats": [fmt.name for fmt in REID_EXPORT_FORMATS],
        "native_live_trackers": list(supported_native_live_trackers()),
        "native_replay_trackers": list(supported_native_replay_trackers()),
    }
    if check_cli_help:
        summary["cli_help"] = [
            _help_check(),
            _help_check("track"),
            _help_check("generate"),
            _help_check("eval"),
            _help_check("tune"),
            _help_check("research"),
            _help_check("train"),
            _help_check("eval-reid"),
            _help_check("compare-reid"),
            _help_check("export"),
            _help_check("build"),
        ]
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Check BoxMOT installation and core CLI routes safely.")
    parser.add_argument("--json", action="store_true", help="Print JSON instead of text")
    parser.add_argument("--skip-cli-help", action="store_true", help="Skip the subprocess CLI help checks")
    args = parser.parse_args()

    summary = build_summary(check_cli_help=not args.skip_cli_help)
    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print(f"boxmot: {summary['package_version']} on Python {summary['python_version']}")
        print(f"trackers: {', '.join(summary['trackers'])}")
        print(f"training recipes: {', '.join(summary['training_recipes'])}")
        print(f"reid backbones: {len(summary['reid_backbones'])}")
        print(f"native live trackers: {', '.join(summary['native_live_trackers'])}")
        print(f"native replay trackers: {', '.join(summary['native_replay_trackers'])}")
        if "cli_help" in summary:
            ok_routes = [item["command"] for item in summary["cli_help"] if item["ok"]]
            print(f"cli help ok: {', '.join(ok_routes)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
