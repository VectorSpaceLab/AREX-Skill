#!/usr/bin/env python3
"""Validate PDAugment data layout without importing Muzic or audio/MIDI packages."""

from __future__ import annotations

import argparse
import csv
import json
import os
import shlex
import sys
from pathlib import Path
from typing import Any

REQUIRED_METADATA_COLUMNS = ("wav", "new_wav", "txt", "phone", "new_phone")
COMMON_NOTES = ("C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B")


def add_error(messages: list[str], text: str) -> None:
    messages.append("ERROR: " + text)


def add_warning(messages: list[str], text: str) -> None:
    messages.append("WARN: " + text)


def maybe_missing(messages: list[str], text: str, *, allow_empty: bool) -> None:
    if allow_empty:
        add_warning(messages, text)
    else:
        add_error(messages, text)


def is_writable_dir(path: Path) -> bool:
    return path.is_dir() and os.access(path, os.W_OK)


def count_files(root: Path, suffixes: tuple[str, ...]) -> int:
    if not root.exists() or not root.is_dir():
        return 0
    lowered = tuple(s.lower() for s in suffixes)
    return sum(1 for p in root.rglob("*") if p.is_file() and p.suffix.lower() in lowered)


def validate_frequency_json(path: Path, messages: list[str]) -> dict[str, Any]:
    details: dict[str, Any] = {"octaves": [], "note_count": 0}
    if not path.exists():
        add_error(messages, f"frequency JSON is missing: {path}")
        return details
    if not path.is_file():
        add_error(messages, f"frequency JSON path is not a file: {path}")
        return details
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        add_error(messages, f"frequency JSON is not parseable: {path}: {exc}")
        return details
    if not isinstance(data, dict) or not data:
        add_error(messages, "frequency JSON must be a non-empty object keyed by octave")
        return details
    note_count = 0
    octaves: list[str] = []
    for octave, mapping in data.items():
        if not isinstance(mapping, dict):
            add_error(messages, f"frequency JSON octave {octave!r} is not an object")
            continue
        octaves.append(str(octave))
        missing_notes = [note for note in COMMON_NOTES if note not in mapping]
        if missing_notes:
            add_warning(messages, f"frequency JSON octave {octave!r} is missing common notes: {', '.join(missing_notes)}")
        for note, value in mapping.items():
            if not isinstance(value, (int, float)):
                add_error(messages, f"frequency JSON value for octave {octave!r}, note {note!r} is not numeric")
            else:
                note_count += 1
    details["octaves"] = sorted(octaves)
    details["note_count"] = note_count
    return details


def inspect_metadata(args: argparse.Namespace, messages: list[str]) -> dict[str, Any]:
    path = args.metadata_csv
    details: dict[str, Any] = {"row_count": 0, "columns": [], "missing_wav_references": []}
    if not path.exists():
        add_error(messages, f"metadata CSV is missing: {path}")
        return details
    if not path.is_file():
        add_error(messages, f"metadata CSV path is not a file: {path}")
        return details
    try:
        with path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            columns = reader.fieldnames or []
            details["columns"] = columns
            missing_columns = [col for col in REQUIRED_METADATA_COLUMNS if col not in columns]
            if missing_columns:
                add_error(messages, f"metadata CSV missing required columns: {', '.join(missing_columns)}")
            seen_new_wav: set[str] = set()
            duplicate_new_wav: set[str] = set()
            rows_preview: list[dict[str, str]] = []
            for idx, row in enumerate(reader, start=1):
                details["row_count"] = idx
                if idx <= args.sample_rows:
                    rows_preview.append({col: (row.get(col) or "") for col in REQUIRED_METADATA_COLUMNS})
                new_wav = row.get("new_wav", "")
                if new_wav in seen_new_wav:
                    duplicate_new_wav.add(new_wav)
                elif new_wav:
                    seen_new_wav.add(new_wav)
                wav_value = row.get("wav", "")
                if args.check_wav_references and idx <= args.sample_rows:
                    if not wav_value:
                        details["missing_wav_references"].append(f"row {idx}: empty wav field")
                    elif not wav_reference_exists(wav_value, path.parent):
                        details["missing_wav_references"].append(f"row {idx}: {wav_value}")
            details["rows_preview"] = rows_preview
            if duplicate_new_wav:
                add_warning(messages, f"metadata CSV has duplicate new_wav values, first examples: {', '.join(sorted(duplicate_new_wav)[:5])}")
    except Exception as exc:
        add_error(messages, f"could not read metadata CSV: {path}: {exc}")
        return details
    if details["row_count"] == 0:
        add_error(messages, f"metadata CSV contains no data rows: {path}")
    if details["missing_wav_references"]:
        add_warning(messages, "sampled metadata wav references did not resolve: " + "; ".join(details["missing_wav_references"]))
    return details


def wav_reference_exists(value: str, metadata_parent: Path) -> bool:
    candidate = Path(value)
    if candidate.is_absolute():
        return candidate.exists()
    return candidate.exists() or (metadata_parent / candidate).exists()


def validate_pickle(path: Path, messages: list[str]) -> dict[str, Any]:
    details = {"exists": path.exists(), "suffix": path.suffix}
    if not path.exists():
        add_error(messages, f"alignment pickle is missing: {path}")
        return details
    if not path.is_file():
        add_error(messages, f"alignment pickle path is not a file: {path}")
        return details
    if path.suffix.lower() not in (".pickle", ".pkl"):
        add_warning(messages, f"alignment pickle has uncommon extension {path.suffix!r}; expected .pickle or .pkl")
    if path.stat().st_size == 0:
        add_error(messages, f"alignment pickle is empty: {path}")
    return details


def validate_dataset_dir(args: argparse.Namespace, messages: list[str]) -> dict[str, Any]:
    root = args.dataset_dir
    details = {"wav_count": 0, "transcript_count": 0}
    if not root.exists():
        add_error(messages, f"dataset directory is missing: {root}")
        return details
    if not root.is_dir():
        add_error(messages, f"dataset path is not a directory: {root}")
        return details
    wav_count = count_files(root, (".wav",))
    transcript_count = sum(1 for p in root.rglob("*") if p.is_file() and p.name.endswith(".trans.txt"))
    details["wav_count"] = wav_count
    details["transcript_count"] = transcript_count
    if wav_count == 0:
        maybe_missing(messages, f"no .wav files found under dataset directory: {root}", allow_empty=args.allow_empty_data)
    if transcript_count == 0:
        add_warning(messages, f"no .trans.txt transcript files found under dataset directory: {root}")
    return details


def validate_midi_dir(args: argparse.Namespace, messages: list[str]) -> dict[str, Any]:
    root = args.midi_file_dir
    details = {"midi_count_recursive": 0, "midi_count_top_level": 0}
    if not root.exists():
        add_error(messages, f"MIDI directory is missing: {root}")
        return details
    if not root.is_dir():
        add_error(messages, f"MIDI path is not a directory: {root}")
        return details
    recursive = count_files(root, (".mid", ".midi"))
    top_level = sum(1 for p in root.iterdir() if p.is_file() and p.suffix.lower() in (".mid", ".midi"))
    details["midi_count_recursive"] = recursive
    details["midi_count_top_level"] = top_level
    if recursive == 0:
        maybe_missing(messages, f"no .mid or .midi files found under MIDI directory: {root}", allow_empty=args.allow_empty_data)
    elif top_level == 0:
        add_warning(messages, "MIDI files were found only in nested folders; the inspected source code uses a flat file list unless patched")
    return details


def validate_output_dir(path: Path, label: str, args: argparse.Namespace, messages: list[str]) -> dict[str, Any]:
    details = {"path": str(path), "exists": path.exists(), "writable": False}
    if path.exists():
        if not path.is_dir():
            add_error(messages, f"{label} output path exists but is not a directory: {path}")
        else:
            details["writable"] = is_writable_dir(path)
            if not details["writable"]:
                add_error(messages, f"{label} output directory is not writable: {path}")
    else:
        if args.make_output_dirs:
            try:
                path.mkdir(parents=True, exist_ok=True)
                details["exists"] = True
                details["writable"] = is_writable_dir(path)
            except Exception as exc:
                add_error(messages, f"could not create {label} output directory {path}: {exc}")
        else:
            parent = path.parent if path.parent != Path("") else Path(".")
            if not parent.exists():
                add_warning(messages, f"{label} output directory does not exist and parent is also missing: {path}")
            else:
                add_warning(messages, f"{label} output directory does not exist yet: {path}")
    return details


def command_preview(args: argparse.Namespace) -> str:
    parts = [
        "python",
        "pdaugment.py",
        str(args.pickle_path),
        str(args.frequency_json),
        str(args.dataset_dir),
        str(args.midi_file_dir),
        str(args.metadata_csv),
        str(args.output_duration_dir),
        str(args.output_pitch_dir),
        str(args.output_pdaugment_dir),
        str(args.threads),
    ]
    return " ".join(shlex.quote(part) for part in parts)


def validate(args: argparse.Namespace) -> dict[str, Any]:
    messages: list[str] = []
    if args.threads <= 0:
        add_error(messages, "threads must be a positive integer")
    if args.sample_rows <= 0:
        add_error(messages, "sample_rows must be a positive integer")

    details: dict[str, Any] = {
        "pickle": validate_pickle(args.pickle_path, messages),
        "frequency_json": validate_frequency_json(args.frequency_json, messages),
        "dataset": validate_dataset_dir(args, messages),
        "midi": validate_midi_dir(args, messages),
        "metadata": inspect_metadata(args, messages),
        "outputs": {
            "duration": validate_output_dir(args.output_duration_dir, "duration", args, messages),
            "pitch": validate_output_dir(args.output_pitch_dir, "pitch", args, messages),
            "pdaugment": validate_output_dir(args.output_pdaugment_dir, "pdaugment", args, messages),
        },
        "threads": args.threads,
        "command": command_preview(args),
    }

    add_warning(messages, "inspected pdaugment.py needs a source patch or wrapper for CLI argument runs: load frequency JSON, load alignment pickle, populate MIDI list from the configured folder, join paths safely, and create output file parents")

    errors = [m for m in messages if m.startswith("ERROR:")]
    warnings = [m for m in messages if m.startswith("WARN:")]
    return {"ok": not errors, "errors": errors, "warnings": warnings, "details": details}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate PDAugment positional-argument layout without importing audio, MIDI, or Muzic source packages.",
        epilog=(
            "Example: python scripts/validate_pdaugment_layout.py --pickle-path data/pickle/mel_splits.pickle "
            "--frequency-json utils/frequency.json --dataset-dir data/speech/wav/dev-clean "
            "--midi-file-dir data/midis/processed/midi_6tracks --metadata-csv data/speech/phone/dev-clean_metadata.csv "
            "--output-duration-dir data/duration --output-pitch-dir data/pitch --output-pdaugment-dir data/pdaugment --threads 16"
        ),
    )
    parser.add_argument("--pickle-path", type=Path, required=True, help="Alignment pickle path consumed as pdaugment.py positional argument 1")
    parser.add_argument("--frequency-json", type=Path, required=True, help="Frequency JSON path consumed as positional argument 2")
    parser.add_argument("--dataset-dir", type=Path, required=True, help="WAV dataset directory consumed as positional argument 3")
    parser.add_argument("--midi-file-dir", type=Path, required=True, help="Processed MIDI directory consumed as positional argument 4")
    parser.add_argument("--metadata-csv", type=Path, required=True, help="Metadata CSV path consumed as positional argument 5")
    parser.add_argument("--output-duration-dir", type=Path, required=True, help="Duration output root consumed as positional argument 6")
    parser.add_argument("--output-pitch-dir", type=Path, required=True, help="Pitch output root consumed as positional argument 7")
    parser.add_argument("--output-pdaugment-dir", type=Path, required=True, help="Combined PDAugment output root consumed as positional argument 8")
    parser.add_argument("--threads", type=int, required=True, help="Positive thread count consumed as positional argument 9")
    parser.add_argument("--allow-empty-data", action="store_true", help="Warn instead of failing when WAV or MIDI files are absent")
    parser.add_argument("--check-wav-references", action="store_true", help="Check sampled metadata wav paths for existence")
    parser.add_argument("--sample-rows", type=int, default=5, help="Number of metadata rows to preview/check")
    parser.add_argument("--make-output-dirs", action="store_true", help="Create missing output root directories")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    return parser


def print_human(report: dict[str, Any]) -> None:
    print("PDAugment layout validation:", "OK" if report["ok"] else "FAILED")
    print("Final positional command:")
    print(report["details"]["command"])
    print("Summary:")
    print(f"- metadata rows: {report['details']['metadata'].get('row_count', 0)}")
    print(f"- dataset wav files: {report['details']['dataset'].get('wav_count', 0)}")
    print(f"- dataset transcript files: {report['details']['dataset'].get('transcript_count', 0)}")
    print(f"- MIDI files recursive/top-level: {report['details']['midi'].get('midi_count_recursive', 0)}/{report['details']['midi'].get('midi_count_top_level', 0)}")
    print(f"- frequency octaves: {', '.join(report['details']['frequency_json'].get('octaves', []))}")
    print(f"- threads: {report['details']['threads']}")
    for warning in report["warnings"]:
        print(warning)
    for error in report["errors"]:
        print(error)


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    report = validate(args)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_human(report)
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
