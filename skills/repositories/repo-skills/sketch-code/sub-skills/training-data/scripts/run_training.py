#!/usr/bin/env python3
"""Guarded SketchCode training wrapper.

This bundled helper validates the high-risk parts of SketchCode training before
calling the legacy model classes. By default it is a dry-run planner. To start a
real training run, pass both --run and --allow-destructive-split after reading
the training-data troubleshooting reference.
"""

import argparse
import contextlib
import os
import sys
from pathlib import Path
from typing import Iterator, List, Optional, Set, Tuple


@contextlib.contextmanager
def _pushd(path: Path) -> Iterator[None]:
    old = Path.cwd()
    os.chdir(str(path))
    try:
        yield
    finally:
        os.chdir(str(old))


def _resolve_runtime(sketchcode_root: str) -> Tuple[Path, Path]:
    root = Path(sketchcode_root).expanduser().resolve()
    if (root / "src" / "classes").is_dir():
        return root, root / "src"
    if (root / "classes").is_dir():
        return root.parent, root
    raise SystemExit(
        "Could not find SketchCode classes. Point --sketchcode-root at a "
        "checkout root containing src/classes/ or directly at a src directory."
    )


def _paired_counts(data_dir: Path) -> Tuple[Set[str], Set[str]]:
    png = {p.stem for p in data_dir.iterdir() if p.is_file() and p.suffix.lower() == ".png"}
    gui = {p.stem for p in data_dir.iterdir() if p.is_file() and p.suffix.lower() == ".gui"}
    return png, gui


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate and optionally run legacy SketchCode training.")
    parser.add_argument("--sketchcode-root", required=True, help="SketchCode checkout root containing src/classes/ and vocabulary.vocab.")
    parser.add_argument("--data-input-path", required=True, help="Flat directory of paired sample_id.png and sample_id.gui files.")
    parser.add_argument("--validation-split", type=float, default=0.2, help="Fraction of paired samples copied to validation; default matches the legacy CLI.")
    parser.add_argument("--epochs", type=int, required=True, help="Number of epochs for a real run.")
    parser.add_argument("--model-output-path", required=True, help="Directory where model_json.json, weights.h5, logs, and checkpoints are written.")
    parser.add_argument("--model-json-file", help="Optional pretrained Keras model JSON for fine-tuning; requires --model-weights-file.")
    parser.add_argument("--model-weights-file", help="Optional pretrained Keras weights for fine-tuning; requires --model-json-file.")
    parser.add_argument("--augment-training-data", type=int, choices=(0, 1), default=1, help="Use Keras image augmentation for training images; default 1.")
    parser.add_argument("--run", action="store_true", help="Actually start the TensorFlow/Keras training run. Without this flag, only a dry-run plan is printed.")
    parser.add_argument("--allow-destructive-split", action="store_true", help="Acknowledge that sibling training_set and validation_set directories may be deleted/recreated.")
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    root, src_dir = _resolve_runtime(args.sketchcode_root)
    data_dir = Path(args.data_input_path).expanduser().resolve()
    if not data_dir.is_dir():
        raise SystemExit(f"Missing data input directory: {data_dir}")
    if not 0 <= args.validation_split <= 1:
        raise SystemExit("--validation-split must be between 0 and 1.")
    if args.epochs < 1:
        raise SystemExit("--epochs must be at least 1.")
    if bool(args.model_json_file) != bool(args.model_weights_file):
        raise SystemExit("Fine-tuning requires both --model-json-file and --model-weights-file.")
    if args.model_json_file and not Path(args.model_json_file).expanduser().is_file():
        raise SystemExit(f"Missing model JSON: {args.model_json_file}")
    if args.model_weights_file and not Path(args.model_weights_file).expanduser().is_file():
        raise SystemExit(f"Missing model weights: {args.model_weights_file}")

    png, gui = _paired_counts(data_dir)
    paired = png & gui
    missing_gui = sorted(png - gui)
    missing_png = sorted(gui - png)
    parent = data_dir.parent
    training_set = parent / "training_set"
    validation_set = parent / "validation_set"
    model_output = Path(args.model_output_path).expanduser().resolve()

    print(f"SketchCode root: {root}")
    print(f"Source dir for imports/current working dir: {src_dir}")
    print(f"Paired samples: {len(paired)}")
    print(f"Missing .gui for PNG stems: {missing_gui[:10]}{'...' if len(missing_gui) > 10 else ''}")
    print(f"Missing .png for GUI stems: {missing_png[:10]}{'...' if len(missing_png) > 10 else ''}")
    print(f"Validation samples requested: {int(args.validation_split * len(paired))}")
    print(f"Training split directory that may be deleted/recreated: {training_set}")
    print(f"Validation split directory that may be deleted/recreated: {validation_set}")
    print(f"Model output directory: {model_output}")

    if missing_gui or missing_png:
        raise SystemExit("Refusing to train until every sample stem has both .png and .gui files.")
    if not paired:
        raise SystemExit("Refusing to train an empty dataset.")
    if not args.run:
        print("Dry run only. Re-run with --run --allow-destructive-split to start training.")
        return 0
    if not args.allow_destructive_split:
        raise SystemExit("Real training requires --allow-destructive-split because split directories may be deleted/recreated.")

    sys.path.insert(0, str(src_dir))
    try:
        from classes.model.SketchCodeModel import SketchCodeModel  # type: ignore
        from classes.model.ModelUtils import ModelUtils  # type: ignore
    except Exception as exc:  # pragma: no cover - depends on external runtime
        raise SystemExit(
            "Could not import SketchCode training classes. Activate/install the legacy "
            f"TensorFlow/Keras/OpenCV runtime. Original error: {type(exc).__name__}: {exc}"
        )

    model_output.mkdir(parents=True, exist_ok=True)
    with _pushd(src_dir):
        model = SketchCodeModel(str(model_output), args.model_json_file, args.model_weights_file)
        training_path, validation_path = ModelUtils.prepare_data_for_training(
            str(data_dir), args.validation_split, args.augment_training_data
        )
        model.train(training_path=training_path, validation_path=validation_path, epochs=args.epochs)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
