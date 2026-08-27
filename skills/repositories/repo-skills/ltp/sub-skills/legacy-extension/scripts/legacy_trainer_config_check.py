#!/usr/bin/env python3
"""Validate legacy perceptron trainer inputs without running training."""
from __future__ import annotations

import argparse
from pathlib import Path

ALGORITHMS = {"AP", "Pa", "PaI", "PaII"}
TASKS = {"cws", "pos", "ner"}


def main() -> int:
    parser = argparse.ArgumentParser(description="Check LTP legacy trainer task, labels, data paths, and algorithm.")
    parser.add_argument("--task", required=True, choices=sorted(TASKS))
    parser.add_argument("--train-file", required=True)
    parser.add_argument("--eval-file", required=True)
    parser.add_argument("--labels", help="comma-separated labels required for pos/ner")
    parser.add_argument("--algorithm", default="AP", choices=sorted(ALGORITHMS))
    parser.add_argument("--param", type=float, help="optional margin/parameter for PaI/PaII-style algorithms")
    args = parser.parse_args()

    errors = []
    train = Path(args.train_file)
    evalf = Path(args.eval_file)
    if not train.is_file():
        errors.append(f"train file not found: {train}")
    if not evalf.is_file():
        errors.append(f"eval file not found: {evalf}")
    labels = [x.strip() for x in (args.labels or "").split(",") if x.strip()]
    if args.task in {"pos", "ner"} and not labels:
        errors.append(f"--labels is required for {args.task} training")
    if args.algorithm in {"PaI", "PaII"} and args.param is None:
        errors.append(f"--param is recommended for {args.algorithm}")

    if errors:
        print("Legacy trainer configuration is not ready:")
        for err in errors:
            print(f"- {err}")
        return 1

    print("Legacy trainer configuration looks ready for an explicit user-approved training run.")
    print(f"task={args.task} algorithm={args.algorithm} labels={labels or 'not required'}")
    print(f"train_file={train} eval_file={evalf}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
