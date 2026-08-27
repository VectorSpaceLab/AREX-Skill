#!/usr/bin/env python3
"""Validate StyleTTS2 data lists and OOD text files without training."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Sequence, Tuple


@dataclass
class ParseMessage:
    level: str
    line_no: int
    message: str


@dataclass
class RowRecord:
    line_no: int
    raw: str
    fields: List[str]
    kind: str
    speaker_missing: bool = False
    speaker: Optional[str] = None
    text: Optional[str] = None
    wav_path: Optional[str] = None


@dataclass
class FileSummary:
    label: str
    total: int = 0
    valid: int = 0
    warnings: int = 0
    errors: int = 0
    speaker_missing: int = 0
    unique_speakers: int = 0
    shortest_text: Optional[int] = None
    longest_text: Optional[int] = None
    missing_files: int = 0
    parsed_examples: List[str] = None
    issue_examples: List[str] = None

    def __post_init__(self) -> None:
        if self.parsed_examples is None:
            self.parsed_examples = []
        if self.issue_examples is None:
            self.issue_examples = []


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate StyleTTS2 data lists and OOD text files safely.",
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=None,
        help="Optional checkout root used to resolve relative inputs.",
    )
    parser.add_argument(
        "--train-list",
        type=Path,
        default=Path("Data/train_list.txt"),
        help="Training list path (default: Data/train_list.txt).",
    )
    parser.add_argument(
        "--val-list",
        type=Path,
        default=Path("Data/val_list.txt"),
        help="Validation list path (default: Data/val_list.txt).",
    )
    parser.add_argument(
        "--ood-texts",
        type=Path,
        default=Path("Data/OOD_texts.txt"),
        help="OOD text path (default: Data/OOD_texts.txt).",
    )
    parser.add_argument(
        "--audio-root",
        type=Path,
        default=None,
        help="Root directory used to check wav existence when --check-files is set.",
    )
    parser.add_argument(
        "--sample-limit",
        type=int,
        default=5,
        help="Maximum number of example issues or sample rows to print per section.",
    )
    parser.add_argument(
        "--strict-speaker",
        action="store_true",
        help="Require explicit speaker ids in train/val rows.",
    )
    parser.add_argument(
        "--check-files",
        action="store_true",
        help="Check whether train/val wav files exist under --audio-root.",
    )
    return parser


def resolve_input(path: Path, repo_root: Optional[Path]) -> Path:
    if path.is_absolute():
        return path
    base = repo_root if repo_root is not None else Path.cwd()
    return (base / path).resolve()


def read_lines(path: Path) -> List[str]:
    with path.open("r", encoding="utf-8", errors="ignore") as handle:
        return handle.readlines()


def parse_train_val_row(line: str, line_no: int, strict_speaker: bool) -> Tuple[Optional[RowRecord], List[ParseMessage]]:
    raw = line.rstrip("\n")
    stripped = raw.strip()
    if not stripped:
        return None, []

    fields = [part.strip() for part in stripped.split("|")]
    messages: List[ParseMessage] = []

    if len(fields) not in (2, 3):
        messages.append(ParseMessage("error", line_no, f"expected 2 or 3 fields, found {len(fields)}"))
        return RowRecord(line_no=line_no, raw=raw, fields=fields, kind="train-val"), messages

    wav_path = fields[0]
    text = fields[1]

    if not wav_path:
        messages.append(ParseMessage("error", line_no, "missing wav path"))
    if not text:
        messages.append(ParseMessage("error", line_no, "missing transcription"))

    if len(fields) == 2:
        if strict_speaker:
            messages.append(ParseMessage("error", line_no, "missing speaker id in strict mode"))
        else:
            messages.append(ParseMessage("warning", line_no, "speaker id missing; loader will default it to 0"))
        speaker = "0"
        speaker_missing = True
    else:
        speaker = fields[2]
        speaker_missing = False
        if not speaker:
            messages.append(ParseMessage("error", line_no, "empty speaker id"))
        else:
            try:
                int(speaker)
            except ValueError:
                messages.append(ParseMessage("error", line_no, f"speaker id is not an integer: {speaker!r}"))

    record = RowRecord(
        line_no=line_no,
        raw=raw,
        fields=fields,
        kind="train-val",
        speaker_missing=speaker_missing,
        speaker=speaker,
        text=text,
        wav_path=wav_path,
    )
    return record, messages


def parse_ood_row(line: str, line_no: int) -> Tuple[Optional[RowRecord], List[ParseMessage]]:
    raw = line.rstrip("\n")
    stripped = raw.strip()
    if not stripped:
        return None, []

    fields = [part.strip() for part in stripped.split("|")]
    messages: List[ParseMessage] = []

    if not fields:
        messages.append(ParseMessage("error", line_no, "empty OOD row"))
        return RowRecord(line_no=line_no, raw=raw, fields=fields, kind="ood"), messages

    if len(fields) == 1:
        text = fields[0]
        source = "field1"
    elif ".wav" in fields[0].lower():
        if len(fields) < 2:
            messages.append(ParseMessage("error", line_no, "wav-style OOD row is missing the text field"))
            text = ""
        else:
            text = fields[1]
        source = "field2"
    else:
        text = fields[0]
        source = "field1"

    if not text:
        messages.append(ParseMessage("error", line_no, "missing OOD text"))

    record = RowRecord(
        line_no=line_no,
        raw=raw,
        fields=fields,
        kind=source,
        text=text,
    )
    return record, messages


def update_text_stats(summary: FileSummary, text: str) -> None:
    length = len(text)
    summary.shortest_text = length if summary.shortest_text is None else min(summary.shortest_text, length)
    summary.longest_text = length if summary.longest_text is None else max(summary.longest_text, length)


def preview(text: str, limit: int = 120) -> str:
    if len(text) <= limit:
        return text
    return text[: limit - 3] + "..."


def summarize_train_val(
    label: str,
    path: Path,
    repo_root: Optional[Path],
    audio_root: Optional[Path],
    sample_limit: int,
    strict_speaker: bool,
    check_files: bool,
) -> FileSummary:
    resolved = resolve_input(path, repo_root)
    summary = FileSummary(label=label)
    if not resolved.exists():
        summary.errors += 1
        summary.issue_examples.append(f"{label}: file not found: {resolved}")
        return summary

    lines = read_lines(resolved)
    speakers = set()
    parsed_rows: List[RowRecord] = []

    for line_no, line in enumerate(lines, start=1):
        record, messages = parse_train_val_row(line, line_no, strict_speaker=strict_speaker)
        if record is None:
            continue
        summary.total += 1
        parsed_rows.append(record)
        if record.text is not None:
            update_text_stats(summary, record.text)
        if record.speaker is not None:
            speakers.add(record.speaker)
        if record.speaker_missing:
            summary.speaker_missing += 1
        if len(summary.parsed_examples) < sample_limit:
            summary.parsed_examples.append(f"{line_no}: {preview(record.raw)}")

        has_error = False
        for msg in messages:
            if msg.level == "error":
                summary.errors += 1
                has_error = True
            else:
                summary.warnings += 1
            if len(summary.issue_examples) < sample_limit:
                summary.issue_examples.append(f"{label}:{msg.line_no}: {msg.level}: {msg.message}")
        if not has_error:
            summary.valid += 1

    summary.unique_speakers = len(speakers)

    if check_files:
        if audio_root is None:
            summary.errors += 1
            summary.issue_examples.append(f"{label}: --audio-root is required when --check-files is set")
        else:
            for record in parsed_rows:
                candidate = Path(record.wav_path or "")
                if candidate.is_absolute():
                    exists = candidate.exists()
                    checked = candidate
                else:
                    checked = (audio_root / candidate).resolve()
                    exists = checked.exists()
                if not exists:
                    summary.missing_files += 1
                    summary.errors += 1
                    if len(summary.issue_examples) < sample_limit:
                        summary.issue_examples.append(f"{label}:{record.line_no}: missing file: {checked}")

    return summary


def summarize_ood(path: Path, repo_root: Optional[Path], sample_limit: int) -> FileSummary:
    resolved = resolve_input(path, repo_root)
    summary = FileSummary(label="ood")
    if not resolved.exists():
        summary.errors += 1
        summary.issue_examples.append(f"ood: file not found: {resolved}")
        return summary

    lines = read_lines(resolved)
    for line_no, line in enumerate(lines, start=1):
        record, messages = parse_ood_row(line, line_no)
        if record is None:
            continue
        summary.total += 1
        if record.text is not None:
            summary.valid += 1
            update_text_stats(summary, record.text)
        if len(summary.parsed_examples) < sample_limit:
            sample = record.text if record.text is not None else ""
            summary.parsed_examples.append(f"{line_no}: {preview(sample)}")
        for msg in messages:
            if msg.level == "error":
                summary.errors += 1
            else:
                summary.warnings += 1
            if len(summary.issue_examples) < sample_limit:
                summary.issue_examples.append(f"ood:{msg.line_no}: {msg.level}: {msg.message}")

    return summary


def print_summary(summary: FileSummary) -> None:
    print(f"[{summary.label}] rows={summary.total} valid={summary.valid} warnings={summary.warnings} errors={summary.errors}")
    if summary.speaker_missing:
        print(f"[{summary.label}] implicit speaker rows={summary.speaker_missing}")
    if summary.unique_speakers:
        print(f"[{summary.label}] unique speakers={summary.unique_speakers}")
    if summary.shortest_text is not None and summary.longest_text is not None:
        print(f"[{summary.label}] text length range={summary.shortest_text}..{summary.longest_text}")
    if summary.missing_files:
        print(f"[{summary.label}] missing files={summary.missing_files}")
    if summary.parsed_examples:
        print(f"[{summary.label}] sample rows:")
        for example in summary.parsed_examples:
            print(f"  - {example}")
    if summary.issue_examples:
        print(f"[{summary.label}] sample issues:")
        for example in summary.issue_examples:
            print(f"  - {example}")


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    sample_limit = max(0, args.sample_limit)
    repo_root = args.repo_root.resolve() if args.repo_root is not None else None
    if args.audio_root is not None:
        audio_root = resolve_input(args.audio_root, repo_root)
    else:
        audio_root = None

    train_summary = summarize_train_val(
        "train",
        args.train_list,
        repo_root=repo_root,
        audio_root=audio_root,
        sample_limit=sample_limit,
        strict_speaker=args.strict_speaker,
        check_files=args.check_files,
    )
    val_summary = summarize_train_val(
        "val",
        args.val_list,
        repo_root=repo_root,
        audio_root=audio_root,
        sample_limit=sample_limit,
        strict_speaker=args.strict_speaker,
        check_files=args.check_files,
    )
    ood_summary = summarize_ood(
        args.ood_texts,
        repo_root=repo_root,
        sample_limit=sample_limit,
    )

    print_summary(train_summary)
    print_summary(val_summary)
    print_summary(ood_summary)

    total_errors = train_summary.errors + val_summary.errors + ood_summary.errors
    if total_errors:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
