#!/usr/bin/env python3
"""Safe wrapper for SketchCode PNG-to-GUI/HTML conversion.

The historical repository exposes conversion as source-tree scripts. This
bundled wrapper keeps argument validation and troubleshooting in the generated
skill while importing SketchCode runtime classes from either the current Python
path or a user-supplied SketchCode checkout/runtime root.

Examples:
  python run_conversion.py single --sketchcode-root /path/to/sketch-code \
    --png-path sketch.png --output-folder out \
    --model-json-file model_json.json --model-weights-file weights.h5

  python run_conversion.py batch --sketchcode-root /path/to/sketch-code \
    --pngs-path sketches --output-folder out \
    --model-json-file model_json.json --model-weights-file weights.h5
"""

import argparse
import os
import sys
from pathlib import Path
from typing import List, Optional

SUPPORTED_STYLES = ("default", "facebook", "airbnb")


def _add_runtime_path(sketchcode_root: Optional[str]) -> Optional[Path]:
    if not sketchcode_root:
        return None
    root = Path(sketchcode_root).expanduser().resolve()
    candidates = []
    if (root / "src" / "classes").is_dir():
        candidates.append(root / "src")
    if (root / "classes").is_dir():
        candidates.append(root)
    for candidate in candidates:
        sys.path.insert(0, str(candidate))
        return candidate
    raise SystemExit(
        "Could not find SketchCode classes. Point --sketchcode-root at a "
        "checkout root containing src/classes/ or directly at a src directory "
        "containing classes/."
    )


def _require_file(path: str, label: str) -> Path:
    p = Path(path).expanduser()
    if not p.is_file():
        raise SystemExit(f"Missing {label}: {p}")
    return p


def _require_dir(path: str, label: str, create: bool = False) -> Path:
    p = Path(path).expanduser()
    if create:
        p.mkdir(parents=True, exist_ok=True)
    if not p.is_dir():
        raise SystemExit(f"Missing {label}: {p}")
    return p


def _load_sampler(sketchcode_root: Optional[str]):
    runtime_path = _add_runtime_path(sketchcode_root)
    try:
        from classes.inference.Sampler import Sampler  # type: ignore
    except Exception as exc:  # pragma: no cover - depends on external runtime
        where = f" using runtime path {runtime_path}" if runtime_path else " from current Python path"
        raise SystemExit(
            "Could not import classes.inference.Sampler" + where + ". "
            "Install/activate SketchCode's legacy TensorFlow/Keras/OpenCV "
            "environment, or pass --sketchcode-root to the checkout you are operating on. "
            f"Original error: {type(exc).__name__}: {exc}"
        )
    return Sampler


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run SketchCode conversion with bundled validation.")
    parser.add_argument(
        "--sketchcode-root",
        help="SketchCode checkout root containing src/classes/ or a src directory containing classes/. If omitted, imports from the current Python path.",
    )
    subparsers = parser.add_subparsers(dest="mode")
    subparsers.required = True

    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--output-folder", required=True, help="Directory for generated .gui and .html files; created when missing.")
    common.add_argument("--model-json-file", required=True, help="Keras model architecture JSON file.")
    common.add_argument("--model-weights-file", required=True, help="Keras HDF5 weights file matching the JSON architecture.")
    common.add_argument("--style", choices=SUPPORTED_STYLES, default="default", help="HTML style mapping to use.")

    single = subparsers.add_parser("single", parents=[common], help="Convert one PNG image.")
    single.add_argument("--png-path", required=True, help="PNG file to convert.")
    single.add_argument("--print-generated-output", type=int, choices=(0, 1), default=1)
    single.add_argument("--print-bleu-score", type=int, choices=(0, 1), default=0)
    single.add_argument("--original-gui-filepath", help="Original .gui file for optional sentence BLEU.")

    batch = subparsers.add_parser("batch", parents=[common], help="Convert all PNG files in a directory.")
    batch.add_argument("--pngs-path", required=True, help="Directory containing PNG files.")
    batch.add_argument("--print-bleu-score", type=int, choices=(0, 1), default=0)
    batch.add_argument("--original-guis-filepath", help="Directory of original .gui files for optional corpus BLEU.")
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    _require_file(args.model_json_file, "model JSON")
    _require_file(args.model_weights_file, "model weights")
    output_folder = _require_dir(args.output_folder, "output folder", create=True)

    Sampler = _load_sampler(args.sketchcode_root)
    sampler = Sampler(model_json_path=args.model_json_file, model_weights_path=args.model_weights_file)

    if args.mode == "single":
        png_path = _require_file(args.png_path, "PNG input")
        if png_path.suffix.lower() != ".png":
            raise SystemExit(f"SketchCode conversion expects a .png filename, got: {png_path}")
        if args.print_bleu_score and not args.original_gui_filepath:
            raise SystemExit("--print-bleu-score 1 requires --original-gui-filepath for single mode.")
        if args.original_gui_filepath:
            _require_file(args.original_gui_filepath, "original GUI")
        sampler.convert_single_image(
            str(output_folder),
            png_path=str(png_path),
            print_generated_output=args.print_generated_output,
            get_sentence_bleu=args.print_bleu_score,
            original_gui_filepath=args.original_gui_filepath,
            style=args.style,
        )
        return 0

    pngs_path = _require_dir(args.pngs_path, "PNG folder")
    if args.print_bleu_score and not args.original_guis_filepath:
        raise SystemExit("--print-bleu-score 1 requires --original-guis-filepath for batch mode.")
    if args.original_guis_filepath:
        _require_dir(args.original_guis_filepath, "original GUIs folder")
    sampler.convert_batch_of_images(
        str(output_folder),
        pngs_path=str(pngs_path),
        get_corpus_bleu=args.print_bleu_score,
        original_guis_filepath=args.original_guis_filepath,
        style=args.style,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
