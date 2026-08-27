#!/usr/bin/env python3
"""Check a VAD nuScenes/CAN-bus layout without downloading or importing VAD.

Examples:
  python check_data_layout.py --data-root data/nuscenes
  python check_data_layout.py --data-root data/nuscenes --canbus-root data --require-train --require-val
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, List


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--data-root", required=True, help="nuScenes data root")
    p.add_argument("--canbus-root", help="parent containing can_bus/")
    p.add_argument("--require-train", action="store_true", help="require the VAD train temporal PKL")
    p.add_argument("--require-val", action="store_true", help="require the VAD val temporal PKL")
    p.add_argument("--require-map-ann", action="store_true", help="require nuscenes_map_anns_val.json")
    p.add_argument("--json", action="store_true", dest="as_json", help="emit JSON")
    return p


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    root = Path(args.data_root).expanduser()
    checks: Dict[str, bool] = {
        "data_root": root.is_dir(),
        "maps": (root / "maps").is_dir(),
        "samples": (root / "samples").is_dir(),
        "sweeps": (root / "sweeps").is_dir(),
    }
    version_dirs = [p.name for p in root.glob("v1.0-*") if p.is_dir()]
    if args.canbus_root:
        checks["can_bus"] = (Path(args.canbus_root).expanduser() / "can_bus").is_dir()
    if args.require_train:
        checks["temporal_train"] = (root / "vad_nuscenes_infos_temporal_train.pkl").is_file()
    if args.require_val:
        checks["temporal_val"] = (root / "vad_nuscenes_infos_temporal_val.pkl").is_file()
    if args.require_map_ann:
        checks["map_annotation"] = (root / "nuscenes_map_anns_val.json").is_file()
    result = {"data_root": str(root), "checks": checks, "version_directories": sorted(version_dirs),
              "ok": all(checks.values())}
    if args.as_json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print("VAD data layout:", "OK" if result["ok"] else "INCOMPLETE")
        print("root:", root)
        print("version directories:", ", ".join(sorted(version_dirs)) or "none")
        for name, ok in checks.items():
            print("  %-18s %s" % (name, "OK" if ok else "MISSING"))
        if not result["ok"]:
            print("Run this check before conversion and fix missing paths; no files were changed.")
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
