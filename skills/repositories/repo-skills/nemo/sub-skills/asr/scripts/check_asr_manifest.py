#!/usr/bin/env python3
"""Validate NeMo ASR JSONL manifests without importing NeMo."""

from __future__ import annotations

import argparse
import json
import math
import statistics
import string
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Iterable

YES_NO_FIELDS = ("pnc", "itn", "timestamp", "diarize")
CANARY_BASE_FIELDS = ("source_lang", "target_lang")
CANARY_V1_FIELDS = ("task", "pnc")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate NeMo ASR JSONL manifest fields and summarize durations/transcript style.",
    )
    parser.add_argument("manifest", type=Path, help="Path to a JSONL manifest.")
    parser.add_argument(
        "--canary",
        action="store_true",
        help="Require Canary-style source_lang/target_lang fields and validate prompt-like fields when present.",
    )
    parser.add_argument(
        "--canary-v1",
        action="store_true",
        help="Require Canary v1 task and pnc fields in addition to source_lang/target_lang.",
    )
    parser.add_argument(
        "--allow-empty-text",
        action="store_true",
        help="Allow empty text fields, useful for inference-only manifests.",
    )
    parser.add_argument("--min-duration", type=float, default=None, help="Warn when duration is below this many seconds.")
    parser.add_argument("--max-duration", type=float, default=None, help="Warn when duration exceeds this many seconds.")
    parser.add_argument(
        "--warn-missing-audio",
        action="store_true",
        help="Warn when audio_filepath does not exist. Relative paths are resolved from the manifest directory.",
    )
    parser.add_argument(
        "--style-summary",
        action="store_true",
        help="Print transcript casing, punctuation, digit, whitespace, and language/task summaries.",
    )
    parser.add_argument(
        "--max-examples",
        type=int,
        default=5,
        help="Maximum example line numbers to show for each issue category. Default: 5.",
    )
    return parser.parse_args()


def add_issue(issues: dict[str, list[str]], key: str, line_no: int, message: str, limit: int) -> None:
    bucket = issues.setdefault(key, [])
    if len(bucket) < limit:
        bucket.append(f"line {line_no}: {message}")
    elif len(bucket) == limit:
        bucket.append("...")


def is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value))


def existing_audio_path(raw_path: str, manifest_dir: Path) -> Path:
    audio_path = Path(raw_path)
    if audio_path.is_absolute():
        return audio_path
    return manifest_dir / audio_path


def transcript_style(text: str) -> dict[str, bool]:
    letters = [char for char in text if char.isalpha()]
    punctuation_chars = [char for char in text if char in string.punctuation]
    return {
        "empty": text == "",
        "has_upper": any(char.isupper() for char in letters),
        "has_lower": any(char.islower() for char in letters),
        "has_punctuation": bool(punctuation_chars),
        "has_digits": any(char.isdigit() for char in text),
        "has_repeated_space": "  " in text,
        "has_edge_space": text != text.strip(),
    }


def percentile(sorted_values: list[float], pct: float) -> float:
    if not sorted_values:
        return float("nan")
    if len(sorted_values) == 1:
        return sorted_values[0]
    position = (len(sorted_values) - 1) * pct
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return sorted_values[int(position)]
    weight = position - lower
    return sorted_values[lower] * (1 - weight) + sorted_values[upper] * weight


def validate_record(
    record: Any,
    line_no: int,
    args: argparse.Namespace,
    manifest_dir: Path,
    issues: dict[str, list[str]],
) -> tuple[float | None, str | None, dict[str, Any] | None]:
    if not isinstance(record, dict):
        add_issue(issues, "not_object", line_no, "record is not a JSON object", args.max_examples)
        return None, None, None

    for field in ("audio_filepath", "text", "duration"):
        if field not in record:
            add_issue(issues, f"missing_{field}", line_no, f"missing required field {field!r}", args.max_examples)

    audio = record.get("audio_filepath")
    if audio is not None:
        if not isinstance(audio, str) or not audio.strip():
            add_issue(issues, "bad_audio_filepath", line_no, "audio_filepath must be a non-empty string", args.max_examples)
        elif args.warn_missing_audio and not existing_audio_path(audio, manifest_dir).exists():
            add_issue(issues, "missing_audio_file", line_no, f"audio file not found: {audio}", args.max_examples)

    text = record.get("text")
    if text is not None:
        if not isinstance(text, str):
            add_issue(issues, "bad_text", line_no, "text must be a string", args.max_examples)
            text = None
        elif text == "" and not args.allow_empty_text:
            add_issue(issues, "empty_text", line_no, "text is empty", args.max_examples)

    duration = record.get("duration")
    duration_value: float | None = None
    if duration is not None:
        if not is_number(duration):
            add_issue(issues, "bad_duration", line_no, "duration must be a finite number", args.max_examples)
        else:
            duration_value = float(duration)
            if duration_value <= 0:
                add_issue(issues, "nonpositive_duration", line_no, "duration must be positive", args.max_examples)
            if args.min_duration is not None and duration_value < args.min_duration:
                add_issue(
                    issues,
                    "below_min_duration",
                    line_no,
                    f"duration {duration_value:g} < min {args.min_duration:g}",
                    args.max_examples,
                )
            if args.max_duration is not None and duration_value > args.max_duration:
                add_issue(
                    issues,
                    "above_max_duration",
                    line_no,
                    f"duration {duration_value:g} > max {args.max_duration:g}",
                    args.max_examples,
                )

    require_canary = args.canary or args.canary_v1
    if require_canary:
        for field in CANARY_BASE_FIELDS:
            if field not in record:
                add_issue(issues, f"missing_{field}", line_no, f"missing Canary field {field!r}", args.max_examples)
            elif not isinstance(record[field], str) or not record[field].strip():
                add_issue(issues, f"bad_{field}", line_no, f"{field} must be a non-empty string", args.max_examples)

    if args.canary_v1:
        for field in CANARY_V1_FIELDS:
            if field not in record:
                add_issue(issues, f"missing_{field}", line_no, f"missing Canary v1 field {field!r}", args.max_examples)

    task = record.get("task")
    if task is not None and task not in {"asr", "ast", "transcribe", "translate", "s2t_translation"}:
        add_issue(issues, "unusual_task", line_no, f"unusual task value {task!r}", args.max_examples)

    for field in YES_NO_FIELDS:
        value = record.get(field)
        if value is not None and value not in {"yes", "no", True, False}:
            add_issue(issues, f"bad_{field}", line_no, f"{field} should usually be yes/no", args.max_examples)

    if require_canary:
        source_lang = record.get("source_lang")
        target_lang = record.get("target_lang")
        task_value = record.get("task")
        if task_value in {"asr", "transcribe"} and source_lang and target_lang and source_lang != target_lang:
            add_issue(
                issues,
                "asr_language_mismatch",
                line_no,
                f"ASR task has source_lang={source_lang!r} target_lang={target_lang!r}",
                args.max_examples,
            )

    style = transcript_style(text) if isinstance(text, str) else None
    return duration_value, text, {"record": record, "style": style}


def print_counter(title: str, counter: Counter[Any], limit: int = 12) -> None:
    if not counter:
        return
    print(f"{title}:")
    for key, count in counter.most_common(limit):
        print(f"  {key!r}: {count}")
    if len(counter) > limit:
        print(f"  ... {len(counter) - limit} more")


def summarize(records: Iterable[dict[str, Any]], durations: list[float], texts: list[str], args: argparse.Namespace) -> None:
    print(f"Records: {len(texts)}")
    if durations:
        sorted_durations = sorted(durations)
        print(
            "Durations seconds: "
            f"min={sorted_durations[0]:.3f} "
            f"p50={percentile(sorted_durations, 0.50):.3f} "
            f"p95={percentile(sorted_durations, 0.95):.3f} "
            f"max={sorted_durations[-1]:.3f} "
            f"mean={statistics.fmean(sorted_durations):.3f} "
            f"total={sum(sorted_durations):.3f}"
        )

    if not args.style_summary:
        return

    style_counts = Counter()
    source_langs: Counter[str] = Counter()
    target_langs: Counter[str] = Counter()
    tasks: Counter[str] = Counter()
    pnc_values: Counter[str] = Counter()
    text_lengths: list[int] = []

    for item in records:
        record = item["record"]
        style = item["style"]
        if style:
            for key, value in style.items():
                if value:
                    style_counts[key] += 1
        text = record.get("text")
        if isinstance(text, str):
            text_lengths.append(len(text))
        for field, counter in (
            ("source_lang", source_langs),
            ("target_lang", target_langs),
            ("task", tasks),
            ("pnc", pnc_values),
        ):
            value = record.get(field)
            if value is not None:
                counter[str(value)] += 1

    if text_lengths:
        print(
            "Transcript chars: "
            f"min={min(text_lengths)} p50={percentile(sorted(text_lengths), 0.50):.1f} "
            f"max={max(text_lengths)} mean={statistics.fmean(text_lengths):.1f}"
        )
    print_counter("Transcript style flags", style_counts)
    print_counter("source_lang", source_langs)
    print_counter("target_lang", target_langs)
    print_counter("task", tasks)
    print_counter("pnc", pnc_values)


def main() -> int:
    args = parse_args()
    issues: dict[str, list[str]] = {}
    durations: list[float] = []
    texts: list[str] = []
    valid_records: list[dict[str, Any]] = []

    if args.min_duration is not None and args.min_duration < 0:
        print("--min-duration must be non-negative", file=sys.stderr)
        return 2
    if args.max_duration is not None and args.max_duration <= 0:
        print("--max-duration must be positive", file=sys.stderr)
        return 2
    if (
        args.min_duration is not None
        and args.max_duration is not None
        and args.min_duration > args.max_duration
    ):
        print("--min-duration cannot exceed --max-duration", file=sys.stderr)
        return 2
    if args.max_examples < 0:
        print("--max-examples must be non-negative", file=sys.stderr)
        return 2

    manifest = args.manifest
    if not manifest.exists():
        print(f"Manifest not found: {manifest}", file=sys.stderr)
        return 2
    if not manifest.is_file():
        print(f"Manifest is not a file: {manifest}", file=sys.stderr)
        return 2

    manifest_dir = manifest.resolve().parent
    total_lines = 0
    blank_lines = 0

    try:
        with manifest.open("r", encoding="utf-8") as stream:
            for line_no, line in enumerate(stream, start=1):
                total_lines += 1
                stripped = line.strip()
                if not stripped:
                    blank_lines += 1
                    add_issue(issues, "blank_line", line_no, "blank line", args.max_examples)
                    continue
                try:
                    record = json.loads(stripped)
                except json.JSONDecodeError as error:
                    add_issue(issues, "json_decode", line_no, error.msg, args.max_examples)
                    continue
                duration, text, valid = validate_record(record, line_no, args, manifest_dir, issues)
                if duration is not None and duration > 0:
                    durations.append(duration)
                if isinstance(text, str):
                    texts.append(text)
                if valid is not None:
                    valid_records.append(valid)
    except OSError as error:
        print(f"Could not read manifest: {error}", file=sys.stderr)
        return 2

    print(f"Manifest: {manifest}")
    print(f"Lines: {total_lines} (blank: {blank_lines})")
    summarize(valid_records, durations, texts, args)

    if issues:
        print("Issues:")
        for key in sorted(issues):
            print(f"  {key}: {len([item for item in issues[key] if item != '...'])}")
            for item in issues[key]:
                print(f"    {item}")
        return 1

    print("OK: manifest passed validation checks")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
