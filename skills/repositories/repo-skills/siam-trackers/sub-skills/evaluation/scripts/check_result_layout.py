#!/usr/bin/env python3
"""Offline structural validator for NanoTrack-compatible tracking results.

This script uses only the Python standard library. It does not import the
tracker, load a dataset, download files, start worker processes, or open a GUI.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple


VOT_SHORT = {"VOT2016", "VOT2017", "VOT2018", "VOT2019"}
VOT_LT = {"VOT2018-LT"}
OPE_EXACT = {
    "OTB50",
    "OTB100",
    "OTB2013",
    "OTB2015",
    "DTB70",
    "UAVDT",
    "VisDrone",
    "LaSOT",
    "UAV123",
    "UAV20L",
    "NFS30",
    "NFS240",
}
GOT10K = {"GOT-10k"}
FACTORY_ONLY = {"TrackingNet"}
SAFE_COMPONENT = re.compile(r"^[^/\\\x00]+$")
REP_FILE = re.compile(r"^(?P<seq>.+)_(?P<rep>[0-9]{3})\.txt$")


@dataclass
class Report:
    dataset: str
    category: str = ""
    tracker_dir: str = ""
    checked_files: List[str] = field(default_factory=list)
    sequences: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def error(self, message: str) -> None:
        self.errors.append(message)

    def warn(self, message: str) -> None:
        self.warnings.append(message)

    @property
    def ok(self) -> bool:
        return not self.errors

    def as_dict(self) -> dict:
        return {
            "ok": self.ok,
            "dataset": self.dataset,
            "category": self.category,
            "tracker_dir": self.tracker_dir,
            "sequences": sorted(self.sequences),
            "checked_files": sorted(self.checked_files),
            "warnings": self.warnings,
            "errors": self.errors,
        }


def classify_dataset(name: str) -> Tuple[str, List[str]]:
    """Return (layout category, compatibility notes), or raise ValueError."""
    if name in VOT_LT:
        return "vot-lt", []
    if name in VOT_SHORT:
        notes = []
        if name == "VOT2017":
            notes.append(
                "VOT2017 is handled by the standalone evaluator but not by "
                "DatasetFactory used by the maintained test entry point."
            )
        return "vot-short", notes
    if name in GOT10K:
        return "got10k", []
    if name in OPE_EXACT:
        notes = []
        if name in {"UAVDT", "VisDrone"}:
            notes.append(
                f"{name} has a dataset wrapper, but the maintained evaluator "
                "references its class without importing it; patch that import "
                "in an active runtime before full evaluation."
            )
        return "ope", notes
    if name in FACTORY_ONLY:
        raise ValueError(
            "TrackingNet is constructible by DatasetFactory but has no dispatch "
            "branch in the maintained evaluator."
        )
    if name.startswith("OTB"):
        return "ope", [
            "The evaluator dispatches any name containing OTB, but the exact "
            "name still needs a matching dataset metadata file."
        ]
    if name.startswith("NFS"):
        return "ope", [
            "The evaluator dispatches any name containing NFS; NFS30 and NFS240 "
            "are the documented forms."
        ]
    raise ValueError(
        "unsupported dataset name; use --list-datasets to see maintained "
        "dispatch families"
    )


def validate_component(value: str, label: str) -> Optional[str]:
    if not value or value in {".", ".."} or not SAFE_COMPONENT.match(value):
        return f"{label} must be one non-empty path component: {value!r}"
    return None


def parse_expected(values: Sequence[str]) -> Tuple[Dict[str, Optional[int]], List[str]]:
    expected: Dict[str, Optional[int]] = {}
    errors: List[str] = []
    for raw in values:
        name = raw
        frames: Optional[int] = None
        if ":" in raw:
            name, count = raw.rsplit(":", 1)
            try:
                frames = int(count)
            except ValueError:
                errors.append(f"invalid frame count in --sequence {raw!r}")
                continue
            if frames <= 0:
                errors.append(f"frame count must be positive in --sequence {raw!r}")
                continue
        problem = validate_component(name, "sequence name")
        if problem:
            errors.append(problem)
            continue
        if name in expected:
            errors.append(f"duplicate --sequence value: {name!r}")
            continue
        expected[name] = frames
    return expected, errors


def read_lines(path: Path, report: Report) -> Optional[List[str]]:
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        report.error(f"cannot read {path}: {exc}")
        return None
    report.checked_files.append(str(path))
    lines = text.splitlines()
    if not lines:
        report.error(f"empty result file: {path}")
        return None
    return lines


def parse_floats(
    line: str,
    path: Path,
    line_no: int,
    report: Report,
    widths: Iterable[int],
    *,
    positive_wh: bool = False,
) -> Optional[List[float]]:
    fields = [field.strip() for field in line.split(",")]
    allowed = set(widths)
    if len(fields) not in allowed:
        report.error(
            f"{path}:{line_no}: expected {sorted(allowed)} comma-separated "
            f"values, found {len(fields)}"
        )
        return None
    try:
        values = [float(field) for field in fields]
    except ValueError:
        report.error(f"{path}:{line_no}: non-numeric value")
        return None
    if not all(math.isfinite(value) for value in values):
        report.error(f"{path}:{line_no}: NaN or infinity is not a valid box value")
        return None
    if positive_wh and len(values) == 4 and (values[2] <= 0 or values[3] <= 0):
        report.error(f"{path}:{line_no}: width and height must be positive")
        return None
    return values


def validate_boxes(
    path: Path,
    report: Report,
    expected_frames: Optional[int],
) -> Optional[int]:
    lines = read_lines(path, report)
    if lines is None:
        return None
    for line_no, line in enumerate(lines, 1):
        parse_floats(line, path, line_no, report, {4}, positive_wh=True)
    if expected_frames is not None and len(lines) != expected_frames:
        report.error(
            f"{path}: expected {expected_frames} frame rows, found {len(lines)}"
        )
    return len(lines)


def parse_scalar_rows(
    path: Path,
    report: Report,
    *,
    expected_rows: int,
    first_blank: bool = False,
    positive: bool = False,
    expected_columns: Optional[int] = None,
) -> None:
    lines = read_lines(path, report)
    if lines is None:
        return
    if len(lines) != expected_rows:
        report.error(f"{path}: expected {expected_rows} rows, found {len(lines)}")
    widths: List[int] = []
    for line_no, line in enumerate(lines, 1):
        if first_blank and line_no == 1:
            if line.strip():
                report.error(f"{path}:1: first confidence row must be blank")
            continue
        if not line.strip():
            report.error(f"{path}:{line_no}: unexpected blank scalar row")
            continue
        fields = [field.strip() for field in line.split(",")]
        widths.append(len(fields))
        for field in fields:
            try:
                value = float(field)
            except ValueError:
                report.error(f"{path}:{line_no}: non-numeric scalar value")
                continue
            if not math.isfinite(value):
                report.error(f"{path}:{line_no}: scalar must be finite")
            elif positive and value <= 0:
                report.error(f"{path}:{line_no}: runtime must be positive")
    if widths and len(set(widths)) != 1:
        report.error(f"{path}: inconsistent scalar column counts: {sorted(set(widths))}")
    if expected_columns is not None and widths and widths[0] != expected_columns:
        report.error(
            f"{path}: expected {expected_columns} runtime column(s), found {widths[0]}"
        )


def parse_vot_rows(path: Path, report: Report, expected_frames: Optional[int], strict: bool) -> None:
    lines = read_lines(path, report)
    if lines is None:
        return
    rows: List[Tuple[str, object]] = []
    for line_no, line in enumerate(lines, 1):
        fields = [field.strip() for field in line.split(",")]
        if len(fields) == 1:
            try:
                value = int(fields[0])
            except ValueError:
                report.error(f"{path}:{line_no}: invalid VOT marker {fields[0]!r}")
                rows.append(("invalid", fields[0]))
                continue
            if value not in {0, 1, 2}:
                report.error(f"{path}:{line_no}: VOT marker must be 0, 1, or 2")
                rows.append(("invalid", value))
            else:
                rows.append(("marker", value))
        elif len(fields) in {4, 8}:
            values = parse_floats(line, path, line_no, report, {4, 8}, positive_wh=True)
            rows.append(("box", values))
        else:
            report.error(
                f"{path}:{line_no}: VOT row must be one marker or a 4/8-value box"
            )
            rows.append(("invalid", fields))
    if expected_frames is not None and len(lines) != expected_frames:
        report.error(f"{path}: expected {expected_frames} frame rows, found {len(lines)}")
    if not rows or rows[0] != ("marker", 1):
        report.error(f"{path}: first VOT row must be initialization marker 1")
    if strict:
        allowed_restarts = {0}
        for index, row in enumerate(rows):
            if row == ("marker", 2):
                for offset in range(1, 5):
                    following = index + offset
                    if following < len(rows) and rows[following] != ("marker", 0):
                        report.error(
                            f"{path}:{following + 1}: expected skip marker 0 "
                            f"after loss at line {index + 1}"
                        )
                restart = index + 5
                if restart < len(rows):
                    allowed_restarts.add(restart)
                    if rows[restart] != ("marker", 1):
                        report.error(
                            f"{path}:{restart + 1}: expected reinitialization marker 1 "
                            f"five frames after loss"
                        )
        for index, row in enumerate(rows):
            if row == ("marker", 1) and index not in allowed_restarts:
                report.error(f"{path}:{index + 1}: unexpected initialization marker 1")


def ensure_expected(
    discovered: Iterable[str],
    expected: Dict[str, Optional[int]],
    report: Report,
    allow_extra: bool,
) -> List[str]:
    names = sorted(set(discovered))
    if not names:
        report.error("no sequence results found")
        return names
    for name in expected:
        if name not in names:
            report.error(f"missing expected sequence result: {name}")
    if expected and not allow_extra:
        extras = sorted(set(names) - set(expected))
        if extras:
            report.error(f"unexpected sequence results: {', '.join(extras)}")
    report.sequences.extend(names)
    return names


def validate_ope(
    tracker_dir: Path,
    expected: Dict[str, Optional[int]],
    report: Report,
    allow_extra: bool,
) -> None:
    files = sorted(
        path for path in tracker_dir.glob("*.txt")
        if not path.name.endswith("_time.txt")
    )
    by_name = {path.stem: path for path in files}
    names = ensure_expected(by_name, expected, report, allow_extra)
    for name in names:
        validate_boxes(by_name[name], report, expected.get(name))


def validate_vot_short(
    tracker_dir: Path,
    expected: Dict[str, Optional[int]],
    report: Report,
    allow_extra: bool,
    strict: bool,
) -> None:
    baseline = tracker_dir / "baseline"
    dirs = sorted(path for path in baseline.iterdir() if path.is_dir()) if baseline.is_dir() else []
    by_name = {path.name: path for path in dirs}
    names = ensure_expected(by_name, expected, report, allow_extra)
    for name in names:
        files = sorted(
            path for path in by_name[name].glob(f"{name}_*.txt")
            if REP_FILE.match(path.name)
        )
        if not any(path.name == f"{name}_001.txt" for path in files):
            report.error(f"{by_name[name]}: missing required {name}_001.txt")
        if len(files) not in {1, 15}:
            report.warn(
                f"{by_name[name]}: found {len(files)} repetition file(s); the loader "
                "uses all 15 only when exactly 15 exist, otherwise only the first"
            )
        for path in files:
            parse_vot_rows(path, report, expected.get(name), strict)


def validate_vot_lt(
    tracker_dir: Path,
    expected: Dict[str, Optional[int]],
    report: Report,
    allow_extra: bool,
) -> None:
    longterm = tracker_dir / "longterm"
    dirs = sorted(path for path in longterm.iterdir() if path.is_dir()) if longterm.is_dir() else []
    by_name = {path.name: path for path in dirs}
    names = ensure_expected(by_name, expected, report, allow_extra)
    for name in names:
        seq_dir = by_name[name]
        trajectory = seq_dir / f"{name}_001.txt"
        confidence = seq_dir / f"{name}_001_confidence.value"
        timing = seq_dir / f"{name}_time.txt"
        lines = read_lines(trajectory, report) if trajectory.is_file() else None
        if lines is None:
            if not trajectory.is_file():
                report.error(f"missing trajectory file: {trajectory}")
            continue
        for line_no, line in enumerate(lines, 1):
            fields = [field.strip() for field in line.split(",")]
            if len(fields) == 1 and fields[0] in {"0", "1"}:
                if line_no > 1 and fields[0] == "1":
                    report.warn(f"{trajectory}:{line_no}: unusual LT reinitialization marker 1")
                continue
            parse_floats(line, trajectory, line_no, report, {4}, positive_wh=True)
        if lines[0].strip() not in {"0", "1"}:
            report.error(f"{trajectory}: first LT row must be initialization marker 0 or 1")
        if expected.get(name) is not None and len(lines) != expected[name]:
            report.error(
                f"{trajectory}: expected {expected[name]} frame rows, found {len(lines)}"
            )
        if confidence.is_file():
            parse_scalar_rows(confidence, report, expected_rows=len(lines), first_blank=True)
        else:
            report.error(f"missing confidence file: {confidence}")
        if timing.is_file():
            parse_scalar_rows(timing, report, expected_rows=len(lines), positive=True)
        else:
            report.error(f"missing timing file: {timing}")


def validate_got10k(
    tracker_dir: Path,
    expected: Dict[str, Optional[int]],
    report: Report,
    allow_extra: bool,
) -> None:
    dirs = sorted(path for path in tracker_dir.iterdir() if path.is_dir()) if tracker_dir.is_dir() else []
    by_name = {path.name: path for path in dirs}
    names = ensure_expected(by_name, expected, report, allow_extra)
    for name in names:
        seq_dir = by_name[name]
        records = sorted(
            path for path in seq_dir.glob(f"{name}_*.txt")
            if REP_FILE.match(path.name)
        )
        if not records:
            report.error(f"{seq_dir}: no {name}_NNN.txt result files")
            continue
        if not any(path.name == f"{name}_001.txt" for path in records):
            report.error(f"{seq_dir}: missing required {name}_001.txt")
        row_counts: List[int] = []
        for path in records:
            count = validate_boxes(path, report, expected.get(name))
            if count is not None:
                row_counts.append(count)
        if row_counts and len(set(row_counts)) != 1:
            report.error(f"{seq_dir}: repetition files have different frame counts")
        timing = seq_dir / f"{name}_time.txt"
        if timing.is_file() and row_counts:
            parse_scalar_rows(
                timing,
                report,
                expected_rows=row_counts[0],
                positive=True,
                expected_columns=len(records),
            )
        elif not timing.is_file():
            report.error(f"missing timing file: {timing}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Validate NanoTrack-compatible result names, directories, and text "
            "rows without loading a dataset or tracker."
        ),
        epilog=(
            "Example: check_result_layout.py --dataset VOT2018 --results-root "
            "./results --tracker nano --sequence bolt:350. Invalid dataset "
            "names, missing tracker directories, malformed rows, NaN/Inf boxes, "
            "bad VOT restart markers, and LT confidence/time mismatches exit 1."
        ),
    )
    parser.add_argument("--dataset", help="exact benchmark dataset name")
    parser.add_argument(
        "--results-root",
        type=Path,
        help="parent directory corresponding to the test/eval result-root flag",
    )
    parser.add_argument("--tracker-name", help="exact tracker directory name; no glob")
    parser.add_argument(
        "--sequence",
        action="append",
        default=[],
        metavar="NAME[:FRAMES]",
        help="expected sequence and optional frame count; repeat as needed",
    )
    parser.add_argument(
        "--allow-extra-sequences",
        action="store_true",
        help="allow discovered sequences not named by --sequence",
    )
    parser.add_argument(
        "--relax-vot-restart",
        action="store_true",
        help="validate VOT row types but not the stock five-frame restart schedule",
    )
    parser.add_argument("--json", action="store_true", help="emit one JSON report")
    parser.add_argument(
        "--list-datasets",
        action="store_true",
        help="print maintained dispatch names/families and exit",
    )
    return parser


def print_dataset_list() -> None:
    print("OPE: " + ", ".join(sorted(OPE_EXACT)))
    print("VOT restart: " + ", ".join(sorted(VOT_SHORT)))
    print("VOT long-term: " + ", ".join(sorted(VOT_LT)))
    print("GOT-10k: " + ", ".join(sorted(GOT10K)))
    print("Factory-only (not eval-dispatched): " + ", ".join(sorted(FACTORY_ONLY)))


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.list_datasets:
        print_dataset_list()
        return 0
    missing = [
        flag
        for flag, value in (
            ("--dataset", args.dataset),
            ("--results-root", args.results_root),
            ("--tracker-name", args.tracker_name),
        )
        if value is None
    ]
    if missing:
        parser.error("required unless --list-datasets: " + ", ".join(missing))

    report = Report(dataset=args.dataset)
    problem = validate_component(args.dataset, "dataset name")
    if problem:
        report.error(problem)
    problem = validate_component(args.tracker_name, "tracker name")
    if problem:
        report.error(problem)
    try:
        report.category, notes = classify_dataset(args.dataset)
        report.warnings.extend(notes)
    except ValueError as exc:
        report.error(f"dataset {args.dataset!r}: {exc}")

    expected, expected_errors = parse_expected(args.sequence)
    report.errors.extend(expected_errors)
    tracker_dir = args.results_root / args.dataset / args.tracker_name
    report.tracker_dir = str(tracker_dir)
    if not tracker_dir.is_dir():
        report.error(f"tracker result directory does not exist: {tracker_dir}")
    elif report.category == "ope":
        validate_ope(tracker_dir, expected, report, args.allow_extra_sequences)
    elif report.category == "vot-short":
        validate_vot_short(
            tracker_dir,
            expected,
            report,
            args.allow_extra_sequences,
            not args.relax_vot_restart,
        )
    elif report.category == "vot-lt":
        validate_vot_lt(tracker_dir, expected, report, args.allow_extra_sequences)
    elif report.category == "got10k":
        validate_got10k(tracker_dir, expected, report, args.allow_extra_sequences)

    if args.json:
        print(json.dumps(report.as_dict(), indent=2, sort_keys=True))
    else:
        status = "PASS" if report.ok else "FAIL"
        print(f"{status}: {report.dataset} / {args.tracker_name} ({report.category or 'unknown'})")
        print(f"tracker_dir: {report.tracker_dir}")
        print(f"sequences: {len(set(report.sequences))}; files checked: {len(report.checked_files)}")
        for warning in report.warnings:
            print(f"WARNING: {warning}")
        for error in report.errors:
            print(f"ERROR: {error}", file=sys.stderr)
    return 0 if report.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
