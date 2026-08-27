#!/usr/bin/env python3
"""Run a credentials-free W&B offline tracking smoke test."""

from __future__ import annotations

import argparse
import json
import math
import pathlib
import random
import tempfile
from typing import Any


def positive_int(value: str) -> int:
    parsed = int(value)
    if parsed < 1:
        raise argparse.ArgumentTypeError("value must be >= 1")
    return parsed


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Create an offline W&B run, log config/metrics/custom axes/table data, "
            "finish cleanly, and print a JSON summary."
        )
    )
    parser.add_argument("--project", default="wandb-offline-smoke", help="W&B project name to store in local run metadata.")
    parser.add_argument("--run-name", default="offline-tracking-smoke", help="Display name for the local smoke run.")
    parser.add_argument("--steps", type=positive_int, default=5, help="Number of synthetic training steps to log.")
    parser.add_argument("--seed", type=int, default=7, help="Random seed for deterministic synthetic metrics.")
    parser.add_argument("--dir", type=pathlib.Path, default=None, help="Writable directory for the local offline run. Defaults to a temporary directory.")
    parser.add_argument("--keep-dir", action="store_true", help="Keep the temporary run directory after the script exits.")
    return parser


def run_smoke(args: argparse.Namespace, root_dir: pathlib.Path) -> dict[str, Any]:
    import wandb

    rng = random.Random(args.seed)
    config = {
        "epochs": args.steps,
        "learning_rate": 0.001,
        "seed": args.seed,
        "tracking_mode": "offline",
    }

    with wandb.init(
        project=args.project,
        name=args.run_name,
        mode="offline",
        dir=str(root_dir),
        config=config,
        settings=wandb.Settings(console="off", init_timeout=60),
    ) as run:
        run.define_metric("train_step")
        run.define_metric("train/*", step_metric="train_step")
        run.define_metric("eval/*", step_metric="train_step", summary="max")

        table_rows = []
        best_accuracy = 0.0
        final_loss = None
        for step in range(args.steps):
            loss = math.exp(-step / max(args.steps, 1)) + rng.random() * 0.01
            accuracy = min(1.0, 0.55 + step / (2 * args.steps) + rng.random() * 0.02)
            final_loss = loss
            best_accuracy = max(best_accuracy, accuracy)
            table_rows.append([step, round(loss, 6), round(accuracy, 6)])
            run.log(
                {
                    "train_step": step,
                    "train/loss": loss,
                    "eval/accuracy": accuracy,
                }
            )

        metrics_table = wandb.Table(
            columns=["train_step", "loss", "accuracy"],
            data=table_rows,
        )
        run.log({"eval/metrics_table": metrics_table})
        run.summary["best_eval_accuracy"] = best_accuracy
        run.summary["final_train_loss"] = final_loss

        return {
            "ok": True,
            "project": args.project,
            "run_id": run.id,
            "run_name": run.name,
            "mode": run.settings.mode,
            "run_dir": run.dir,
            "summary": {
                "best_eval_accuracy": best_accuracy,
                "final_train_loss": final_loss,
                "rows_logged": len(table_rows),
            },
        }


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.dir is not None:
        args.dir.mkdir(parents=True, exist_ok=True)
        result = run_smoke(args, args.dir)
        print(json.dumps(result, indent=2, sort_keys=True))
        return

    if args.keep_dir:
        root_dir = pathlib.Path(tempfile.mkdtemp(prefix="wandb-offline-smoke-"))
        result = run_smoke(args, root_dir)
        result["root_dir"] = str(root_dir)
        print(json.dumps(result, indent=2, sort_keys=True))
        return

    with tempfile.TemporaryDirectory(prefix="wandb-offline-smoke-") as tmp:
        result = run_smoke(args, pathlib.Path(tmp))
        print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
