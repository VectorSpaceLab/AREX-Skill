#!/usr/bin/env python3
"""Print a compact summary of a YiVal Experiment pickle."""

from __future__ import annotations

import argparse
import json
import pickle
from pathlib import Path
from typing import Any


def safe_len(value: Any) -> int:
    try:
        return len(value)
    except Exception:
        return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pickle_path", type=Path)
    args = parser.parse_args()

    with args.pickle_path.open("rb") as f:
        experiment = pickle.load(f)

    combo_metrics = getattr(experiment, "combination_aggregated_metrics", []) or []
    summary = {
        "enable_custom_func": getattr(experiment, "enable_custom_func", None),
        "group_count": safe_len(getattr(experiment, "group_experiment_results", [])),
        "combination_count": safe_len(combo_metrics),
        "selection_output": getattr(getattr(experiment, "selection_output", None), "__dict__", None),
        "combinations": [
            {
                "combo_key": getattr(combo, "combo_key", None),
                "result_count": safe_len(getattr(combo, "experiment_results", [])),
                "average_token_usage": getattr(combo, "average_token_usage", None),
                "average_latency": getattr(combo, "average_latency", None),
                "aggregated_metric_keys": sorted((getattr(combo, "aggregated_metrics", {}) or {}).keys()),
            }
            for combo in combo_metrics
        ],
    }
    print(json.dumps(summary, indent=2, sort_keys=True, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
