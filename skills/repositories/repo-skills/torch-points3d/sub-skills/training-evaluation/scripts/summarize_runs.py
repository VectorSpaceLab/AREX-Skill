#!/usr/bin/env python3
"""Read-only Torch Points3D experiment run summarizer.

This adapts the repository's `find_runs.py` helper but removes its deletion
option. It scans an outputs tree for `.pt` checkpoints and summarizes model
names plus available metric histories when checkpoints can be loaded.

Example:
  python sub-skills/training-evaluation/scripts/summarize_runs.py --outputs-dir outputs --json
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List


def jsonable(value: Any) -> Any:
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if isinstance(value, dict):
        return {str(k): jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [jsonable(v) for v in value]
    try:
        return float(value)
    except Exception:
        return str(value)


def summarize_checkpoint(path: Path) -> Dict[str, Any]:
    try:
        import torch
    except Exception as exc:  # noqa: BLE001
        return {"path": path.name, "loadable": False, "error": f"torch import failed: {type(exc).__name__}: {exc}"}

    try:
        obj = torch.load(path, map_location="cpu")
    except Exception as exc:  # noqa: BLE001
        return {"path": path.name, "loadable": False, "error": f"torch.load failed: {type(exc).__name__}: {exc}"}

    stats = obj.get("stats", {}) if isinstance(obj, dict) else {}
    models = obj.get("models", {}) if isinstance(obj, dict) else {}
    latest = {}
    for split_name, history in stats.items():
        if history:
            latest[split_name] = jsonable(history[-1])
    return {
        "path": path.name,
        "loadable": True,
        "model_keys": sorted(map(str, models.keys())) if isinstance(models, dict) else [],
        "stats_splits": sorted(map(str, stats.keys())) if isinstance(stats, dict) else [],
        "num_epochs": len(stats.get("train", [])) if isinstance(stats, dict) else None,
        "latest_metrics": latest,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Summarize Torch Points3D output runs without modifying them.")
    parser.add_argument("--outputs-dir", type=Path, default=Path("outputs"), help="Torch Points3D outputs directory or a single run directory.")
    parser.add_argument("--json", action="store_true", help="Emit JSON summary.")
    parser.add_argument("--max-runs", type=int, default=200, help="Maximum run directories to inspect.")
    args = parser.parse_args()

    if not args.outputs_dir.exists():
        raise SystemExit(f"outputs-dir does not exist: {args.outputs_dir}")
    if args.max_runs <= 0:
        raise SystemExit("--max-runs must be positive")

    if list(args.outputs_dir.glob("*.pt")):
        run_dirs = [args.outputs_dir]
    else:
        run_dirs = sorted({p.parent for p in args.outputs_dir.glob("*/*/*.pt")})
        if not run_dirs:
            run_dirs = [p for p in sorted(args.outputs_dir.glob("*/*")) if p.is_dir()]

    run_dirs = run_dirs[: args.max_runs]
    reports: List[Dict[str, Any]] = []
    for run_dir in run_dirs:
        checkpoints = sorted(run_dir.glob("*.pt"))
        reports.append(
            {
                "run": str(run_dir.relative_to(args.outputs_dir)) if run_dir != args.outputs_dir else ".",
                "checkpoint_count": len(checkpoints),
                "checkpoints": [summarize_checkpoint(path) for path in checkpoints],
            }
        )

    result = {"outputs_dir": str(args.outputs_dir), "run_count": len(reports), "runs": reports}

    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(f"Torch Points3D runs under {args.outputs_dir}: {len(reports)}")
        for report in reports:
            print(f"run {report['run']}: {report['checkpoint_count']} checkpoint(s)")
            for ckpt in report["checkpoints"]:
                status = "loadable" if ckpt.get("loadable") else ckpt.get("error", "not loadable")
                print(f"  {ckpt['path']}: {status}")
                if ckpt.get("loadable"):
                    print(f"    model keys: {ckpt.get('model_keys')}")
                    print(f"    epochs: {ckpt.get('num_epochs')}")
                    print(f"    latest metrics: {ckpt.get('latest_metrics')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
