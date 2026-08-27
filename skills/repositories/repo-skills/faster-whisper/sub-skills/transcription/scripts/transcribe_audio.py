#!/usr/bin/env python3
"""Configurable faster-whisper transcription helper.

Purpose: transcribe a local audio file or stream with the public faster-whisper
package. This helper is safe to inspect with --help and does not depend on the
original repository checkout. Real transcription may download or load a model.

Example:
    python transcribe_audio.py --audio audio.mp3 --model tiny --device cpu \
        --compute-type int8 --language en
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Transcribe audio with faster-whisper."
    )
    parser.add_argument("--audio", required=True, help="Path to an input audio file.")
    parser.add_argument(
        "--model",
        default="tiny",
        help="Model alias, HF CTranslate2 id, or local CTranslate2 directory.",
    )
    parser.add_argument(
        "--device",
        default="auto",
        help='Compute device to use, such as "auto", "cpu", or "cuda".',
    )
    parser.add_argument(
        "--compute-type",
        default="default",
        help='CTranslate2 compute type, such as "default", "int8", or "float16".',
    )
    parser.add_argument("--language", help="Optional ISO language code.")
    parser.add_argument(
        "--task",
        choices=("transcribe", "translate"),
        default="transcribe",
        help="Transcription task to run.",
    )
    parser.add_argument("--beam-size", type=int, default=5, help="Beam size.")
    parser.add_argument(
        "--batched",
        action="store_true",
        help="Use BatchedInferencePipeline instead of WhisperModel.",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=8,
        help="Batch size used only with --batched.",
    )
    parser.add_argument(
        "--word-timestamps",
        action="store_true",
        help="Print word-level timestamps when available.",
    )
    parser.add_argument(
        "--vad-filter",
        action="store_true",
        help="Enable VAD filtering.",
    )
    parser.add_argument(
        "--hotwords",
        help="Comma-separated hotwords or hint phrases.",
    )
    parser.add_argument(
        "--condition-on-previous-text",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Toggle previous-window conditioning.",
    )
    parser.add_argument(
        "--download-root",
        help="Directory where Hugging Face snapshots are cached.",
    )
    parser.add_argument(
        "--local-files-only",
        action="store_true",
        help="Fail if the requested model is not already cached locally.",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        help="Logging level for faster_whisper and this helper.",
    )
    parser.add_argument(
        "--max-segments",
        type=int,
        help="Stop after printing this many segments.",
    )
    return parser


def configure_logging(level: str) -> None:
    numeric = getattr(logging, level.upper(), None)
    if not isinstance(numeric, int):
        raise SystemExit(f"Unknown log level: {level!r}")
    logging.basicConfig(level=numeric, format="%(levelname)s: %(message)s")
    logging.getLogger("faster_whisper").setLevel(numeric)


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    configure_logging(args.log_level)

    try:
        from faster_whisper import BatchedInferencePipeline, WhisperModel
    except ImportError as exc:
        raise SystemExit(
            "faster-whisper is not installed in the current environment: %s" % exc
        ) from exc

    audio_path = Path(args.audio)
    if not audio_path.exists():
        raise SystemExit(f"Audio file does not exist: {audio_path}")

    try:
        model = WhisperModel(
            args.model,
            device=args.device,
            compute_type=args.compute_type,
            download_root=args.download_root,
            local_files_only=args.local_files_only,
        )
        if args.batched:
            runner = BatchedInferencePipeline(model=model)
            transcribe_kwargs = {"batch_size": args.batch_size}
        else:
            runner = model
            transcribe_kwargs = {}

        segments, info = runner.transcribe(
            str(audio_path),
            language=args.language,
            task=args.task,
            beam_size=args.beam_size,
            vad_filter=args.vad_filter,
            condition_on_previous_text=args.condition_on_previous_text,
            hotwords=args.hotwords,
            word_timestamps=args.word_timestamps,
            **transcribe_kwargs,
        )
    except RuntimeError as exc:
        raise SystemExit(f"faster-whisper runtime error: {exc}") from exc
    except Exception as exc:  # noqa: BLE001 - present concise CLI errors
        raise SystemExit(f"failed to initialize or transcribe: {exc}") from exc

    print(f"language: {info.language} ({info.language_probability:.3f})")
    print(f"duration: {info.duration:.2f}s")
    if info.duration_after_vad != info.duration:
        print(f"duration_after_vad: {info.duration_after_vad:.2f}s")

    count = 0
    for segment in segments:
        print(f"[{segment.start:.2f} -> {segment.end:.2f}] {segment.text}")
        if args.word_timestamps and segment.words:
            for word in segment.words:
                print(
                    f"  word [{word.start:.2f} -> {word.end:.2f}] "
                    f"{word.word} ({word.probability:.3f})"
                )
        count += 1
        if args.max_segments is not None and count >= args.max_segments:
            break

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
