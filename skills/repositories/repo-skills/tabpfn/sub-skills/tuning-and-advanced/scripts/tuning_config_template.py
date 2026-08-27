#!/usr/bin/env python3
"""Print a safe TabPFN tuning / calibration template."""

from __future__ import annotations

import argparse
import json

from tabpfn.inference_tuning import ClassifierTuningConfig, TuningConfig


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task", choices=["classifier", "regressor"], default="classifier")
    parser.add_argument("--json", action="store_true", help="Emit JSON.")
    args = parser.parse_args()

    if args.task == "classifier":
        tuning = ClassifierTuningConfig(
            calibrate_temperature=True,
            tune_decision_thresholds=True,
            tuning_holdout_frac="auto",
            tuning_n_folds="auto",
        )
        payload = {
            "task": args.task,
            "eval_metric": "log_loss",
            "tuning_config": tuning.__dict__,
            "note": "Use this for ordinary classifier calibration; fine-tuning is separate.",
        }
    else:
        tuning = TuningConfig(
            calibrate_temperature=True,
            tuning_holdout_frac="auto",
            tuning_n_folds="auto",
        )
        payload = {
            "task": args.task,
            "eval_metric": "mse",
            "tuning_config": tuning.__dict__,
            "note": "Use this for regression calibration; fine-tuning is separate.",
        }

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
        return

    print(f"task: {payload['task']}")
    print(f"eval_metric: {payload['eval_metric']}")
    print(f"tuning_config: {payload['tuning_config']}")
    print(payload['note'])


if __name__ == "__main__":
    main()
