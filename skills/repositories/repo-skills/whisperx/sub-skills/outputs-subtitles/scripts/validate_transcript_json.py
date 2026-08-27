#!/usr/bin/env python3
"""Validate a minimal WhisperX transcript result JSON file.

This helper checks only post-processing data shape. It does not import WhisperX,
load audio, run ASR, run alignment, call diarization, or download models.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any


class ValidationState:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def error(self, message: str) -> None:
        self.errors.append(message)

    def warn(self, message: str) -> None:
        self.warnings.append(message)


def _is_number(value: Any) -> bool:
    return not isinstance(value, bool) and isinstance(value, (int, float)) and math.isfinite(float(value))


def _validate_time(value: Any, path: str, state: ValidationState) -> float | None:
    if not _is_number(value):
        state.error(f"{path} must be a finite number of seconds")
        return None
    numeric = float(value)
    if numeric < 0:
        state.error(f"{path} must be non-negative")
    return numeric


def _load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def validate_result(data: Any, *, require_words: bool = False, require_word_timestamps: bool = False) -> ValidationState:
    state = ValidationState()

    if not isinstance(data, dict):
        state.error("top-level JSON value must be an object with 'language' and 'segments'")
        return state

    language = data.get("language")
    if not isinstance(language, str) or not language.strip():
        state.error("$.language is required and must be a non-empty string language code")

    segments = data.get("segments")
    if not isinstance(segments, list):
        state.error("$.segments is required and must be a list")
        return state

    if not segments:
        state.warn("$.segments is empty; writers will create empty text/subtitle files")
        return state

    words_presence: list[bool] = []
    total_words = 0
    words_missing_timing = 0
    words_with_timing = 0

    for seg_index, segment in enumerate(segments):
        seg_path = f"$.segments[{seg_index}]"
        if not isinstance(segment, dict):
            state.error(f"{seg_path} must be an object")
            words_presence.append(False)
            continue

        start = _validate_time(segment.get("start"), f"{seg_path}.start", state)
        end = _validate_time(segment.get("end"), f"{seg_path}.end", state)
        if start is not None and end is not None and end < start:
            state.error(f"{seg_path}.end must be greater than or equal to {seg_path}.start")

        if not isinstance(segment.get("text"), str):
            state.error(f"{seg_path}.text is required and must be a string")

        if "speaker" in segment and not isinstance(segment["speaker"], str):
            state.error(f"{seg_path}.speaker must be a string when present")

        has_words = "words" in segment
        words_presence.append(has_words)
        if require_words and not has_words:
            state.error(f"{seg_path}.words is required by --require-words")
        if require_word_timestamps and not has_words:
            state.error(f"{seg_path}.words is required by --require-word-timestamps")

        if not has_words:
            continue

        words = segment["words"]
        if not isinstance(words, list):
            state.error(f"{seg_path}.words must be a list when present")
            continue
        if require_words and not words:
            state.error(f"{seg_path}.words must not be empty when --require-words is used")
        if require_word_timestamps and not words:
            state.error(f"{seg_path}.words must not be empty when --require-word-timestamps is used")

        for word_index, word in enumerate(words):
            word_path = f"{seg_path}.words[{word_index}]"
            total_words += 1
            if not isinstance(word, dict):
                state.error(f"{word_path} must be an object")
                continue
            if not isinstance(word.get("word"), str):
                state.error(f"{word_path}.word is required and must be a string")

            has_start = "start" in word
            has_end = "end" in word
            if has_start != has_end:
                state.error(f"{word_path} must include both start and end, or neither")
            elif has_start and has_end:
                w_start = _validate_time(word.get("start"), f"{word_path}.start", state)
                w_end = _validate_time(word.get("end"), f"{word_path}.end", state)
                if w_start is not None and w_end is not None:
                    if w_end < w_start:
                        state.error(f"{word_path}.end must be greater than or equal to {word_path}.start")
                    if start is not None and end is not None and (w_start < start or w_end > end):
                        state.warn(
                            f"{word_path} timing falls outside its segment; writer will still use the word timing"
                        )
                words_with_timing += 1
            else:
                words_missing_timing += 1
                if require_word_timestamps:
                    state.error(f"{word_path} lacks start/end required by --require-word-timestamps")

            if "score" in word and not _is_number(word["score"]):
                state.error(f"{word_path}.score must be numeric when present")
            if "speaker" in word and not isinstance(word["speaker"], str):
                state.error(f"{word_path}.speaker must be a string when present")

    if any(words_presence) and not all(words_presence):
        if words_presence[0]:
            state.error(
                "mixed word-mode result: the first segment has words, so WhisperX SRT/VTT writers expect words on every segment"
            )
        else:
            state.warn(
                "mixed word-mode result: the first segment lacks words, so later word timings will be ignored by SRT/VTT writers"
            )

    if total_words and words_missing_timing:
        state.warn(
            f"{words_missing_timing} of {total_words} word object(s) lack start/end; plain subtitles may fall back to segment timing, but highlighting is incomplete"
        )
    if total_words and words_with_timing == 0:
        state.warn("no word-level timestamp pairs found; highlight_words output will not underline words")

    return state


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate a minimal WhisperX result JSON file for safe output/subtitle writing."
    )
    parser.add_argument("transcript_json", type=Path, help="Path to a WhisperX-style transcript result JSON file.")
    parser.add_argument(
        "--require-words",
        action="store_true",
        help="Fail if any segment lacks a words list. Useful before word-mode subtitle processing.",
    )
    parser.add_argument(
        "--require-word-timestamps",
        action="store_true",
        help="Fail unless every word has start/end timing pairs suitable for highlight_words.",
    )
    parser.add_argument(
        "--warnings-as-errors",
        action="store_true",
        help="Treat validation warnings as failures.",
    )
    parser.add_argument("--quiet", action="store_true", help="Only print errors and warnings.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    try:
        data = _load_json(args.transcript_json)
    except FileNotFoundError:
        print(f"ERROR: file not found: {args.transcript_json}", file=sys.stderr)
        return 2
    except json.JSONDecodeError as exc:
        print(
            f"ERROR: malformed JSON in {args.transcript_json}: line {exc.lineno}, column {exc.colno}: {exc.msg}",
            file=sys.stderr,
        )
        return 2
    except OSError as exc:
        print(f"ERROR: could not read {args.transcript_json}: {exc}", file=sys.stderr)
        return 2

    state = validate_result(
        data,
        require_words=args.require_words or args.require_word_timestamps,
        require_word_timestamps=args.require_word_timestamps,
    )

    for warning in state.warnings:
        print(f"WARNING: {warning}", file=sys.stderr)
    for error in state.errors:
        print(f"ERROR: {error}", file=sys.stderr)

    if state.errors or (args.warnings_as_errors and state.warnings):
        return 1

    if not args.quiet:
        segment_count = len(data.get("segments", [])) if isinstance(data, dict) else 0
        print(f"OK: validated WhisperX transcript JSON with {segment_count} segment(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
