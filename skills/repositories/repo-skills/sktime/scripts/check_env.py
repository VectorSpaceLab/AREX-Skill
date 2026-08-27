#!/usr/bin/env python3
"""Offline environment smoke check for the sktime repo skill."""
from __future__ import annotations
import argparse, importlib, json, subprocess, sys
from importlib.metadata import PackageNotFoundError, metadata, version
from pathlib import Path
CORE_MODULES = ["sktime","sktime.forecasting","sktime.classification","sktime.regression","sktime.clustering","sktime.transformations","sktime.datatypes","sktime.datasets","sktime.detection","sktime.dists_kernels","sktime.performance_metrics","sktime.split","sktime.benchmarking","sktime.registry"]
SMOKE_SCRIPTS = ["sub-skills/forecasting/scripts/forecasting_smoke.py","sub-skills/panel-learning/scripts/panel_learning_smoke.py","sub-skills/transformations-pipelines/scripts/transform_pipeline_smoke.py","sub-skills/data-interfaces/scripts/check_data_format.py","sub-skills/data-interfaces/scripts/tsfile_roundtrip.py","sub-skills/detection-distances/scripts/detection_distance_smoke.py","sub-skills/evaluation-benchmarking/scripts/evaluation_smoke.py","sub-skills/extension-development/scripts/check_estimator_smoke.py"]
def package_report():
    try:
        md = metadata("sktime"); return {"name": md.get("Name"), "version": version("sktime"), "requires_python": md.get("Requires-Python")}
    except PackageNotFoundError: return {"error": "distribution metadata for sktime was not found"}
    except Exception as exc: return {"error": f"{type(exc).__name__}: {exc}"}
def import_report():
    out = {}
    for name in CORE_MODULES:
        try: mod = importlib.import_module(name); out[name] = {"ok": True, "module": mod.__name__}
        except Exception as exc: out[name] = {"ok": False, "error_type": type(exc).__name__, "error": str(exc)}
    return out
def registry_report():
    try:
        from sktime.registry import all_estimators, all_tags
        counts = {et: len(all_estimators(estimator_types=et, return_names=True)) for et in ["forecaster","classifier","regressor","clusterer","transformer","detector","metric","splitter"]}
        return {"ok": True, "estimator_counts": counts, "tag_count": len(all_tags())}
    except Exception as exc: return {"ok": False, "error_type": type(exc).__name__, "error": str(exc)}
def run_smokes(skill_root: Path, timeout: int):
    results = {}
    for rel in SMOKE_SCRIPTS:
        script = skill_root / rel
        cmd = [sys.executable, str(script), "--json"]
        if rel.endswith("forecasting_smoke.py"): cmd = [sys.executable, str(script), "--json"]
        if rel.endswith("check_data_format.py"): cmd = [sys.executable, str(script), "--example", "tiny-panel"]
        if rel.endswith("tsfile_roundtrip.py"): cmd = [sys.executable, str(script), "--json"]
        if rel.endswith("check_estimator_smoke.py"): cmd = [sys.executable, str(script), "--signature", "--json"]
        try:
            proc = subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout)
            results[rel] = {"ok": proc.returncode == 0, "returncode": proc.returncode, "stdout_tail": proc.stdout[-1000:], "stderr_tail": proc.stderr[-1000:]}
        except Exception as exc: results[rel] = {"ok": False, "error_type": type(exc).__name__, "error": str(exc)}
    return results
def main(argv=None):
    ap = argparse.ArgumentParser(description="Check an installed sktime environment offline.")
    ap.add_argument("--skill-root", type=Path, default=Path(__file__).resolve().parents[1])
    ap.add_argument("--run-subskill-smokes", action="store_true")
    ap.add_argument("--timeout", type=int, default=60)
    ap.add_argument("--pretty", action="store_true")
    args = ap.parse_args(argv)
    report = {"python": sys.version.split()[0], "package": package_report(), "imports": import_report(), "registry": registry_report()}
    if args.run_subskill_smokes: report["subskill_smokes"] = run_smokes(args.skill_root, args.timeout)
    ok = not report["package"].get("error") and all(v.get("ok") for v in report["imports"].values()) and report["registry"].get("ok")
    if "subskill_smokes" in report: ok = ok and all(v.get("ok") for v in report["subskill_smokes"].values())
    report["status"] = "passed" if ok else "failed"
    print(json.dumps(report, indent=2 if args.pretty else None, sort_keys=True)); return 0 if ok else 1
if __name__ == "__main__": raise SystemExit(main())
