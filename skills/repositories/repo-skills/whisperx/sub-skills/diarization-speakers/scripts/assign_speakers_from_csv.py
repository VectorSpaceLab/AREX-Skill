#!/usr/bin/env python3
"""Assign WhisperX speaker labels from a diarization CSV.

This helper is intentionally offline and safe by default: it does not create a
DiarizationPipeline, does not accept Hugging Face tokens, and does not download
models. It reads transcript JSON plus a CSV containing start,end,speaker rows,
calls whisperx.diarize.assign_word_speakers, and writes a new JSON file.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from pathlib import Path
from typing import Any

REQUIRED_COLUMNS = {"start", "end", "speaker"}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Assign speakers to WhisperX transcript segments/words from an "
            "existing diarization CSV. Does not instantiate diarization models."
        )
    )
    parser.add_argument(
        "--transcript-json",
        required=True,
        type=Path,
        help="Input WhisperX transcript JSON with a top-level segments list.",
    )
    parser.add_argument(
        "--diarization-csv",
        required=True,
        type=Path,
        help="CSV containing required columns: start,end,speaker (seconds).",
    )
    parser.add_argument(
        "--output-json",
        required=True,
        type=Path,
        help="New JSON path to write; existing files are not overwritten.",
    )
    parser.add_argument(
        "--fill-nearest",
        action="store_true",
        help="Assign nearest speaker when a segment/word has no direct overlap.",
    )
    return parser


def fail(message: str) -> None:
    raise ValueError(message)


def load_transcript(path: Path) -> dict[str, Any]:
    if not path.is_file():
        fail(f"transcript JSON not found: {path}")
    try:
        with path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
    except json.JSONDecodeError as exc:
        fail(f"invalid transcript JSON at line {exc.lineno} column {exc.colno}: {exc.msg}")
    if not isinstance(data, dict):
        fail("transcript JSON must be an object/dictionary")
    segments = data.get("segments")
    if not isinstance(segments, list):
        fail("transcript JSON must contain a top-level 'segments' list")
    for index, segment in enumerate(segments):
        if not isinstance(segment, dict):
            fail(f"segments[{index}] must be an object")
        words = segment.get("words")
        if words is not None and not isinstance(words, list):
            fail(f"segments[{index}].words must be a list when present")
    return data


def parse_float(value: Any, *, row_number: int, column: str) -> float:
    text = "" if value is None else str(value).strip()
    if text == "":
        fail(f"row {row_number}: missing {column!r}")
    try:
        number = float(text)
    except ValueError:
        fail(f"row {row_number}: {column!r} is not numeric: {text!r}")
    if not math.isfinite(number):
        fail(f"row {row_number}: {column!r} must be finite")
    if number < 0:
        fail(f"row {row_number}: {column!r} must be non-negative seconds")
    return number


def load_diarization_rows(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        fail(f"diarization CSV not found: {path}")
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        fieldnames = set(reader.fieldnames or [])
        missing = REQUIRED_COLUMNS - fieldnames
        if missing:
            fail(
                "diarization CSV missing required column(s): "
                + ", ".join(sorted(missing))
            )
        rows: list[dict[str, Any]] = []
        for row_number, row in enumerate(reader, start=2):
            start = parse_float(row.get("start"), row_number=row_number, column="start")
            end = parse_float(row.get("end"), row_number=row_number, column="end")
            if end <= start:
                fail(f"row {row_number}: 'end' must be greater than 'start'")
            speaker = str(row.get("speaker", "")).strip()
            if not speaker:
                fail(f"row {row_number}: 'speaker' must be non-empty")
            rows.append({"start": start, "end": end, "speaker": speaker})
    if not rows:
        fail("diarization CSV has no data rows")
    rows.sort(key=lambda item: (item["start"], item["end"], item["speaker"]))
    return rows


def count_speaker_labels(transcript: dict[str, Any]) -> tuple[int, int]:
    segment_count = 0
    word_count = 0
    for segment in transcript.get("segments", []):
        if isinstance(segment, dict) and segment.get("speaker") is not None:
            segment_count += 1
        if isinstance(segment, dict):
            for word in segment.get("words", []) or []:
                if isinstance(word, dict) and word.get("speaker") is not None:
                    word_count += 1
    return segment_count, word_count


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    transcript_path = args.transcript_json
    diarization_path = args.diarization_csv
    output_path = args.output_json

    if output_path.exists():
        parser.error(f"--output-json already exists; choose a new path: {output_path}")
    try:
        if transcript_path.resolve() == output_path.resolve():
            parser.error("--output-json must be different from --transcript-json")
    except FileNotFoundError:
        # Path.resolve can fail on some platforms for missing parents. Parent
        # creation below will surface a clearer error if the path is invalid.
        pass

    try:
        transcript = load_transcript(transcript_path)
        rows = load_diarization_rows(diarization_path)

        try:
            import pandas as pd
            from whisperx.diarize import assign_word_speakers
        except Exception as exc:  # pragma: no cover - environment dependent
            fail(
                "could not import pandas/whisperx.diarize.assign_word_speakers; "
                "install WhisperX with its diarization dependencies before running this helper "
                f"({exc.__class__.__name__}: {exc})"
            )

        diarize_df = pd.DataFrame.from_records(rows, columns=["start", "end", "speaker"])
        before_segments, before_words = count_speaker_labels(transcript)
        updated = assign_word_speakers(
            diarize_df,
            transcript,
            fill_nearest=bool(args.fill_nearest),
        )
        after_segments, after_words = count_speaker_labels(updated)

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("w", encoding="utf-8") as handle:
            json.dump(updated, handle, ensure_ascii=False, indent=2)
            handle.write("\n")

        print(
            "assigned speaker labels: "
            f"segments {before_segments}->{after_segments}, "
            f"words {before_words}->{after_words}; "
            f"wrote {output_path}",
            file=sys.stderr,
        )
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
