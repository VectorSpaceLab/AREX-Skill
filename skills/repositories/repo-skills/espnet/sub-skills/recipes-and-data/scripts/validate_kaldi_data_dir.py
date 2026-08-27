#!/usr/bin/env python3
"""Validate core Kaldi-style ESPnet data directory structure."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from typing import Any


def read_pairs(path: Path, min_fields: int = 2) -> tuple[dict[str, list[str]], list[str]]:
    data: dict[str, list[str]] = {}
    errors: list[str] = []
    if not path.exists():
        return data, [f"missing {path.name}"]
    for line_no, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not raw.strip():
            continue
        parts = raw.split()
        if len(parts) < min_fields:
            errors.append(f"{path.name}:{line_no}: expected at least {min_fields} fields")
            continue
        if parts[0] in data:
            errors.append(f"{path.name}:{line_no}: duplicate key {parts[0]}")
        data[parts[0]] = parts[1:]
    return data, errors


def validate(data_dir: Path, require_text: bool = True) -> dict[str, Any]:
    errors: list[str] = []
    text: dict[str, list[str]] = {}
    if require_text:
        text, new_errors = read_pairs(data_dir / "text")
        errors.extend(new_errors)
    wav, new_errors = read_pairs(data_dir / "wav.scp")
    errors.extend(new_errors)
    utt2spk, new_errors = read_pairs(data_dir / "utt2spk")
    errors.extend(new_errors)
    spk2utt, new_errors = read_pairs(data_dir / "spk2utt")
    errors.extend(new_errors)
    segments: dict[str, list[str]] = {}
    if (data_dir / "segments").exists():
        segments, new_errors = read_pairs(data_dir / "segments", 4)
        errors.extend(new_errors)
        for utt, values in segments.items():
            rec, start, end = values[0], values[1], values[2]
            if rec not in wav:
                errors.append(f"segments: recording {rec} for utterance {utt} not in wav.scp")
            try:
                if float(end) <= float(start):
                    errors.append(f"segments: utterance {utt} has end <= start")
            except ValueError:
                errors.append(f"segments: utterance {utt} has nonnumeric times")
    utterance_keys = set(segments) if segments else set(wav)
    if require_text:
        for key in sorted(set(text) - set(utt2spk)):
            errors.append(f"text key {key} missing from utt2spk")
        for key in sorted(set(text) - utterance_keys):
            errors.append(f"text key {key} missing from {'segments' if segments else 'wav.scp'}")
    for key in sorted(set(utt2spk) - utterance_keys):
        errors.append(f"utt2spk key {key} missing from {'segments' if segments else 'wav.scp'}")
    inverse: dict[str, set[str]] = {}
    for utt, values in utt2spk.items():
        inverse.setdefault(values[0], set()).add(utt)
    for speaker, utts in spk2utt.items():
        if inverse.get(speaker, set()) != set(utts):
            errors.append(f"spk2utt mismatch for {speaker}: expected {sorted(inverse.get(speaker, set()))}, found {sorted(set(utts))}")
    return {
        "ok": not errors,
        "errors": errors,
        "counts": {"text": len(text), "wav.scp": len(wav), "utt2spk": len(utt2spk), "spk2utt": len(spk2utt), "segments": len(segments)},
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate ESPnet/Kaldi-style data directory files.")
    parser.add_argument("data_dir", type=Path)
    parser.add_argument("--no-text", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    result = validate(args.data_dir, not args.no_text)
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print("PASS" if result["ok"] else "FAIL")
        for error in result["errors"]:
            print("- " + error)
        print(result["counts"])
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
