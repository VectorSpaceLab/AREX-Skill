#!/usr/bin/env python3
"""Summarize a Plexe workdir without opening the Streamlit dashboard."""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path

import yaml

from plexe.utils.dashboard.discovery import discover_experiments, load_experiment_checkpoints


def _load_model_metadata(exp_path: Path) -> dict:
    model_yaml = exp_path / "model" / "model.yaml"
    if not model_yaml.exists():
        return {}
    try:
        with open(model_yaml, encoding="utf-8") as f:
            loaded = yaml.safe_load(f) or {}
        return loaded if isinstance(loaded, dict) else {}
    except Exception:
        return {}


def _summarize_experiment(exp) -> dict:
    checkpoints = load_experiment_checkpoints(exp.path)
    model_metadata = _load_model_metadata(exp.path)
    model_tarball = exp.path / "model.tar.gz"

    return {
        "dataset_name": exp.dataset_name,
        "timestamp": exp.timestamp,
        "experiment_id": exp.experiment_id,
        "status": exp.status,
        "current_phase": exp.current_phase,
        "phase_number": exp.phase_number,
        "best_performance": exp.best_performance,
        "metric_name": exp.metric_name,
        "last_modified": exp.last_modified.isoformat(timespec="seconds"),
        "checkpoint_phases": sorted(checkpoints.keys()),
        "checkpoint_count": len(checkpoints),
        "has_model_package": (exp.path / "model").exists(),
        "has_model_tarball": model_tarball.exists(),
        "model_tarball_mb": round(model_tarball.stat().st_size / (1024**2), 2) if model_tarball.exists() else None,
        "model_type": model_metadata.get("model_type"),
        "task_type": model_metadata.get("task_type"),
    }


def _print_human(rows: list[dict]) -> None:
    if not rows:
        print("No Plexe experiments found.")
        return

    for row in rows:
        perf = f"{row['best_performance']:.4f}" if row["best_performance"] is not None else "N/A"
        print(f"- {row['dataset_name']}/{row['timestamp']} [{row['status']}] phase={row['phase_number']} perf={perf}")
        print(f"  experiment_id: {row['experiment_id']}")
        print(f"  metric: {row['metric_name'] or 'N/A'}")
        print(f"  checkpoints: {', '.join(row['checkpoint_phases']) or 'none'}")
        if row["has_model_package"]:
            print(
                f"  model: {row['model_type'] or 'unknown'} / {row['task_type'] or 'unknown'} / "
                f"{row['model_tarball_mb'] if row['model_tarball_mb'] is not None else 'N/A'} MB"
            )
        else:
            print("  model: not packaged")


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect a Plexe workdir")
    parser.add_argument("work_dir", type=Path, help="Root workdir containing saved Plexe experiments")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON")
    args = parser.parse_args()

    if not args.work_dir.exists():
        raise SystemExit(f"Work dir does not exist: {args.work_dir}")

    experiments = discover_experiments(args.work_dir)
    rows = [_summarize_experiment(exp) for exp in experiments]

    if args.json:
        print(json.dumps(rows, indent=2))
    else:
        _print_human(rows)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
