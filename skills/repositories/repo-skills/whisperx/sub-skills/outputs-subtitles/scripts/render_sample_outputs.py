#!/usr/bin/env python3
"""Render safe sample WhisperX outputs without ASR/model execution.

The script creates or loads a small WhisperX-style result dictionary and sends it
to whisperx.utils.get_writer. It does not load audio, run transcription, run
alignment, run diarization, use credentials, or download models.
"""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path
from typing import Any

CORE_ALL_FORMATS = ("txt", "vtt", "srt", "tsv", "json")
ALL_FORMATS = CORE_ALL_FORMATS + ("aud",)


def sample_transcript(kind: str) -> dict[str, Any]:
    if kind == "speaker-words":
        return {
            "language": "en",
            "segments": [
                {
                    "start": 0.0,
                    "end": 1.35,
                    "text": "Hello world.",
                    "speaker": "SPEAKER_00",
                    "words": [
                        {"word": "Hello", "start": 0.0, "end": 0.45, "score": 0.99},
                        {"word": "world.", "start": 0.55, "end": 1.2, "score": 0.98},
                    ],
                },
                {
                    "start": 1.6,
                    "end": 3.1,
                    "text": "A second speaker replies.",
                    "speaker": "SPEAKER_01",
                    "words": [
                        {"word": "A", "start": 1.6, "end": 1.72, "score": 0.96},
                        {"word": "second", "start": 1.73, "end": 2.18, "score": 0.97},
                        {"word": "speaker", "start": 2.2, "end": 2.68, "score": 0.97},
                        {"word": "replies.", "start": 2.7, "end": 3.05, "score": 0.95},
                    ],
                },
            ],
        }
    if kind == "missing-word-timings":
        return {
            "language": "en",
            "segments": [
                {
                    "start": 0.0,
                    "end": 2.0,
                    "text": "Fallback timing is readable.",
                    "speaker": "SPEAKER_00",
                    "words": [
                        {"word": "Fallback"},
                        {"word": "timing"},
                        {"word": "is"},
                        {"word": "readable."},
                    ],
                },
                {
                    "start": 2.2,
                    "end": 3.7,
                    "text": "Highlighting needs alignment.",
                    "speaker": "SPEAKER_00",
                    "words": [
                        {"word": "Highlighting"},
                        {"word": "needs"},
                        {"word": "alignment."},
                    ],
                },
            ],
        }
    if kind == "no-words":
        return {
            "language": "en",
            "segments": [
                {"start": 0.0, "end": 1.25, "text": "Segment timing only.", "speaker": "SPEAKER_00"},
                {"start": 1.5, "end": 2.75, "text": "No word highlighting here.", "speaker": "SPEAKER_01"},
            ],
        }
    if kind == "zh":
        return {
            "language": "zh",
            "segments": [
                {
                    "start": 0.0,
                    "end": 1.8,
                    "text": "你好世界，欢迎。",
                    "speaker": "SPEAKER_00",
                    "words": [
                        {"word": "你好", "start": 0.0, "end": 0.45, "score": 0.99},
                        {"word": "世界，", "start": 0.5, "end": 1.0, "score": 0.98},
                        {"word": "欢迎。", "start": 1.05, "end": 1.65, "score": 0.97},
                    ],
                }
            ],
        }
    raise ValueError(f"unknown sample kind: {kind}")


def load_transcript_json(path: Path) -> dict[str, Any]:
    try:
        with path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
    except FileNotFoundError as exc:
        raise SystemExit(f"ERROR: transcript JSON not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise SystemExit(
            f"ERROR: malformed JSON in {path}: line {exc.lineno}, column {exc.colno}: {exc.msg}"
        ) from exc
    except OSError as exc:
        raise SystemExit(f"ERROR: could not read {path}: {exc}") from exc

    if not isinstance(data, dict):
        raise SystemExit("ERROR: transcript JSON top level must be an object")
    return data


def parse_formats(raw: str) -> list[str]:
    requested = [part.strip().lower() for part in raw.split(",") if part.strip()]
    if not requested:
        raise SystemExit("ERROR: --formats must name at least one format")

    invalid = [fmt for fmt in requested if fmt not in ALL_FORMATS and fmt != "all"]
    if invalid:
        choices = ", ".join((*ALL_FORMATS, "all"))
        raise SystemExit(f"ERROR: unsupported format(s): {', '.join(invalid)}. Choices: {choices}")

    deduped: list[str] = []
    for fmt in requested:
        if fmt not in deduped:
            deduped.append(fmt)
    return deduped


def expected_extensions(formats: list[str]) -> list[str]:
    extensions: list[str] = []
    for fmt in formats:
        if fmt == "all":
            candidates = CORE_ALL_FORMATS
        else:
            candidates = (fmt,)
        for ext in candidates:
            if ext not in extensions:
                extensions.append(ext)
    return extensions


def basic_validate_for_rendering(result: dict[str, Any]) -> list[str]:
    warnings: list[str] = []
    if not isinstance(result.get("language"), str) or not result.get("language", "").strip():
        raise SystemExit("ERROR: transcript must contain a non-empty string 'language' field")
    segments = result.get("segments")
    if not isinstance(segments, list):
        raise SystemExit("ERROR: transcript must contain a 'segments' list")
    if not segments:
        warnings.append("segments is empty; output files will contain no transcript cues")
        return warnings

    words_presence = []
    timed_words = 0
    untimed_words = 0
    one_sided_timing = 0
    for seg_index, segment in enumerate(segments):
        if not isinstance(segment, dict):
            raise SystemExit(f"ERROR: segments[{seg_index}] must be an object")
        for key in ("start", "end", "text"):
            if key not in segment:
                raise SystemExit(f"ERROR: segments[{seg_index}] is missing required field {key!r}")
        has_words = "words" in segment
        words_presence.append(has_words)
        if not has_words:
            continue
        if not isinstance(segment["words"], list):
            raise SystemExit(f"ERROR: segments[{seg_index}].words must be a list")
        for word_index, word in enumerate(segment["words"]):
            if not isinstance(word, dict) or not isinstance(word.get("word"), str):
                raise SystemExit(f"ERROR: segments[{seg_index}].words[{word_index}] must contain a string 'word'")
            has_start = "start" in word
            has_end = "end" in word
            if has_start and has_end:
                timed_words += 1
            elif has_start != has_end:
                one_sided_timing += 1
            else:
                untimed_words += 1

    if any(words_presence) and not all(words_presence):
        if words_presence[0]:
            raise SystemExit(
                "ERROR: first segment has words, so WhisperX SRT/VTT writers require words on every segment"
            )
        warnings.append("first segment has no words; later word timings will be ignored by SRT/VTT writers")
    if one_sided_timing:
        raise SystemExit("ERROR: word timing records must contain both start and end, or neither")
    if timed_words == 0:
        warnings.append("no word start/end pairs found; highlight_words will not underline words")
    elif untimed_words:
        warnings.append(f"{untimed_words} word(s) lack start/end; highlighting will be incomplete for those words")
    return warnings


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Render sample WhisperX output files via whisperx.utils.get_writer without running ASR models."
    )
    parser.add_argument(
        "--transcript-json",
        type=Path,
        default=None,
        help="Use an existing WhisperX-style result JSON instead of a built-in sample.",
    )
    parser.add_argument(
        "--sample",
        choices=("speaker-words", "missing-word-timings", "no-words", "zh"),
        default="speaker-words",
        help="Built-in sample to use when --transcript-json is not provided.",
    )
    parser.add_argument(
        "--formats",
        default="srt,vtt,json",
        help="Comma-separated formats to write: txt,vtt,srt,tsv,json,aud,all. 'all' writes WhisperX core formats, not aud.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Directory for rendered files. Defaults to a new temporary directory to avoid overwrites.",
    )
    parser.add_argument(
        "--audio-basename",
        default="sample_audio.wav",
        help="Audio-like filename used only to derive output basenames; the file is not opened.",
    )
    parser.add_argument("--highlight-words", action="store_true", help="Pass highlight_words=True to SRT/VTT writers.")
    parser.add_argument("--max-line-width", type=int, default=None, help="Pass max_line_width to SRT/VTT writers.")
    parser.add_argument("--max-line-count", type=int, default=None, help="Pass max_line_count to SRT/VTT writers.")
    parser.add_argument(
        "--force-overwrite",
        action="store_true",
        help="Allow overwriting files in --output-dir when names already exist.",
    )
    parser.add_argument("--list-samples", action="store_true", help="List built-in samples and exit without writing files.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if args.list_samples:
        print("speaker-words: two speaker-labeled English segments with complete word timestamps")
        print("missing-word-timings: speaker-labeled words without start/end to show segment-level fallback")
        print("no-words: segment-level transcript with no word list")
        print("zh: Chinese sample showing no-space language behavior in plain word-mode subtitles")
        return 0

    try:
        from whisperx.utils import LANGUAGES_WITHOUT_SPACES, get_writer
    except Exception as exc:  # pragma: no cover - environment-specific import error detail
        print(f"ERROR: could not import whisperx.utils.get_writer: {exc}", file=sys.stderr)
        return 2

    result = load_transcript_json(args.transcript_json) if args.transcript_json else sample_transcript(args.sample)
    warnings = basic_validate_for_rendering(result)

    if args.max_line_count is not None and args.max_line_width is None:
        warnings.append("max_line_count has no effect unless max_line_width is also set")
    if args.highlight_words:
        any_timed_word = any(
            "start" in word and "end" in word
            for segment in result.get("segments", [])
            if isinstance(segment, dict)
            for word in segment.get("words", [])
            if isinstance(word, dict)
        )
        if not any_timed_word:
            warnings.append("highlight_words=True requested, but no word timestamps are available; output falls back to plain cues")
    if result.get("language") in LANGUAGES_WITHOUT_SPACES and args.highlight_words:
        warnings.append("highlighted cues may contain spaces even for languages normally rendered without spaces")

    for warning in warnings:
        print(f"WARNING: {warning}", file=sys.stderr)

    formats = parse_formats(args.formats)
    if args.output_dir is None:
        output_dir = Path(tempfile.mkdtemp(prefix="whisperx_render_"))
        print(f"Using temporary output directory: {output_dir}")
    else:
        output_dir = args.output_dir
        output_dir.mkdir(parents=True, exist_ok=True)

    basename = Path(args.audio_basename).stem
    targets = [output_dir / f"{basename}.{ext}" for ext in expected_extensions(formats)]
    existing = [target for target in targets if target.exists()]
    if existing and not args.force_overwrite:
        joined = ", ".join(str(path) for path in existing)
        print(f"ERROR: refusing to overwrite existing output file(s): {joined}", file=sys.stderr)
        print("Pass --force-overwrite or choose a fresh --output-dir.", file=sys.stderr)
        return 2

    options = {
        "highlight_words": bool(args.highlight_words),
        "max_line_width": args.max_line_width,
        "max_line_count": args.max_line_count,
    }

    try:
        for fmt in formats:
            writer = get_writer(fmt, str(output_dir))
            writer(result, args.audio_basename, options)
    except KeyError as exc:
        print(f"ERROR: unsupported writer format: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:  # pragma: no cover - depends on installed package behavior
        print(f"ERROR: writer failed: {exc}", file=sys.stderr)
        return 1

    print("Wrote:")
    for target in targets:
        print(f"  {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
