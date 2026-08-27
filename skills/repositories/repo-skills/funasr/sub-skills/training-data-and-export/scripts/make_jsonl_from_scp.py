#!/usr/bin/env python3
"""Create a FunASR standard audio-training JSONL manifest from wav.scp + text.

The output schema matches FunASR's public audio JSONL convention:
{"key", "source", "source_len", "target", "target_len", ...}.
This helper is intentionally stricter than the public converter so tiny fixture
problems fail before a long training run starts.
"""

from __future__ import annotations

import argparse
import json
import sys
import wave
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple
from urllib.parse import urlparse


Entry = Tuple[str, str, int]


def is_uri(value: str) -> bool:
    return urlparse(value).scheme in {"http", "https", "s3", "gs", "oss"}


def read_key_value_file(path: Path, label: str) -> Tuple[List[Entry], List[str]]:
    entries: List[Entry] = []
    errors: List[str] = []
    seen: Dict[str, int] = {}
    with path.open("r", encoding="utf-8") as handle:
        for line_no, raw in enumerate(handle, 1):
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split(maxsplit=1)
            if len(parts) != 2:
                errors.append(f"{label}:{line_no}: expected '<key> <value>', got {raw.rstrip()!r}")
                continue
            key, value = parts[0], parts[1].strip()
            if key in seen:
                errors.append(
                    f"{label}:{line_no}: duplicate key {key!r}; first seen on line {seen[key]}"
                )
                continue
            seen[key] = line_no
            entries.append((key, value, line_no))
    return entries, errors


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


def source_length(
    source: str,
    *,
    no_check_sources: bool,
    strict_source_len: bool,
    fallback_source_len: int,
    warnings: List[str],
    errors: List[str],
    key: str,
) -> int:
    if no_check_sources:
        return fallback_source_len

    if is_uri(source):
        warnings.append(
            f"{key}: source is a URI; keeping it but using fallback source_len={fallback_source_len}"
        )
        return fallback_source_len

    source_path = Path(source).expanduser()
    if not source_path.exists():
        errors.append(f"{key}: local source does not exist: {source}")
        return fallback_source_len

    try:
        return wav_centisecond_length(source_path)
    except Exception as exc:  # noqa: BLE001 - report any tiny-fixture read failure clearly.
        message = f"{key}: could not compute WAV duration for {source}: {exc}"
        if strict_source_len:
            errors.append(message)
        else:
            warnings.append(f"{message}; using fallback source_len={fallback_source_len}")
        return fallback_source_len


def build_records(args: argparse.Namespace) -> Tuple[List[dict], List[str], List[str]]:
    wav_entries, wav_errors = read_key_value_file(Path(args.wav_scp), "wav-scp")
    text_entries, text_errors = read_key_value_file(Path(args.text), "text")
    errors = wav_errors + text_errors
    warnings: List[str] = []

    wav_by_key = {key: (value, line_no) for key, value, line_no in wav_entries}
    text_by_key = {key: (value, line_no) for key, value, line_no in text_entries}

    wav_keys = set(wav_by_key)
    text_keys = set(text_by_key)
    only_wav = sorted(wav_keys - text_keys)
    only_text = sorted(text_keys - wav_keys)
    if (only_wav or only_text) and not args.allow_mismatched_keys:
        if only_wav:
            errors.append(f"keys present only in wav-scp: {', '.join(only_wav[:10])}")
        if only_text:
            errors.append(f"keys present only in text: {', '.join(only_text[:10])}")
    selected_keys = [key for key, _, _ in wav_entries if key in text_by_key]

    if errors:
        return [], warnings, errors

    records: List[dict] = []
    for key in selected_keys:
        source, _source_line = wav_by_key[key]
        target, _target_line = text_by_key[key]
        local_errors: List[str] = []
        src_len = source_length(
            source,
            no_check_sources=args.no_check_sources,
            strict_source_len=args.strict_source_len,
            fallback_source_len=args.fallback_source_len,
            warnings=warnings,
            errors=local_errors,
            key=key,
        )
        if local_errors:
            errors.extend(local_errors)
            continue
        record = {
            "key": key,
            args.source_field: source,
            f"{args.source_field}_len": src_len,
            args.target_field: target,
            f"{args.target_field}_len": target_length(target, args.target_len_mode),
        }
        if args.prompt is not None:
            record["prompt"] = args.prompt
        records.append(record)

    return records, warnings, errors


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create a FunASR JSONL manifest from aligned wav.scp and text files."
    )
    parser.add_argument("--wav-scp", required=True, help="Input wav.scp: '<key> <audio-path-or-uri>'.")
    parser.add_argument("--text", required=True, help="Input text file: '<key> <transcript>'.")
    parser.add_argument("--output", required=True, help="Output JSONL path.")
    parser.add_argument("--source-field", default="source", help="Audio field name; default: source.")
    parser.add_argument("--target-field", default="target", help="Text field name; default: target.")
    parser.add_argument(
        "--target-len-mode",
        choices=("auto", "word", "char"),
        default="auto",
        help="How to compute target_len; auto matches FunASR's public converter.",
    )
    parser.add_argument("--prompt", default=None, help="Optional prompt field to add to every record.")
    parser.add_argument(
        "--fallback-source-len",
        type=int,
        default=1,
        help="source_len used for URI/non-WAV sources when duration is not checked; default: 1.",
    )
    parser.add_argument(
        "--no-check-sources",
        action="store_true",
        help="Do not require local source files to exist and do not compute WAV duration.",
    )
    parser.add_argument(
        "--strict-source-len",
        action="store_true",
        help="Fail if a local source exists but WAV duration cannot be computed.",
    )
    parser.add_argument(
        "--allow-mismatched-keys",
        action="store_true",
        help="Use only the key intersection instead of failing on wav/text key-set differences.",
    )
    parser.add_argument("--dry-run", action="store_true", help="Validate and report without writing JSONL.")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    if args.fallback_source_len < 1:
        print("--fallback-source-len must be >= 1", file=sys.stderr)
        return 2

    records, warnings, errors = build_records(args)
    for warning in warnings:
        print(f"warning: {warning}", file=sys.stderr)
    if errors:
        for error in errors:
            print(f"error: {error}", file=sys.stderr)
        print("no JSONL written", file=sys.stderr)
        return 1

    if args.dry_run:
        print(f"dry run ok: {len(records)} records", file=sys.stderr)
        return 0

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
    print(f"wrote {len(records)} records to {output_path}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
