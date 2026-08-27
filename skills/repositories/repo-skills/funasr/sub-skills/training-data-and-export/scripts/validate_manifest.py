#!/usr/bin/env python3
"""Validate FunASR training JSONL manifests and optionally write wav.scp/text.

Default validation targets the standard audio JSONL schema:
{"key", "source", "source_len", "target", "target_len"}.
Use --schema messages for conversational audio manifests.
"""

from __future__ import annotations

import argparse
import json
import sys
import wave
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple
from urllib.parse import urlparse


AUDIO_REQUIRED = ("key", "source", "target")
AUDIO_LENGTHS = ("source_len", "target_len")


def is_uri(value: str) -> bool:
    return urlparse(value).scheme in {"http", "https", "s3", "gs", "oss"}


def target_length(text: str, mode: str) -> int:
    if mode == "word":
        return len(text.split())
    if mode == "char":
        return len(text)
    return len(text.split()) if " " in text else len(text)


def wav_centisecond_length(path: Path) -> int:
    with wave.open(str(path), "rb") as wav:
        frames = wav.getnframes()
        rate = wav.getframerate()
    if rate <= 0:
        raise ValueError("WAV sample rate is not positive")
    return max(1, int(frames * 100 / rate))


def as_nonnegative_int(value: object) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value if value >= 0 else None
    if isinstance(value, str) and value.isdigit():
        return int(value)
    return None


def load_jsonl(path: Path) -> Tuple[List[Tuple[int, dict]], List[str]]:
    records: List[Tuple[int, dict]] = []
    errors: List[str] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_no, raw in enumerate(handle, 1):
            line = raw.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
            except json.JSONDecodeError as exc:
                errors.append(f"line {line_no}: invalid JSON: {exc}")
                continue
            if not isinstance(data, dict):
                errors.append(f"line {line_no}: JSONL record must be an object")
                continue
            records.append((line_no, data))
    return records, errors


def validate_audio_record(
    line_no: int,
    data: dict,
    args: argparse.Namespace,
    seen_keys: Dict[str, int],
    warnings: List[str],
) -> List[str]:
    errors: List[str] = []
    for field in AUDIO_REQUIRED:
        if field not in data:
            errors.append(f"line {line_no}: missing required field {field!r}")
    if errors:
        return errors

    key = data["key"]
    if not isinstance(key, str) or not key:
        errors.append(f"line {line_no}: key must be a non-empty string")
    elif key in seen_keys:
        errors.append(f"line {line_no}: duplicate key {key!r}; first seen on line {seen_keys[key]}")
    else:
        seen_keys[key] = line_no

    source = data["source"]
    target = data["target"]
    if not isinstance(source, str) or not source:
        errors.append(f"line {line_no}: source must be a non-empty string")
    if not isinstance(target, str):
        errors.append(f"line {line_no}: target must be a string")

    for field in AUDIO_LENGTHS:
        if field not in data:
            if not args.allow_missing_lengths:
                errors.append(f"line {line_no}: missing length field {field!r}")
            continue
        value = as_nonnegative_int(data[field])
        if value is None:
            errors.append(f"line {line_no}: {field} must be a non-negative integer")

    if isinstance(target, str) and "target_len" in data:
        expected = target_length(target, args.target_len_mode)
        observed = as_nonnegative_int(data["target_len"])
        if observed is not None and observed != expected:
            errors.append(
                f"line {line_no}: target_len={observed} but recomputed {expected} for key {key!r}"
            )

    if isinstance(source, str) and source:
        source_path = Path(source).expanduser()
        if args.check_sources:
            if is_uri(source):
                warnings.append(f"line {line_no}: source for key {key!r} is a URI; existence not checked")
            elif not source_path.exists():
                errors.append(f"line {line_no}: source path does not exist for key {key!r}: {source}")
        if args.check_source_len and not is_uri(source) and source_path.exists():
            try:
                expected_len = wav_centisecond_length(source_path)
                observed_len = as_nonnegative_int(data.get("source_len"))
                if observed_len is not None and abs(observed_len - expected_len) > args.source_len_tolerance:
                    errors.append(
                        f"line {line_no}: source_len={observed_len} but WAV duration gives "
                        f"{expected_len} for key {key!r}"
                    )
            except Exception as exc:  # noqa: BLE001 - report all audio probe failures clearly.
                message = f"line {line_no}: could not compute WAV duration for key {key!r}: {exc}"
                if args.strict_audio:
                    errors.append(message)
                else:
                    warnings.append(message)
    return errors


def validate_messages_record(line_no: int, data: dict, args: argparse.Namespace) -> List[str]:
    errors: List[str] = []
    messages = data.get("messages")
    if not isinstance(messages, list) or len(messages) < 2:
        errors.append(f"line {line_no}: messages must be a list with at least two turns")
        return errors
    for idx, turn in enumerate(messages):
        if not isinstance(turn, dict):
            errors.append(f"line {line_no}: messages[{idx}] must be an object")
            continue
        role = turn.get("role")
        content = turn.get("content")
        if role not in {"system", "user", "assistant"}:
            errors.append(f"line {line_no}: messages[{idx}].role has unexpected value {role!r}")
        if not isinstance(content, str) or not content:
            errors.append(f"line {line_no}: messages[{idx}].content must be a non-empty string")
    for field in ("speech_length", "text_length"):
        if field not in data:
            if not args.allow_missing_lengths:
                errors.append(f"line {line_no}: missing field {field!r}")
            continue
        value = as_nonnegative_int(data[field])
        if value is None or value < 1:
            errors.append(f"line {line_no}: {field} must be a positive integer")
    return errors


def choose_schema(data: dict, requested: str) -> str:
    if requested != "auto":
        return requested
    if "messages" in data and "source" not in data:
        return "messages"
    return "audio"


def write_reverse_scps(records: List[dict], args: argparse.Namespace) -> None:
    if not args.write_wav_scp and not args.write_text:
        return
    if args.write_wav_scp:
        wav_path = Path(args.write_wav_scp)
        wav_path.parent.mkdir(parents=True, exist_ok=True)
        with wav_path.open("w", encoding="utf-8") as wav_out:
            for record in records:
                wav_out.write(f"{record['key']}\t{record['source']}\n")
    if args.write_text:
        text_path = Path(args.write_text)
        text_path.parent.mkdir(parents=True, exist_ok=True)
        with text_path.open("w", encoding="utf-8") as text_out:
            for record in records:
                target = record["target"]
                if args.aishell_strip_spaces and "aishell" in str(record.get("source", "")):
                    target = target.replace(" ", "")
                text_out.write(f"{record['key']}\t{target}\n")


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate FunASR JSONL manifests.")
    parser.add_argument("manifest", help="JSONL manifest to validate.")
    parser.add_argument(
        "--schema",
        choices=("auto", "audio", "messages"),
        default="auto",
        help="Manifest schema. auto treats records with messages and no source as conversational.",
    )
    parser.add_argument(
        "--target-len-mode",
        choices=("auto", "word", "char"),
        default="auto",
        help="How to recompute target_len for audio records.",
    )
    parser.add_argument("--allow-missing-lengths", action="store_true", help="Warn less strictly about missing length fields.")
    parser.add_argument("--check-sources", action="store_true", help="Require local audio sources to exist; URI existence is not probed.")
    parser.add_argument("--check-source-len", action="store_true", help="Compare source_len with local WAV duration when possible.")
    parser.add_argument("--strict-audio", action="store_true", help="Fail if local audio duration cannot be read.")
    parser.add_argument("--source-len-tolerance", type=int, default=2, help="Allowed centisecond/frame tolerance; default: 2.")
    parser.add_argument("--max-errors", type=int, default=20, help="Maximum errors to print; default: 20.")
    parser.add_argument("--write-wav-scp", help="Optional wav.scp output, written only if validation succeeds.")
    parser.add_argument("--write-text", help="Optional text output, written only if validation succeeds.")
    parser.add_argument("--aishell-strip-spaces", action="store_true", help="When writing text, strip spaces if source contains 'aishell'.")
    parser.add_argument("--json-report", help="Optional path for a compact validation report JSON.")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    if args.source_len_tolerance < 0:
        print("--source-len-tolerance must be >= 0", file=sys.stderr)
        return 2

    records, errors = load_jsonl(Path(args.manifest))
    warnings: List[str] = []
    audio_records: List[dict] = []
    seen_keys: Dict[str, int] = {}
    schema_counts = {"audio": 0, "messages": 0}

    for line_no, data in records:
        schema = choose_schema(data, args.schema)
        schema_counts[schema] += 1
        if schema == "audio":
            rec_errors = validate_audio_record(line_no, data, args, seen_keys, warnings)
            if not rec_errors:
                audio_records.append(data)
            errors.extend(rec_errors)
        else:
            errors.extend(validate_messages_record(line_no, data, args))

    for warning in warnings:
        print(f"warning: {warning}", file=sys.stderr)

    if errors:
        for error in errors[: args.max_errors]:
            print(f"error: {error}", file=sys.stderr)
        if len(errors) > args.max_errors:
            print(f"error: ... and {len(errors) - args.max_errors} more", file=sys.stderr)
        status = "failed"
    else:
        status = "ok"
        write_reverse_scps(audio_records, args)

    report = {
        "status": status,
        "records": len(records),
        "schema_counts": schema_counts,
        "warnings": len(warnings),
        "errors": len(errors),
    }
    if args.json_report:
        report_path = Path(args.json_report)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, sort_keys=True), file=sys.stderr)
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
