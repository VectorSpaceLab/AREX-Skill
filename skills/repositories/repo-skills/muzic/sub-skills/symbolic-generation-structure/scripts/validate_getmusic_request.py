#!/usr/bin/env python3
"""Validate GETMusic track-generation and position-infilling requests.

This helper does not import the Muzic source tree. It only checks the
user-provided prompt grammar and optional MIDI path layout.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Sequence, Tuple

TRACK_LETTERS = {
    "l": "lead",
    "b": "bass",
    "d": "drum",
    "g": "guitar",
    "p": "piano",
    "s": "string",
    "c": "chord",
}
CONTENT_LETTERS = {k: v for k, v in TRACK_LETTERS.items() if k != "c"}
POSITION_TRACKS = {
    0: "lead",
    1: "bass",
    2: "drum",
    3: "guitar",
    4: "piano",
    5: "string",
    6: "chord",
}


@dataclass
class ValidationResult:
    mode: str
    ok: bool
    errors: List[str]
    warnings: List[str]
    summary: Dict[str, object]


def _unique_letters(text: str, allowed: Dict[str, str]) -> Tuple[List[str], List[str]]:
    seen: List[str] = []
    invalid: List[str] = []
    for ch in text.lower():
        if ch.isspace():
            continue
        if ch in allowed:
            if ch not in seen:
                seen.append(ch)
        else:
            invalid.append(ch)
    return seen, invalid


def _validate_midi_path(path: Optional[str]) -> List[str]:
    warnings: List[str] = []
    if not path:
        return warnings
    if not os.path.exists(path):
        warnings.append(f"input MIDI path does not exist: {path}")
    elif not path.lower().endswith((".mid", ".midi")):
        warnings.append(f"input path does not look like a MIDI file: {path}")
    return warnings


def _intervals_overlap(a_start: int, a_end: Optional[int], b_start: int, b_end: Optional[int]) -> bool:
    a_stop = float("inf") if a_end is None else a_end
    b_stop = float("inf") if b_end is None else b_end
    return not (a_stop <= b_start or b_stop <= a_start)


def _parse_position_command(raw: str) -> Tuple[List[Tuple[int, int, Optional[int]]], List[str]]:
    errors: List[str] = []
    if raw == "-":
        return [], errors

    segments: List[Tuple[int, int, Optional[int]]] = []
    for chunk in [part.strip() for part in raw.split(";") if part.strip()]:
        parts = chunk.split(",")
        if len(parts) != 3:
            errors.append(f"segment must have exactly 3 comma-separated fields: {chunk!r}")
            continue
        track_s, start_s, end_s = parts
        if not track_s.isdigit():
            errors.append(f"track id must be an integer: {chunk!r}")
            continue
        track_id = int(track_s)
        if track_id not in POSITION_TRACKS:
            errors.append(f"track id out of range 0..6: {track_id}")
            continue
        if not start_s.isdigit():
            errors.append(f"start position must be a non-negative integer: {chunk!r}")
            continue
        start = int(start_s)
        if end_s == "":
            end = None
        elif end_s.isdigit():
            end = int(end_s)
            if end <= start:
                errors.append(f"end must be greater than start for finite spans: {chunk!r}")
                continue
        else:
            errors.append(f"end position must be empty or a non-negative integer: {chunk!r}")
            continue
        segments.append((track_id, start, end))
    return segments, errors


def validate_track_request(condition: str, content: str, input_midi: Optional[str]) -> ValidationResult:
    errors: List[str] = []
    warnings: List[str] = []

    condition_letters, condition_invalid = _unique_letters(condition, TRACK_LETTERS)
    content_letters, content_invalid = _unique_letters(content, CONTENT_LETTERS)

    if condition_invalid:
        errors.append(f"invalid condition letters: {''.join(condition_invalid)}")
    if content_invalid:
        errors.append(f"invalid content letters: {''.join(content_invalid)}")

    if not content_letters:
        errors.append("at least one content track must be selected")

    if "c" in content.lower():
        errors.append("content tracks do not accept chord guidance; use chord only as conditioning guidance")

    condition_names = [TRACK_LETTERS[ch] for ch in condition_letters]
    content_names = [CONTENT_LETTERS[ch] for ch in content_letters]

    overlap = sorted(set(condition_letters) & set(content_letters))
    if overlap:
        warnings.append(
            "condition/content overlap on: " + ", ".join(TRACK_LETTERS[ch] for ch in overlap)
        )

    if set(condition_letters) >= set("lbdgps"):
        warnings.append("all six musical tracks are conditioned; GETMusic may fall back to an unconditional branch")

    warnings.extend(_validate_midi_path(input_midi))

    ok = not errors
    return ValidationResult(
        mode="track",
        ok=ok,
        errors=errors,
        warnings=warnings,
        summary={
            "condition_letters": condition_letters,
            "condition_tracks": condition_names,
            "content_letters": content_letters,
            "content_tracks": content_names,
            "input_midi": input_midi,
        },
    )


def validate_position_request(condition: str, empty: str, input_midi: Optional[str]) -> ValidationResult:
    errors: List[str] = []
    warnings: List[str] = []

    condition_segments, condition_errors = _parse_position_command(condition)
    empty_segments, empty_errors = _parse_position_command(empty)
    errors.extend(condition_errors)
    errors.extend(empty_errors)

    for label, segments in (("condition", condition_segments), ("empty", empty_segments)):
        by_track: Dict[int, List[Tuple[int, Optional[int]]]] = {}
        for track_id, start, end in segments:
            by_track.setdefault(track_id, []).append((start, end))
        for track_id, spans in by_track.items():
            for idx, (start_a, end_a) in enumerate(spans):
                for start_b, end_b in spans[idx + 1 :]:
                    if _intervals_overlap(start_a, end_a, start_b, end_b):
                        warnings.append(
                            f"{label} spans overlap on track {track_id} ({POSITION_TRACKS[track_id]})"
                        )
                        break

    for c_track, c_start, c_end in condition_segments:
        for e_track, e_start, e_end in empty_segments:
            if c_track == e_track and _intervals_overlap(c_start, c_end, e_start, e_end):
                warnings.append(
                    f"condition and empty overlap on track {c_track} ({POSITION_TRACKS[c_track]})"
                )
                break

    warnings.extend(_validate_midi_path(input_midi))

    ok = not errors
    return ValidationResult(
        mode="position",
        ok=ok,
        errors=errors,
        warnings=warnings,
        summary={
            "condition_segments": [
                {"track_id": t, "track": POSITION_TRACKS[t], "start": s, "end": e}
                for t, s, e in condition_segments
            ],
            "empty_segments": [
                {"track_id": t, "track": POSITION_TRACKS[t], "start": s, "end": e}
                for t, s, e in empty_segments
            ],
            "input_midi": input_midi,
        },
    )


def _print_result(result: ValidationResult, as_json: bool) -> int:
    payload = asdict(result)
    if as_json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(f"mode: {result.mode}")
        print(f"ok: {result.ok}")
        if result.summary:
            print("summary:")
            for key, value in result.summary.items():
                print(f"  {key}: {value}")
        if result.warnings:
            print("warnings:")
            for item in result.warnings:
                print(f"  - {item}")
        if result.errors:
            print("errors:")
            for item in result.errors:
                print(f"  - {item}")
    return 0 if result.ok else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate GETMusic track-generation and position-infilling prompts.",
    )
    subparsers = parser.add_subparsers(dest="mode", required=True)

    track = subparsers.add_parser("track", help="validate a track-generation request")
    track.add_argument("--condition", default="", help="condition-track letters, e.g. lc")
    track.add_argument("--content", required=True, help="content-track letters, e.g. dgp")
    track.add_argument("--input-midi", default=None, help="optional MIDI file to inspect")
    track.add_argument("--json", action="store_true", help="print JSON output")

    position = subparsers.add_parser("position", help="validate a position-infilling request")
    position.add_argument("--condition", default="-", help="condition position command")
    position.add_argument("--empty", default="-", help="empty position command")
    position.add_argument("--input-midi", default=None, help="optional MIDI file to inspect")
    position.add_argument("--json", action="store_true", help="print JSON output")

    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.mode == "track":
        result = validate_track_request(args.condition, args.content, args.input_midi)
        return _print_result(result, args.json)
    if args.mode == "position":
        result = validate_position_request(args.condition, args.empty, args.input_midi)
        return _print_result(result, args.json)

    parser.error("unknown mode")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
