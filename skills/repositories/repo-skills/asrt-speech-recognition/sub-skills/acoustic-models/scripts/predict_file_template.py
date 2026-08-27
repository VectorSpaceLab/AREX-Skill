#!/usr/bin/env python3
"""Parameterized ASRT single-file acoustic prediction template."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any


MODEL_CLASS_NAMES = {
    "24": "SpeechModel24",
    "25": "SpeechModel25",
    "251": "SpeechModel251",
    "251bn": "SpeechModel251BN",
}


def _parse_shape(value: str) -> tuple[int, int, int]:
    parts = [part.strip() for part in value.split(",")]
    if len(parts) != 3:
        raise argparse.ArgumentTypeError("shape must have three comma-separated integers, e.g. 1600,200,1")
    try:
        shape = tuple(int(part) for part in parts)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("shape values must be integers") from exc
    if any(dim <= 0 for dim in shape):
        raise argparse.ArgumentTypeError("shape dimensions must be positive")
    return shape  # type: ignore[return-value]


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Load an ASRT Keras acoustic model and decode one WAV file to pinyin tokens. "
            "This template stops before the pinyin-to-Chinese language model."
        )
    )
    parser.add_argument("--asrt-root", help="Optional ASRT project root to prepend to PYTHONPATH for imports.")
    parser.add_argument("--wav", required=True, help="Path to one WAV file to decode.")
    weights = parser.add_mutually_exclusive_group(required=True)
    weights.add_argument("--weights", help="Training-model weights file, normally ending in .model.h5.")
    weights.add_argument("--base-weights", help="Base/inference weights file, normally ending in .model.base.h5.")
    parser.add_argument("--model", choices=sorted(MODEL_CLASS_NAMES), default="251bn", help="Acoustic model variant. Default: 251bn.")
    parser.add_argument("--input-shape", type=_parse_shape, default=(1600, 200, 1), help="Input shape as time,bins,channels. Default: 1600,200,1.")
    parser.add_argument("--output-size", type=int, default=1428, help="Output class count. Default: 1428.")
    parser.add_argument("--max-label-length", type=int, default=64, help="Maximum CTC label length used by ModelSpeech. Default: 64.")
    parser.add_argument("--cuda-visible-devices", help="Set CUDA_VISIBLE_DEVICES before importing TensorFlow, e.g. -1 for CPU or 0 for the first GPU.")
    parser.add_argument("--dry-run", action="store_true", help="Validate arguments and imports, construct the model, but do not load weights or read/decode the WAV.")
    parser.add_argument("--json", action="store_true", help="Print decoded pinyin tokens as JSON.")
    return parser


def _require_file(path_value: str, label: str) -> Path:
    path = Path(path_value).expanduser()
    if not path.is_file():
        raise FileNotFoundError(f"{label} does not exist or is not a file: {path}")
    return path


def main(argv: list[str] | None = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    if args.output_size <= 0:
        parser.error("--output-size must be positive")
    if args.max_label_length <= 0:
        parser.error("--max-label-length must be positive")

    try:
        wav_path = _require_file(args.wav, "WAV path")
        weights_path = _require_file(args.weights or args.base_weights, "weights path")
    except FileNotFoundError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")
    if args.cuda_visible_devices is not None:
        os.environ["CUDA_VISIBLE_DEVICES"] = args.cuda_visible_devices

    if args.asrt_root:
        sys.path.insert(0, os.path.abspath(args.asrt_root))

    try:
        from model_zoo.speech_model import keras_backend  # noqa: WPS433
        from speech_features import Spectrogram  # noqa: WPS433
        from speech_model import ModelSpeech  # noqa: WPS433
    except Exception as exc:  # pragma: no cover - environment dependent
        print(f"ASRT imports failed: {exc}", file=sys.stderr)
        return 3

    cls = getattr(keras_backend, MODEL_CLASS_NAMES[args.model])
    try:
        acoustic = cls(input_shape=args.input_shape, output_size=args.output_size)
        recognizer = ModelSpeech(acoustic, Spectrogram(), max_label_length=args.max_label_length)
    except Exception as exc:  # pragma: no cover - environment dependent
        print(f"Model construction failed: {exc}", file=sys.stderr)
        return 4

    setup_report: dict[str, Any] = {
        "wav": str(wav_path),
        "weights": str(weights_path),
        "weights_kind": "base" if args.base_weights else "training",
        "class_name": cls.__name__,
        "model_name": acoustic.get_model_name(),
        "input_shape": list(acoustic.input_shape),
        "output_shape": list(acoustic.output_shape),
    }

    if args.dry_run:
        print(json.dumps({"dry_run": True, **setup_report}, indent=2, sort_keys=True))
        return 0

    try:
        if args.base_weights:
            acoustic.get_eval_model().load_weights(str(weights_path))
        else:
            recognizer.load_model(str(weights_path))
    except Exception as exc:  # pragma: no cover - environment dependent
        print(f"Weight loading failed: {exc}", file=sys.stderr)
        return 5

    try:
        pinyin_tokens = recognizer.recognize_speech_from_file(str(wav_path))
    except Exception as exc:  # pragma: no cover - environment dependent
        print(f"Prediction failed: {exc}", file=sys.stderr)
        return 6

    if args.json:
        print(json.dumps({"pinyin_tokens": pinyin_tokens, **setup_report}, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print("ASRT acoustic pinyin tokens:")
        print(" ".join(pinyin_tokens))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
