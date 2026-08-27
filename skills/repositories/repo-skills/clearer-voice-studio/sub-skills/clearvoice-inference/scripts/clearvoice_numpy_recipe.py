#!/usr/bin/env python3
"""Safe ClearVoice NumPy/Tensor recipe.

This helper validates array shapes by default and only loads one ClearVoice
model when the user explicitly asks for a real run with --run.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np

SUPPORTED_MODELS = {
    "speech_enhancement": [
        "FRCRN_SE_16K",
        "MossFormer2_SE_48K",
        "MossFormerGAN_SE_16K",
    ],
    "speech_separation": ["MossFormer2_SS_16K"],
    "speech_super_resolution": ["MossFormer2_SR_48K"],
    "target_speaker_extraction": ["AV_MossFormer2_TSE_16K"],
}

MODEL_TO_TASK = {
    "FRCRN_SE_16K": "speech_enhancement",
    "MossFormer2_SE_48K": "speech_enhancement",
    "MossFormerGAN_SE_16K": "speech_enhancement",
    "MossFormer2_SS_16K": "speech_separation",
    "MossFormer2_SR_48K": "speech_super_resolution",
    "AV_MossFormer2_TSE_16K": "target_speaker_extraction",
}

EXPECTED_SAMPLE_RATE = {
    "FRCRN_SE_16K": 16000,
    "MossFormer2_SE_48K": 48000,
    "MossFormerGAN_SE_16K": 16000,
    "MossFormer2_SS_16K": 16000,
    "MossFormer2_SR_48K": 48000,
    "AV_MossFormer2_TSE_16K": 16000,
}

AUDIO_ONLY_TASKS = {"speech_enhancement", "speech_separation", "speech_super_resolution"}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Safe CLI recipe for ClearVoice NumPy/Tensor inference."
    )
    parser.add_argument("--task", help="ClearVoice task to inspect or run in tensor mode.")
    parser.add_argument(
        "--model-name",
        action="append",
        default=[],
        metavar="NAME",
        help="Repeatable ClearVoice model name. Tensor mode accepts exactly one model.",
    )
    parser.add_argument(
        "--input-path",
        help="Optional .npy file containing a batch shaped like [batch, length].",
    )
    parser.add_argument(
        "--output-path",
        help="Optional .npy file for saving the output array when --run is used.",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=1,
        help="Synthetic batch size used when no input file is supplied.",
    )
    parser.add_argument(
        "--length",
        type=int,
        default=16000,
        help="Synthetic sample length used when no input file is supplied.",
    )
    parser.add_argument(
        "--run",
        action="store_true",
        help="Load one model and run inference instead of only validating shapes.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Force validation-only mode even if --run is present.",
    )
    return parser


def normalize_models(model_names: list[str]) -> list[str]:
    cleaned = [name.strip() for name in model_names if name and name.strip()]
    return list(dict.fromkeys(cleaned))


def infer_task(task: str | None, model_names: list[str]) -> str | None:
    if task:
        return task
    if len(model_names) == 1:
        return MODEL_TO_TASK.get(model_names[0])
    return None


def validate_tensor_request(parser: argparse.ArgumentParser, task: str | None, model_names: list[str], run_requested: bool) -> str | None:
    if task == "target_speaker_extraction":
        parser.error(
            "Tensor mode does not support target_speaker_extraction. Use the file-mode recipe with video input and online_write=True."
        )

    if task and task not in SUPPORTED_MODELS:
        parser.error(
            f"Unsupported task {task!r}. Supported tasks are: {', '.join(SUPPORTED_MODELS)}."
        )

    if len(model_names) > 1:
        parser.error("Tensor mode supports only one model. Use file-mode inference if you need several models.")

    resolved_task = infer_task(task, model_names)
    if model_names and not resolved_task:
        parser.error(f"Could not infer a task for model {model_names[0]!r}.")

    if model_names and resolved_task and model_names[0] not in SUPPORTED_MODELS.get(resolved_task, []):
        parser.error(
            f"Unsupported model {model_names[0]!r} for task {resolved_task!r}."
        )

    if run_requested:
        if not model_names:
            parser.error("Provide exactly one --model-name when you want to run tensor-mode inference.")
        if resolved_task not in AUDIO_ONLY_TASKS:
            parser.error(
                "Tensor-mode runs are only available for speech_enhancement, speech_separation, and speech_super_resolution."
            )

    return resolved_task


def load_numpy_batch(parser: argparse.ArgumentParser, input_path: str | None, batch_size: int, length: int) -> np.ndarray:
    if batch_size <= 0:
        parser.error("--batch-size must be a positive integer.")
    if length <= 0:
        parser.error("--length must be a positive integer.")

    if input_path:
        path = Path(input_path)
        if not path.exists():
            parser.error(f"Input file {input_path!r} does not exist.")
        if path.suffix.lower() != ".npy":
            parser.error("This helper expects a .npy file when --input-path is supplied.")
        array = np.load(path, allow_pickle=False)
    else:
        array = np.zeros((batch_size, length), dtype=np.float32)

    array = np.asarray(array, dtype=np.float32)
    if array.ndim == 1:
        array = array[np.newaxis, :]
    if array.ndim != 2:
        parser.error("Tensor mode expects a rank-2 array shaped like [batch, length].")
    return array


def describe_expected_output(task: str | None, array: np.ndarray) -> str:
    if task == "speech_separation":
        return f"[2, {array.shape[0]}, {array.shape[1]}]"
    return f"[{array.shape[0]}, {array.shape[1]}]"


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    model_names = normalize_models(args.model_name)
    dry_run = args.dry_run or not args.run

    resolved_task = validate_tensor_request(parser, args.task, model_names, run_requested=not dry_run)
    array = load_numpy_batch(parser, args.input_path, args.batch_size, args.length)

    print("Tensor validation summary:")
    if resolved_task:
        print(f"- task: {resolved_task}")
    if model_names:
        print(f"- model: {model_names[0]}")
        print(f"- expected sample rate: {EXPECTED_SAMPLE_RATE.get(model_names[0], 'unknown')} Hz")
    print(f"- input shape: {tuple(array.shape)}")
    print(f"- expected output shape: {describe_expected_output(resolved_task, array)}")

    if dry_run:
        print("- mode: validation only; no model will be loaded.")
        return 0

    try:
        from clearvoice import ClearVoice
    except ImportError:
        print("ImportError: install the ClearVoice package first with `pip install clearvoice`.", file=sys.stderr)
        return 2

    runner = ClearVoice(task=resolved_task, model_names=[model_names[0]])
    output = runner(array)

    output_array = np.asarray(output)
    print(f"- actual output shape: {tuple(output_array.shape)}")

    if args.output_path:
        output_path = Path(args.output_path)
        if output_path.suffix.lower() != ".npy":
            output_path = output_path.with_suffix(".npy")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        np.save(output_path, output_array)
        print(f"Saved output to {output_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
