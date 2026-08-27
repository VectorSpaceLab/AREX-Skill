#!/usr/bin/env python3
"""Safe optional model import checks for segment-geospatial.

By default this imports optional wrappers that should not download model weights.
Captioning and FER are opt-in because caption import fetches a remote vocabulary
and FER may print GDAL/osgeo warnings. detectree2 runtime is not instantiated.
"""

from __future__ import annotations

import argparse
import importlib
import json


def try_import(name: str) -> dict:
    try:
        module = importlib.import_module(name)
    except Exception as exc:  # noqa: BLE001
        return {"name": name, "ok": False, "error": f"{type(exc).__name__}: {exc}"}
    return {"name": name, "ok": True, "module": getattr(module, "__name__", name)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--include-caption-network", action="store_true", help="Also import samgeo.caption; this may fetch a remote vocabulary.")
    parser.add_argument("--include-detectree2", action="store_true", help="Import samgeo.detectree2 but do not instantiate TreeCrownDelineator.")
    parser.add_argument("--include-fer", action="store_true", help="Import samgeo.fer; may print an osgeo/GDAL warning if GDAL is missing.")
    parser.add_argument("--strict", action="store_true", help="Return non-zero if any checked import fails.")
    parser.add_argument("--json", action="store_true", help="Emit JSON.")
    args = parser.parse_args()

    modules = ["samgeo.fast_sam", "samgeo.hq_sam", "samgeo.text_sam"]
    if args.include_caption_network:
        modules.append("samgeo.caption")
    if args.include_detectree2:
        modules.append("samgeo.detectree2")
    if args.include_fer:
        modules.append("samgeo.fer")

    results = [try_import(name) for name in modules]
    report = {
        "checked": results,
        "notes": [
            "This script does not construct optional models or download weights.",
            "detectree2 requires external detectree2/Detectron2 before TreeCrownDelineator can run.",
            "caption import is opt-in because it can perform a network vocabulary fetch.",
        ],
    }

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        for item in results:
            status = "OK" if item["ok"] else f"FAIL ({item['error']})"
            print(f"{item['name']}: {status}")
        for note in report["notes"]:
            print(f"Note: {note}")

    return 0 if (not args.strict or all(item["ok"] for item in results)) else 1


if __name__ == "__main__":
    raise SystemExit(main())
