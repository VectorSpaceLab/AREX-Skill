#!/usr/bin/env python3
"""Validate ECCV2022-RIFE Vimeo triplet data layout without training.

The checker uses only the Python standard library. It verifies list files,
relative sequence keys, required triplet filenames, PNG headers, dimensions,
and the train/validation split implied by dataset.VimeoDataset.
"""

from __future__ import annotations

import argparse
import os
import struct
import sys
from pathlib import Path
from typing import Iterable, List, Optional, Sequence, Tuple

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
REQUIRED_FRAMES = ("im1.png", "im2.png", "im3.png")


class Finding:
    def __init__(self, level: str, message: str) -> None:
        self.level = level
        self.message = message

    def __str__(self) -> str:
        return f"{self.level}: {self.message}"


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Safely validate the Vimeo90K triplet layout expected by "
            "ECCV2022-RIFE training. This does not download data or run train.py."
        )
    )
    parser.add_argument(
        "--root",
        default="vimeo_triplet",
        help=(
            "Path to the vimeo_triplet directory. If a repository root containing "
            "vimeo_triplet/ is supplied, the checker will use that child directory."
        ),
    )
    parser.add_argument(
        "--sample-per-list",
        type=int,
        default=20,
        help=(
            "Maximum number of entries to check from each list by default. "
            "For tri_trainlist.txt, split-boundary and final entries are also checked."
        ),
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Check every listed sequence instead of a bounded deterministic sample.",
    )
    parser.add_argument(
        "--min-crop-size",
        type=int,
        default=224,
        help="Minimum height and width required for the training random crop.",
    )
    parser.add_argument(
        "--skip-png-header",
        action="store_true",
        help="Only check path existence; skip PNG signature and dimension checks.",
    )
    return parser.parse_args(argv)


def resolve_root(user_root: str, findings: List[Finding]) -> Path:
    root = Path(user_root).expanduser()
    child = root / "vimeo_triplet"
    if not (root / "sequences").exists() and child.exists():
        findings.append(Finding("WARN", f"using child dataset directory: {child}"))
        return child
    return root


def read_list_file(path: Path, label: str) -> Tuple[List[str], List[Finding]]:
    findings: List[Finding] = []
    entries: List[str] = []
    if not path.exists():
        return entries, [Finding("ERROR", f"missing {label}: {path}")]
    if not path.is_file():
        return entries, [Finding("ERROR", f"{label} is not a file: {path}")]

    try:
        raw_lines = path.read_text(encoding="utf-8").splitlines()
    except UnicodeDecodeError as exc:
        return entries, [Finding("ERROR", f"cannot decode {label} as UTF-8 text: {exc}")]
    except OSError as exc:
        return entries, [Finding("ERROR", f"cannot read {label}: {exc}")]

    seen = set()
    for line_no, raw in enumerate(raw_lines, start=1):
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            continue
        normalized = stripped.replace("\\", "/").rstrip("/")
        if normalized != stripped:
            findings.append(
                Finding(
                    "WARN",
                    f"{label}:{line_no} normalized {stripped!r} to {normalized!r}",
                )
            )
        if not normalized:
            findings.append(Finding("ERROR", f"{label}:{line_no} is empty after normalization"))
            continue
        if os.path.isabs(normalized):
            findings.append(Finding("ERROR", f"{label}:{line_no} must be relative, got {normalized!r}"))
            continue
        parts = normalized.split("/")
        if any(part in ("", ".", "..") for part in parts):
            findings.append(
                Finding(
                    "ERROR",
                    f"{label}:{line_no} must not contain empty, '.', or '..' path components: {normalized!r}",
                )
            )
            continue
        if normalized in seen:
            findings.append(Finding("WARN", f"{label}:{line_no} duplicates sequence key {normalized!r}"))
        seen.add(normalized)
        entries.append(normalized)

    if not entries:
        findings.append(Finding("ERROR", f"{label} contains no usable sequence entries"))
    return entries, findings


def select_indices(length: int, sample_per_list: int, check_all: bool, include_split: bool) -> List[int]:
    if length <= 0:
        return []
    if check_all:
        return list(range(length))
    count = max(sample_per_list, 0)
    indices = set(range(min(length, count)))
    indices.add(length - 1)
    if include_split:
        split = int(length * 0.95)
        for idx in (split - 1, split, split + 1):
            if 0 <= idx < length:
                indices.add(idx)
    return sorted(indices)


def png_size(path: Path) -> Tuple[int, int]:
    with path.open("rb") as handle:
        header = handle.read(24)
    if len(header) < 24:
        raise ValueError("file is too short to be a PNG")
    if header[:8] != PNG_SIGNATURE:
        raise ValueError("missing PNG signature")
    if header[12:16] != b"IHDR":
        raise ValueError("missing PNG IHDR chunk")
    width, height = struct.unpack(">II", header[16:24])
    if width <= 0 or height <= 0:
        raise ValueError(f"invalid PNG dimensions {width}x{height}")
    return width, height


def validate_sequence(
    sequence_root: Path,
    list_label: str,
    entry: str,
    index: int,
    skip_png_header: bool,
    min_crop_size: int,
    is_training_entry: bool,
) -> List[Finding]:
    findings: List[Finding] = []
    seq_dir = sequence_root / entry
    if not seq_dir.exists():
        return [Finding("ERROR", f"{list_label}[{index}] missing sequence directory: {seq_dir}")]
    if not seq_dir.is_dir():
        return [Finding("ERROR", f"{list_label}[{index}] sequence path is not a directory: {seq_dir}")]

    dimensions: List[Tuple[str, int, int]] = []
    for frame in REQUIRED_FRAMES:
        frame_path = seq_dir / frame
        if not frame_path.exists():
            findings.append(Finding("ERROR", f"{list_label}[{index}] {entry!r} missing {frame}"))
            continue
        if not frame_path.is_file():
            findings.append(Finding("ERROR", f"{list_label}[{index}] {entry!r} {frame} is not a file"))
            continue
        if skip_png_header:
            continue
        try:
            width, height = png_size(frame_path)
        except (OSError, ValueError) as exc:
            findings.append(Finding("ERROR", f"{list_label}[{index}] {entry!r}/{frame} invalid PNG: {exc}"))
            continue
        dimensions.append((frame, width, height))

    if dimensions:
        unique_sizes = {(width, height) for _, width, height in dimensions}
        if len(unique_sizes) > 1:
            detail = ", ".join(f"{name}={width}x{height}" for name, width, height in dimensions)
            findings.append(Finding("ERROR", f"{list_label}[{index}] {entry!r} triplet dimensions differ: {detail}"))
        width, height = dimensions[0][1], dimensions[0][2]
        if width < min_crop_size or height < min_crop_size:
            level = "ERROR" if is_training_entry else "WARN"
            findings.append(
                Finding(
                    level,
                    f"{list_label}[{index}] {entry!r} image size {width}x{height} is smaller than "
                    f"the {min_crop_size}x{min_crop_size} training crop",
                )
            )
    return findings


def print_findings(findings: Iterable[Finding]) -> Tuple[int, int]:
    error_count = 0
    warn_count = 0
    for finding in findings:
        print(finding)
        if finding.level == "ERROR":
            error_count += 1
        elif finding.level == "WARN":
            warn_count += 1
    return error_count, warn_count


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    findings: List[Finding] = []

    root = resolve_root(args.root, findings)
    sequences = root / "sequences"
    train_list_path = root / "tri_trainlist.txt"
    test_list_path = root / "tri_testlist.txt"

    print(f"Dataset root: {root}")
    print(f"Sequences dir: {sequences}")

    if args.sample_per_list < 0:
        findings.append(Finding("ERROR", "--sample-per-list must be non-negative"))
    if args.min_crop_size <= 0:
        findings.append(Finding("ERROR", "--min-crop-size must be positive"))
    if not root.exists():
        findings.append(Finding("ERROR", f"dataset root does not exist: {root}"))
    elif not root.is_dir():
        findings.append(Finding("ERROR", f"dataset root is not a directory: {root}"))
    if not sequences.exists():
        findings.append(Finding("ERROR", f"missing sequences directory: {sequences}"))
    elif not sequences.is_dir():
        findings.append(Finding("ERROR", f"sequences path is not a directory: {sequences}"))

    train_entries, train_findings = read_list_file(train_list_path, "tri_trainlist.txt")
    test_entries, test_findings = read_list_file(test_list_path, "tri_testlist.txt")
    findings.extend(train_findings)
    findings.extend(test_findings)

    split = int(len(train_entries) * 0.95)
    validation_count = len(train_entries) - split
    print(f"tri_trainlist entries: {len(train_entries)}")
    print(f"tri_testlist entries: {len(test_entries)}")
    print(f"VimeoDataset('train') entries: {split}")
    print(f"VimeoDataset('validation') entries: {validation_count}")

    if train_entries and split == 0:
        findings.append(Finding("ERROR", "95/5 split leaves zero training entries"))
    if train_entries and validation_count == 0:
        findings.append(Finding("WARN", "95/5 split leaves zero validation entries"))

    if sequences.exists() and sequences.is_dir():
        train_indices = select_indices(len(train_entries), args.sample_per_list, args.all, include_split=True)
        test_indices = select_indices(len(test_entries), args.sample_per_list, args.all, include_split=False)
        print(f"Checking tri_trainlist sequences: {len(train_indices)}")
        print(f"Checking tri_testlist sequences: {len(test_indices)}")
        for idx in train_indices:
            findings.extend(
                validate_sequence(
                    sequences,
                    "tri_trainlist.txt",
                    train_entries[idx],
                    idx,
                    args.skip_png_header,
                    args.min_crop_size,
                    is_training_entry=idx < split,
                )
            )
        for idx in test_indices:
            findings.extend(
                validate_sequence(
                    sequences,
                    "tri_testlist.txt",
                    test_entries[idx],
                    idx,
                    args.skip_png_header,
                    args.min_crop_size,
                    is_training_entry=False,
                )
            )

    errors, warnings = print_findings(findings)
    print(f"Summary: {errors} error(s), {warnings} warning(s)")
    if errors:
        print("FAIL: Vimeo triplet layout is not ready for ECCV2022-RIFE training preflight.")
        return 2
    print("OK: Vimeo triplet layout preflight passed for the checked entries.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
