#!/usr/bin/env python3
"""Inspect a trusted VAD result pickle/JSON without importing VAD or rendering."""
from __future__ import annotations
import argparse, json, pickle
from pathlib import Path

EXPECTED = ("sample_token", "translation", "size", "rotation", "velocity", "fut_traj", "detection_name", "detection_score")

def parser():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("artifact", help="trusted .pkl/.pickle/.json result artifact")
    p.add_argument("--sample-token", help="inspect one result sample token")
    p.add_argument("--json", action="store_true", dest="as_json")
    return p

def load(path: Path):
    if path.suffix.lower() == ".json":
        with path.open(encoding="utf-8") as f: return json.load(f)
    with path.open("rb") as f: return pickle.load(f)

def main(argv=None):
    args = parser().parse_args(argv); path = Path(args.artifact)
    if not path.is_file(): print("artifact not found:", path); return 1
    try: obj = load(path)
    except Exception as exc: print("cannot read trusted artifact: %s: %s" % (type(exc).__name__, exc)); return 1
    report = {"artifact": str(path), "type": type(obj).__name__, "top_level_keys": list(obj.keys()) if isinstance(obj, dict) else [], "ok": isinstance(obj, dict)}
    if not isinstance(obj, dict): report["error"] = "expected a top-level mapping"; code = 1
    else:
        samples = obj.get("results", {})
        report["result_sample_count"] = len(samples) if isinstance(samples, dict) else None
        report["has_map_results"] = isinstance(obj.get("map_results"), dict)
        report["has_plan_results"] = isinstance(obj.get("plan_results"), dict)
        if args.sample_token:
            if not isinstance(samples, dict) or args.sample_token not in samples:
                report["error"] = "requested sample token not found"; report["ok"] = False
            else:
                records = samples[args.sample_token]
                if isinstance(records, dict): records = [records]
                report["sample_record_count"] = len(records) if isinstance(records, list) else None
                if isinstance(records, list) and records and isinstance(records[0], dict):
                    report["sample_record_keys"] = sorted(records[0].keys())
                    report["missing_expected_fields"] = [k for k in EXPECTED if k not in records[0]]
        code = 0 if report["ok"] else 1
    print(json.dumps(report, indent=2, default=str) if args.as_json else "\n".join("%s: %s" % (k, v) for k, v in report.items()))
    return code

if __name__ == "__main__": raise SystemExit(main())
