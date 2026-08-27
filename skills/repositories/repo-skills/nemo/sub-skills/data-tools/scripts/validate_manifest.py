#!/usr/bin/env python3
"""Validate NeMo-style JSONL manifests without importing NeMo.

The checker is safe by default: it parses JSONL and validates metadata only.
It never opens audio contents, downloads remote files, starts services, trains,
or writes output files. Local file existence checks are opt-in with --check-files.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

REMOTE_PREFIXES = (
    "s3://",
    "ais://",
    "gs://",
    "http://",
    "https://",
    "ftp://",
    "pipe:",
)
DEFAULT_TEXT_KEYS = ("text", "normalized_text", "pred_text", "prompt", "completion")


class IssueTracker:
    def __init__(self, max_examples: int) -> None:
        self.max_examples = max_examples
        self.counts: Counter[str] = Counter()
        self.examples: dict[str, list[str]] = defaultdict(list)

    def add(self, kind: str, line_no: int, message: str) -> None:
        self.counts[kind] += 1
        if len(self.examples[kind]) < self.max_examples:
            self.examples[kind].append(f"line {line_no}: {message}")

    @property
    def total(self) -> int:
        return sum(self.counts.values())

    def print_report(self) -> None:
        if not self.counts:
            print("No validation errors found.")
            return
        print("Validation errors:")
        for kind, count in sorted(self.counts.items()):
            print(f"- {kind}: {count}")
            for example in self.examples[kind]:
                print(f"  - {example}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate NeMo-style JSONL manifests without NeMo imports or audio reads.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("manifest", type=Path, help="Path to a JSONL manifest file.")
    parser.add_argument(
        "--required",
        nargs="+",
        default=["audio_filepath", "duration"],
        help="Required keys for every non-skipped entry. Use text for ASR/TTS transcript manifests and shard_id for tarred manifests.",
    )
    parser.add_argument(
        "--text-keys",
        nargs="+",
        default=list(DEFAULT_TEXT_KEYS),
        help="Text-like keys to summarize and check for mixed transcript conventions.",
    )
    parser.add_argument("--min-duration", type=float, default=None, help="Minimum allowed duration in seconds.")
    parser.add_argument("--max-duration", type=float, default=None, help="Maximum allowed duration in seconds.")
    parser.add_argument(
        "--allow-missing-duration",
        action="store_true",
        help="Do not report missing duration as an error unless duration is explicitly listed in --required.",
    )
    parser.add_argument(
        "--check-files",
        action="store_true",
        help="Check existence of local audio_filepath values. Avoid for tar member names, remote URIs, and huge manifests unless intended.",
    )
    parser.add_argument(
        "--base-dir",
        type=Path,
        default=None,
        help="Base directory for relative local audio paths when --check-files is enabled. Defaults to the manifest directory.",
    )
    parser.add_argument(
        "--tarred",
        action="store_true",
        help="Expect tarred-manifest semantics: require shard_id by default and do not treat duplicate audio filenames as suspicious.",
    )
    parser.add_argument(
        "--sample-limit",
        type=int,
        default=0,
        help="Validate only the first N lines. 0 means all lines.",
    )
    parser.add_argument(
        "--max-examples",
        type=int,
        default=5,
        help="Maximum example messages to print for each issue type.",
    )
    parser.add_argument("--summary", action="store_true", help="Print duration, field, transcript, and blend-hint summaries.")
    return parser.parse_args()


def is_truthy_skip(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    if isinstance(value, str):
        return value.strip().lower() not in {"", "0", "false", "none", "no"}
    return bool(value)


def is_remote_or_pipe(path: str) -> bool:
    return path.startswith(REMOTE_PREFIXES) or "://" in path


def resolve_audio_path(audio_path: str, base_dir: Path) -> Path | None:
    if is_remote_or_pipe(audio_path):
        return None
    candidate = Path(audio_path)
    if candidate.is_absolute():
        return candidate
    return base_dir / candidate


def parse_duration(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    try:
        duration = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(duration):
        return None
    return duration


def percentile(sorted_values: list[float], fraction: float) -> float | None:
    if not sorted_values:
        return None
    index = min(len(sorted_values) - 1, max(0, round((len(sorted_values) - 1) * fraction)))
    return sorted_values[index]


def format_seconds(value: float | None) -> str:
    if value is None:
        return "n/a"
    return f"{value:.3f}s"


def summarize_durations(durations: list[float]) -> None:
    if not durations:
        print("Durations: none found")
        return
    values = sorted(durations)
    total = sum(values)
    print(
        "Durations: "
        f"count={len(values)}, total_hours={total / 3600:.3f}, "
        f"min={format_seconds(values[0])}, p50={format_seconds(percentile(values, 0.5))}, "
        f"p95={format_seconds(percentile(values, 0.95))}, max={format_seconds(values[-1])}"
    )


def summarize_counter(title: str, counter: Counter[Any], limit: int = 10) -> None:
    if not counter:
        print(f"{title}: none")
        return
    parts = [f"{key}={count}" for key, count in counter.most_common(limit)]
    more = "" if len(counter) <= limit else f", ... (+{len(counter) - limit} more)"
    print(f"{title}: " + ", ".join(parts) + more)


def validate_manifest(args: argparse.Namespace) -> int:
    manifest_path = args.manifest
    if not manifest_path.is_file():
        print(f"ERROR: manifest does not exist or is not a file: {manifest_path}", file=sys.stderr)
        return 2

    required = set(args.required)
    if args.tarred:
        required.add("shard_id")
    if args.allow_missing_duration and "duration" not in required:
        required.discard("duration")

    base_dir = args.base_dir if args.base_dir is not None else manifest_path.parent
    issues = IssueTracker(max_examples=max(args.max_examples, 0))

    total_lines = 0
    parsed_entries = 0
    skipped_entries = 0
    durations: list[float] = []
    keys_seen: Counter[str] = Counter()
    text_key_presence: Counter[str] = Counter()
    empty_text_values: Counter[str] = Counter()
    audio_paths: Counter[str] = Counter()
    duplicate_offsets: dict[str, set[Any]] = defaultdict(set)
    shard_ids: Counter[Any] = Counter()
    weights: list[float] = []
    tag_keys: Counter[str] = Counter()
    local_checks = 0
    remote_or_unchecked = 0

    try:
        with manifest_path.open("r", encoding="utf-8") as stream:
            for line_no, raw_line in enumerate(stream, start=1):
                if args.sample_limit and line_no > args.sample_limit:
                    break
                total_lines += 1
                line = raw_line.strip()
                if not line:
                    issues.add("blank-line", line_no, "blank lines are not valid JSONL entries")
                    continue
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError as exc:
                    issues.add("json", line_no, f"invalid JSON: {exc.msg}")
                    continue
                if not isinstance(entry, dict):
                    issues.add("json", line_no, f"expected object, got {type(entry).__name__}")
                    continue

                parsed_entries += 1
                keys_seen.update(entry.keys())

                if is_truthy_skip(entry.get("_skipme", False)):
                    skipped_entries += 1
                    continue

                missing = sorted(key for key in required if key not in entry)
                if missing:
                    issues.add("missing-key", line_no, "missing required key(s): " + ", ".join(missing))

                if "duration" in entry:
                    duration = parse_duration(entry.get("duration"))
                    if duration is None:
                        issues.add("duration", line_no, f"duration is not a finite number: {entry.get('duration')!r}")
                    else:
                        durations.append(duration)
                        if duration < 0:
                            issues.add("duration", line_no, f"duration is negative: {duration}")
                        if args.min_duration is not None and duration < args.min_duration:
                            issues.add("duration-too-short", line_no, f"{duration} < {args.min_duration}")
                        if args.max_duration is not None and duration > args.max_duration:
                            issues.add("duration-too-long", line_no, f"{duration} > {args.max_duration}")
                elif not args.allow_missing_duration and "duration" in required:
                    issues.add("duration", line_no, "duration is required but missing")

                audio_value = entry.get("audio_filepath")
                if audio_value is not None:
                    if not isinstance(audio_value, str) or not audio_value:
                        issues.add("audio-path", line_no, f"audio_filepath should be a non-empty string, got {audio_value!r}")
                    else:
                        audio_paths[audio_value] += 1
                        duplicate_offsets[audio_value].add(entry.get("offset"))
                        if args.check_files:
                            resolved = resolve_audio_path(audio_value, base_dir)
                            if resolved is None:
                                remote_or_unchecked += 1
                            else:
                                local_checks += 1
                                if not resolved.exists():
                                    issues.add("missing-file", line_no, f"local audio path not found: {resolved}")

                if "shard_id" in entry:
                    shard_id = entry["shard_id"]
                    shard_ids[shard_id] += 1
                    if isinstance(shard_id, bool) or not isinstance(shard_id, int) or shard_id < 0:
                        issues.add("shard-id", line_no, f"shard_id should be a non-negative integer, got {shard_id!r}")

                if "weight" in entry:
                    weight = parse_duration(entry.get("weight"))
                    if weight is None or weight <= 0:
                        issues.add("weight", line_no, f"weight should be positive, got {entry.get('weight')!r}")
                    else:
                        weights.append(weight)

                tags = entry.get("tags")
                if tags is not None:
                    if not isinstance(tags, dict):
                        issues.add("tags", line_no, f"tags should be an object, got {type(tags).__name__}")
                    else:
                        tag_keys.update(tags.keys())

                present_text_keys = [key for key in args.text_keys if key in entry]
                text_key_presence.update(present_text_keys)
                for key in present_text_keys:
                    value = entry.get(key)
                    if value is None or value == "":
                        empty_text_values[key] += 1
                    elif not isinstance(value, str):
                        issues.add("text", line_no, f"{key} should be a string when present, got {type(value).__name__}")

                if "text" in required and "text" not in entry and present_text_keys:
                    issues.add(
                        "text-key-mismatch",
                        line_no,
                        "required text is missing but found alternative text-like key(s): " + ", ".join(present_text_keys),
                    )
    except OSError as exc:
        print(f"ERROR: failed to read manifest: {exc}", file=sys.stderr)
        return 2

    if parsed_entries == 0:
        issues.add("empty-manifest", 0, "no valid JSON objects found")

    if not args.tarred:
        duplicate_audio = [(path, count) for path, count in audio_paths.items() if count > 1]
        for path, count in duplicate_audio[: args.max_examples]:
            offsets = duplicate_offsets[path]
            if len(offsets) <= 1:
                issues.add("duplicate-audio", 0, f"{path!r} appears {count} times without distinct offsets")

    print(f"Manifest: {manifest_path}")
    print(f"Lines checked: {total_lines}; parsed objects: {parsed_entries}; skipped by _skipme: {skipped_entries}")
    issues.print_report()

    if args.summary:
        print("\nSummary:")
        summarize_durations(durations)
        summarize_counter("Top-level keys", keys_seen)
        summarize_counter("Text-like keys", text_key_presence)
        summarize_counter("Empty text-like values", empty_text_values)
        summarize_counter("Shard IDs", shard_ids)
        summarize_counter("Tag keys", tag_keys)
        if audio_paths:
            duplicate_count = sum(1 for count in audio_paths.values() if count > 1)
            print(f"Audio paths: unique={len(audio_paths)}, duplicate_path_values={duplicate_count}")
        if weights:
            print(f"Weights: count={len(weights)}, sum={sum(weights):.6g}, min={min(weights):.6g}, max={max(weights):.6g}")
        if args.check_files:
            print(f"File checks: local_checked={local_checks}, remote_or_skipped={remote_or_unchecked}")
        if text_key_presence and len(text_key_presence) > 1:
            print("Hint: multiple text-like fields are present; set the consuming tool's text_field explicitly.")
        if weights and abs(sum(weights) - 1.0) > 1e-6:
            print("Hint: weights do not sum to 1.0; NeMo/Lhotse can normalize positive weights, but verify intent.")
        if args.tarred and not shard_ids:
            print("Hint: tarred manifests should include shard_id values matching tar shard patterns.")

    return 1 if issues.total else 0


def main() -> None:
    args = parse_args()
    raise SystemExit(validate_manifest(args))


if __name__ == "__main__":
    main()
