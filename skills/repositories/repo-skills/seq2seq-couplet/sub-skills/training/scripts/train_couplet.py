#!/usr/bin/env python3
"""Parameterized training wrapper for seq2seq-couplet.

This replaces the legacy hard-coded training script with explicit paths. It
uses the bundled runtime copy by default; ``--repo-root`` is only for deliberate
comparison against a live checkout.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import List, Optional

SKILL_ROOT = Path(__file__).resolve().parents[3]
ROOT_SCRIPTS = SKILL_ROOT / "scripts"
if str(ROOT_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(ROOT_SCRIPTS))

import couplet_runtime  # noqa: E402


def path_arg(value: str) -> Path:
    return Path(value).expanduser().resolve()


def require_files(paths):
    missing = [str(path) for path in paths if not Path(path).exists()]
    if missing:
        raise SystemExit("Missing required file(s): " + ", ".join(missing))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Train seq2seq-couplet with explicit paths.")
    parser.add_argument("--repo-root", default=None, help="Optional checkout containing model.py and reader.py; omit to use the bundled runtime copy.")
    parser.add_argument("--train-input", type=path_arg, required=True, help="Training input line file.")
    parser.add_argument("--train-target", type=path_arg, required=True, help="Training target line file.")
    parser.add_argument("--test-input", type=path_arg, required=True, help="Evaluation input line file.")
    parser.add_argument("--test-target", type=path_arg, required=True, help="Evaluation target line file.")
    parser.add_argument("--vocab-file", type=path_arg, required=True, help="Vocabulary file with <s> and </s> first.")
    parser.add_argument("--output-dir", type=path_arg, required=True, help="Checkpoint/log output directory.")
    parser.add_argument("--num-units", type=int, default=1024)
    parser.add_argument("--layers", type=int, default=4)
    parser.add_argument("--dropout", type=float, default=0.2)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--learning-rate", type=float, default=0.001)
    parser.add_argument("--epochs", type=int, default=5000000, help="Upper bound passed to Model.train; source loops range(start, epochs).")
    parser.add_argument("--start", type=int, default=1, help="Start step for runs. Default 1 avoids the legacy step-0 eval branch during fresh training.")
    parser.add_argument("--save-step", type=int, default=100)
    parser.add_argument("--eval-step", type=int, default=1000)
    parser.add_argument("--restore-model", action="store_true", help="Restore checkpoint before training.")
    parser.add_argument("--param-histogram", action="store_true", help="Enable TensorBoard parameter histograms.")
    parser.add_argument("--dry-run", action="store_true", help="Validate paths and print config without building the graph.")
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    require_files([args.train_input, args.train_target, args.test_input, args.test_target, args.vocab_file])
    try:
        train_validation = couplet_runtime.validate_parallel_files(
            args.train_input, args.train_target, args.vocab_file, args.batch_size
        )
        test_validation = couplet_runtime.validate_parallel_files(
            args.test_input, args.test_target, args.vocab_file, args.batch_size
        )
    except ValueError as exc:
        raise SystemExit("data validation failed: %s" % exc)
    validation_errors = train_validation["errors"] + test_validation["errors"]
    validation_warnings = train_validation["warnings"] + test_validation["warnings"]
    if validation_errors:
        raise SystemExit("data validation failed: " + "; ".join(validation_errors))
    for warning in validation_warnings:
        print("warning:", warning, file=sys.stderr)
    args.output_dir.mkdir(parents=True, exist_ok=True)

    config = {
        "repo_root": str(Path(args.repo_root).expanduser().resolve()) if args.repo_root else None,
        "train_input": str(args.train_input),
        "train_target": str(args.train_target),
        "test_input": str(args.test_input),
        "test_target": str(args.test_target),
        "vocab_file": str(args.vocab_file),
        "output_dir": str(args.output_dir),
        "num_units": args.num_units,
        "layers": args.layers,
        "dropout": args.dropout,
        "batch_size": args.batch_size,
        "learning_rate": args.learning_rate,
        "epochs": args.epochs,
        "start": args.start,
        "save_step": args.save_step,
        "eval_step": args.eval_step,
        "restore_model": args.restore_model,
        "train_validation": train_validation,
        "test_validation": test_validation,
    }

    if args.dry_run:
        print(json.dumps(config, ensure_ascii=False, indent=2, sort_keys=True))
        return 0

    model = couplet_runtime.build_model(
        args.repo_root,
        train_input_file=args.train_input,
        train_target_file=args.train_target,
        test_input_file=args.test_input,
        test_target_file=args.test_target,
        vocab_file=args.vocab_file,
        num_units=args.num_units,
        layers=args.layers,
        dropout=args.dropout,
        batch_size=args.batch_size,
        learning_rate=args.learning_rate,
        output_dir=args.output_dir,
        save_step=args.save_step,
        eval_step=args.eval_step,
        param_histogram=args.param_histogram,
        restore_model=args.restore_model,
        init_train=True,
        init_infer=False,
    )
    model.train(args.epochs, start=args.start)
    print("Training complete. Checkpoint directory:", args.output_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
