#!/usr/bin/env python3
"""Safe ClearVoice file-mode recipe.

This helper can list supported models, validate task/model pairing, and run
file/directory/.scp inference only when the user opts in to a real run.
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

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

AUDIO_INPUT_EXTS = {
    ".wav",
    ".aac",
    ".ac3",
    ".aiff",
    ".flac",
    ".m4a",
    ".mp3",
    ".ogg",
    ".opus",
    ".wma",
    ".webm",
}
VIDEO_INPUT_EXTS = {
    ".avi",
    ".mp4",
    ".mov",
    ".webm",
}
VIDEO_ONLY_EXTS = {
    ".avi",
    ".mp4",
    ".mov",
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Safe CLI recipe for pretrained ClearVoice file-mode inference."
    )
    parser.add_argument("--task", help="ClearVoice task to run.")
    parser.add_argument(
        "--model-name",
        action="append",
        default=[],
        metavar="NAME",
        help="Repeatable ClearVoice model name for the selected task.",
    )
    parser.add_argument(
        "--input-path",
        help="Audio, video, directory, or .scp input path for file-mode inference.",
    )
    parser.add_argument(
        "--output-path",
        help="Output file path for a single result, or output directory for batch runs.",
    )
    parser.add_argument(
        "--online-write",
        action="store_true",
        help="Write outputs during processing instead of returning them in memory.",
    )
    parser.add_argument(
        "--list-models",
        action="store_true",
        help="Print the supported task/model catalog and exit without loading weights.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate task/model/input/output choices without loading models or downloading checkpoints.",
    )
    parser.add_argument(
        "--no-download-warning",
        action="store_true",
        help="Suppress the checkpoint download note in real-run mode.",
    )
    return parser


def print_catalog() -> None:
    print("Supported ClearVoice file-mode models:")
    for task, models in SUPPORTED_MODELS.items():
        print(f"- {task}")
        for model in models:
            print(f"  - {model}")


def normalize_models(model_names: list[str]) -> list[str]:
    cleaned = [name.strip() for name in model_names if name and name.strip()]
    return list(dict.fromkeys(cleaned))


def validate_task_and_models(parser: argparse.ArgumentParser, task: str, model_names: list[str]) -> None:
    if task not in SUPPORTED_MODELS:
        parser.error(
            f"Unsupported task {task!r}. Supported tasks are: {', '.join(SUPPORTED_MODELS)}."
        )
    if not model_names:
        parser.error("At least one --model-name is required for a real run.")
    invalid = [name for name in model_names if name not in SUPPORTED_MODELS[task]]
    if invalid:
        parser.error(
            f"Unsupported model(s) for {task!r}: {', '.join(invalid)}. "
            f"Use one of: {', '.join(SUPPORTED_MODELS[task])}."
        )


def validate_input_hint(parser: argparse.ArgumentParser, task: str, input_path: str | None) -> None:
    if not input_path:
        return

    path = Path(input_path)
    suffix = path.suffix.lower()

    if path.is_file() and task != "target_speaker_extraction" and suffix in VIDEO_ONLY_EXTS:
        parser.error(
            f"{task!r} expects audio input, but {input_path!r} looks like a video file."
        )

    if path.is_file() and task == "target_speaker_extraction" and suffix not in VIDEO_INPUT_EXTS and suffix != ".scp":
        parser.error(
            "target_speaker_extraction expects a video file, a video directory, or a .scp file that lists video paths."
        )


def check_ffmpeg(task: str, input_path: str | None) -> bool:
    if not input_path:
        return False
    path = Path(input_path)
    suffix = path.suffix.lower()
    if not path.is_file():
        return False
    if task == "target_speaker_extraction":
        return suffix in VIDEO_INPUT_EXTS
    return suffix in (AUDIO_INPUT_EXTS - {".wav"})


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.list_models:
        print_catalog()
        return 0

    model_names = normalize_models(args.model_name)

    if args.dry_run:
        print("Dry run: no model will be loaded and no checkpoint download will be attempted.")
        if args.task and model_names:
            if args.task not in SUPPORTED_MODELS:
                parser.error(
                    f"Unsupported task {args.task!r}. Supported tasks are: {', '.join(SUPPORTED_MODELS)}."
                )
            invalid = [name for name in model_names if name not in SUPPORTED_MODELS[args.task]]
            if invalid:
                parser.error(
                    f"Unsupported model(s) for {args.task!r}: {', '.join(invalid)}. "
                    f"Use one of: {', '.join(SUPPORTED_MODELS[args.task])}."
                )
            validate_input_hint(parser, args.task, args.input_path)

        if args.task:
            print(f"Task: {args.task}")
        if model_names:
            print(f"Model names: {', '.join(model_names)}")
        if args.input_path:
            print(f"Input path: {args.input_path}")
        if args.output_path:
            print(f"Output path: {args.output_path}")

        if args.task and model_names:
            if args.task == "target_speaker_extraction" and args.online_write is False:
                print("Note: target_speaker_extraction will require --online-write in a real run.")
            if check_ffmpeg(args.task, args.input_path) and shutil.which("ffmpeg") is None:
                print("Warning: this input will need FFmpeg in a real run, but ffmpeg was not found on PATH.", file=sys.stderr)
        elif args.task and not model_names:
            print("Note: add at least one --model-name to validate a specific task/model pair.")

        return 0

    if not args.task:
        parser.error("--task is required unless you are using --list-models or --dry-run.")
    validate_task_and_models(parser, args.task, model_names)
    validate_input_hint(parser, args.task, args.input_path)

    if args.task == "target_speaker_extraction" and not args.online_write:
        parser.error("target_speaker_extraction requires --online-write.")
    if args.online_write and not args.output_path:
        parser.error("--output-path is required when using --online-write.")
    if not args.input_path:
        parser.error("--input-path is required for a real run.")
    if not Path(args.input_path).exists():
        parser.error(f"Input path {args.input_path!r} does not exist.")

    if check_ffmpeg(args.task, args.input_path) and shutil.which("ffmpeg") is None:
        parser.error(
            "FFmpeg is required for this input type, but ffmpeg was not found on PATH. "
            "Install FFmpeg and rerun the command."
        )

    try:
        from clearvoice import ClearVoice
    except ImportError:
        print("ImportError: install the ClearVoice package first with `pip install clearvoice`.", file=sys.stderr)
        return 2

    if not args.no_download_warning:
        print(
            "Note: ClearVoice may download missing checkpoints into its default checkpoint directory on first use.",
            file=sys.stderr,
        )

    runner = ClearVoice(task=args.task, model_names=model_names)
    input_path = str(Path(args.input_path))

    if args.online_write:
        runner(input_path=input_path, online_write=True, output_path=args.output_path)
        print(f"Wrote outputs under {args.output_path}")
        return 0

    results = runner(input_path=input_path, online_write=False)
    if args.output_path:
        runner.write(results, output_path=args.output_path)
        print(f"Wrote outputs to {args.output_path}")
    else:
        print(f"Returned in-memory results of type {type(results).__name__}")
        if hasattr(results, "shape"):
            print(f"Result shape: {results.shape}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
