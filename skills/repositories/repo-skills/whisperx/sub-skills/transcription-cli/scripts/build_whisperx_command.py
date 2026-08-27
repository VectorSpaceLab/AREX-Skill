#!/usr/bin/env python3
"""Build a shell-quoted WhisperX CLI command without executing it.

The helper validates obvious CLI conflicts and prints a command that a user can
review or copy. It never imports whisperx, touches audio files, reads token
values, downloads models, creates output directories, or executes the command.
"""

from __future__ import annotations

import argparse
import re
import shlex
import sys
from dataclasses import dataclass
from typing import Iterable, List, Optional


OUTPUT_FORMATS = ("all", "srt", "vtt", "txt", "tsv", "json", "aud")
COMPUTE_TYPES = ("default", "float16", "float32", "int8")
VAD_METHODS = ("pyannote", "silero")
TASKS = ("transcribe", "translate")
INTERPOLATE_METHODS = ("nearest", "linear", "ignore")
LOG_LEVELS = ("debug", "info", "warning", "error", "critical")
BOOL_TEXT = ("True", "False")
ENV_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


@dataclass(frozen=True)
class ShellPart:
    value: str
    quote: bool = True


def positive_int(text: str) -> int:
    value = int(text)
    if value <= 0:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return value


def zero_to_one_float(text: str) -> float:
    value = float(text)
    if not 0.0 < value < 1.0:
        raise argparse.ArgumentTypeError("must be between 0 and 1")
    return value


def normalize_env_name(text: str) -> str:
    name = text[1:] if text.startswith("$") else text
    if not ENV_RE.fullmatch(name):
        raise argparse.ArgumentTypeError(
            "must be an environment variable name like HF_TOKEN, not a token value"
        )
    return name


def add_flag(parts: List[ShellPart], flag: str, value: Optional[object] = None) -> None:
    parts.append(ShellPart(flag))
    if value is not None:
        parts.append(ShellPart(str(value)))


def shell_join(parts: Iterable[ShellPart]) -> str:
    rendered = []
    for part in parts:
        rendered.append(part.value if not part.quote else shlex.quote(part.value))
    return " ".join(rendered)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Print a shell-quoted whisperx command without running WhisperX, "
            "checking files, reading token values, downloading models, or writing outputs."
        )
    )
    parser.add_argument("--audio", nargs="+", required=True, help="Audio file path(s) to place as positional CLI arguments; paths are not checked.")
    parser.add_argument("--model", help="Whisper model name, e.g. small, base, large, large-v2.")
    parser.add_argument("--device", help="Device string for WhisperX, commonly cpu or cuda.")
    parser.add_argument("--compute-type", choices=COMPUTE_TYPES, help="Map to WhisperX --compute_type.")
    parser.add_argument("--batch-size", type=positive_int, help="Map to WhisperX --batch_size.")
    parser.add_argument("--language", help="Language code/name to pass to WhisperX --language.")
    parser.add_argument("--task", choices=TASKS, help="Transcribe or translate. translate disables alignment in WhisperX.")
    parser.add_argument("--output-dir", help="Output directory to pass to WhisperX; this helper does not create it.")
    parser.add_argument("--output-format", choices=OUTPUT_FORMATS, help="Output format to pass to WhisperX --output_format.")
    parser.add_argument("--model-dir", help="Model cache/download directory to pass to WhisperX --model_dir.")
    parser.add_argument("--model-cache-only", action="store_true", help="Emit --model_cache_only True so WhisperX uses local cached models only.")
    parser.add_argument("--no-align", action="store_true", help="Emit --no_align and validate word-output conflicts.")
    parser.add_argument("--align-model", help="Optional alignment model override.")
    parser.add_argument("--interpolate-method", choices=INTERPOLATE_METHODS, help="Alignment interpolation method.")
    parser.add_argument("--return-char-alignments", action="store_true", help="Emit --return_char_alignments.")
    parser.add_argument("--highlight-words", choices=BOOL_TEXT, help="Emit --highlight_words True/False. True requires alignment.")
    parser.add_argument("--max-line-width", type=positive_int, help="Emit --max_line_width. Requires alignment.")
    parser.add_argument("--max-line-count", type=positive_int, help="Emit --max_line_count. Requires alignment and max line width to matter.")
    parser.add_argument("--vad-method", choices=VAD_METHODS, help="VAD backend to pass to WhisperX --vad_method.")
    parser.add_argument("--vad-onset", type=zero_to_one_float, help="VAD onset threshold between 0 and 1.")
    parser.add_argument("--vad-offset", type=zero_to_one_float, help="VAD offset threshold between 0 and 1.")
    parser.add_argument("--chunk-size", type=positive_int, help="VAD chunk size in seconds.")
    parser.add_argument("--diarize", action="store_true", help="Emit --diarize.")
    parser.add_argument("--hf-token-env", type=normalize_env_name, help="Environment variable name to emit as --hf_token $NAME; token values are never read.")
    parser.add_argument("--min-speakers", type=positive_int, help="Emit --min_speakers for diarization.")
    parser.add_argument("--max-speakers", type=positive_int, help="Emit --max_speakers for diarization.")
    parser.add_argument("--diarize-model", help="Emit --diarize_model.")
    parser.add_argument("--log-level", choices=LOG_LEVELS, help="Emit --log-level.")
    parser.add_argument("--verbose", choices=BOOL_TEXT, help="Emit --verbose True/False.")
    parser.add_argument("--print-progress", choices=BOOL_TEXT, help="Emit --print_progress True/False.")
    return parser


def validate_args(parser: argparse.ArgumentParser, args: argparse.Namespace) -> None:
    alignment_disabled = args.no_align or args.task == "translate"
    conflicting_word_options = []
    if args.highlight_words == "True":
        conflicting_word_options.append("--highlight-words True")
    if args.max_line_width is not None:
        conflicting_word_options.append("--max-line-width")
    if args.max_line_count is not None:
        conflicting_word_options.append("--max-line-count")

    if alignment_disabled and conflicting_word_options:
        disable_reason = "--task translate" if args.task == "translate" and not args.no_align else "--no-align"
        parser.error(
            f"word-level subtitle options require alignment; {disable_reason} conflicts with "
            f"{', '.join(conflicting_word_options)}. Remove the word options or enable alignment."
        )

    if args.max_line_count is not None and args.max_line_width is None:
        print(
            "warning: WhisperX --max_line_count has no effect unless --max_line_width is also set.",
            file=sys.stderr,
        )

    if (args.min_speakers is not None or args.max_speakers is not None or args.diarize_model) and not args.diarize:
        parser.error("speaker-count or diarization-model options require --diarize")

    if args.min_speakers is not None and args.max_speakers is not None and args.min_speakers > args.max_speakers:
        parser.error("--min-speakers cannot be greater than --max-speakers")

    if args.diarize and args.hf_token_env is None:
        print(
            "warning: --diarize emitted without --hf_token; many diarization models require a token and accepted terms.",
            file=sys.stderr,
        )
    elif args.hf_token_env is not None and not args.diarize:
        print(
            "warning: --hf_token emitted without --diarize; this is usually only needed for diarization or private model access.",
            file=sys.stderr,
        )


def build_command(args: argparse.Namespace) -> str:
    parts: List[ShellPart] = [ShellPart("whisperx")]
    for audio_path in args.audio:
        parts.append(ShellPart(audio_path))

    add_flag(parts, "--model", args.model) if args.model else None
    add_flag(parts, "--device", args.device) if args.device else None
    add_flag(parts, "--compute_type", args.compute_type) if args.compute_type else None
    add_flag(parts, "--batch_size", args.batch_size) if args.batch_size is not None else None
    add_flag(parts, "--language", args.language) if args.language else None
    add_flag(parts, "--task", args.task) if args.task else None
    add_flag(parts, "--output_dir", args.output_dir) if args.output_dir else None
    add_flag(parts, "--output_format", args.output_format) if args.output_format else None
    add_flag(parts, "--model_dir", args.model_dir) if args.model_dir else None
    add_flag(parts, "--model_cache_only", "True") if args.model_cache_only else None

    add_flag(parts, "--no_align") if args.no_align else None
    add_flag(parts, "--align_model", args.align_model) if args.align_model else None
    add_flag(parts, "--interpolate_method", args.interpolate_method) if args.interpolate_method else None
    add_flag(parts, "--return_char_alignments") if args.return_char_alignments else None
    add_flag(parts, "--highlight_words", args.highlight_words) if args.highlight_words is not None else None
    add_flag(parts, "--max_line_width", args.max_line_width) if args.max_line_width is not None else None
    add_flag(parts, "--max_line_count", args.max_line_count) if args.max_line_count is not None else None

    add_flag(parts, "--vad_method", args.vad_method) if args.vad_method else None
    add_flag(parts, "--vad_onset", args.vad_onset) if args.vad_onset is not None else None
    add_flag(parts, "--vad_offset", args.vad_offset) if args.vad_offset is not None else None
    add_flag(parts, "--chunk_size", args.chunk_size) if args.chunk_size is not None else None

    add_flag(parts, "--diarize") if args.diarize else None
    add_flag(parts, "--min_speakers", args.min_speakers) if args.min_speakers is not None else None
    add_flag(parts, "--max_speakers", args.max_speakers) if args.max_speakers is not None else None
    add_flag(parts, "--diarize_model", args.diarize_model) if args.diarize_model else None
    if args.hf_token_env:
        parts.append(ShellPart("--hf_token"))
        parts.append(ShellPart(f"${args.hf_token_env}", quote=False))

    add_flag(parts, "--log-level", args.log_level) if args.log_level else None
    add_flag(parts, "--verbose", args.verbose) if args.verbose is not None else None
    add_flag(parts, "--print_progress", args.print_progress) if args.print_progress is not None else None
    return shell_join(parts)


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    validate_args(parser, args)
    print(build_command(args))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
