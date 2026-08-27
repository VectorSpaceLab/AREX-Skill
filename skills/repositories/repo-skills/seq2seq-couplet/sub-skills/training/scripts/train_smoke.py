#!/usr/bin/env python3
"""Run a tiny end-to-end training smoke for seq2seq-couplet.

The script creates a synthetic aligned dataset, trains a very small model for
one epoch, and checks that checkpoint files are produced. It is intended for
runtime verification, not quality evaluation.
"""

from __future__ import annotations

import argparse
import sys
import tempfile
from pathlib import Path
from typing import List, Optional

SKILL_ROOT = Path(__file__).resolve().parents[3]
ROOT_SCRIPTS = SKILL_ROOT / "scripts"
if str(ROOT_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(ROOT_SCRIPTS))

import couplet_runtime  # noqa: E402


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run a tiny seq2seq-couplet training smoke.")
    parser.add_argument("--repo-root", default=None, help="Optional checkout containing model.py and reader.py; omit to use the bundled runtime copy.")
    parser.add_argument("--workdir", help="Directory to hold the tiny fixture and output checkpoint. Defaults to a new temp dir.")
    parser.add_argument("--num-units", type=int, default=16)
    parser.add_argument("--layers", type=int, default=2)
    parser.add_argument("--dropout", type=float, default=0.0)
    parser.add_argument("--batch-size", type=int, default=1)
    parser.add_argument("--learning-rate", type=float, default=0.01)
    parser.add_argument("--epochs", type=int, default=1)
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    if args.workdir:
        workdir = Path(args.workdir).expanduser().resolve()
        workdir.mkdir(parents=True, exist_ok=True)
    else:
        workdir = Path(tempfile.mkdtemp(prefix="seq2seq-couplet-train-smoke-"))

    result = couplet_runtime.train_tiny_checkpoint(
        args.repo_root,
        workdir,
        num_units=args.num_units,
        layers=args.layers,
        dropout=args.dropout,
        batch_size=args.batch_size,
        learning_rate=args.learning_rate,
        epochs=args.epochs,
    )
    checkpoint_files = sorted(Path(result["output_dir"]).glob("model.ckpl*"))
    if not checkpoint_files:
        raise SystemExit("Training smoke did not produce model.ckpl checkpoint files")

    print("Tiny training smoke passed.")
    print(couplet_runtime.summarize_fixture(result))
    print("Checkpoint files:")
    for path in checkpoint_files:
        print(" -", path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
