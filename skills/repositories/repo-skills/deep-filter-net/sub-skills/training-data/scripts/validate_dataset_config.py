#!/usr/bin/env python3
"""Validate a DeepFilterNet dataset.cfg JSON file.

This helper is intentionally self-contained. It validates the JSON split schema,
row shapes, sampling factors, referenced HDF5 paths relative to --data-dir, and
optionally HDF5 groups/attributes when h5py is installed.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Set, Tuple

REQUIRED_SPLITS: Tuple[str, ...] = ("train", "valid", "test")
TRAINING_GROUPS: Set[str] = {"speech", "noise", "rir"}
KNOWN_GROUPS: Set[str] = TRAINING_GROUPS | {"noisy"}
KNOWN_CODECS: Set[str] = {"pcm", "flac", "vorbis"}
KNOWN_DTYPES: Set[str] = {"int16", "float32"}


@dataclass
class Reporter:
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def error(self, message: str) -> None:
        self.errors.append(message)

    def warn(self, message: str) -> None:
        self.warnings.append(message)

    def ok(self) -> bool:
        return not self.errors

    def print(self) -> None:
        for warning in self.warnings:
            print(f"WARNING: {warning}", file=sys.stderr)
        for error in self.errors:
            print(f"ERROR: {error}", file=sys.stderr)


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config",
        required=True,
        type=Path,
        help="Path to dataset.cfg JSON file.",
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=Path("."),
        help="Directory that HDF5 filenames in the config are relative to (default: current directory).",
    )
    parser.add_argument(
        "--require-files",
        action="store_true",
        help="Fail when a referenced HDF5 file is missing. Without this flag, missing files are warnings.",
    )
    parser.add_argument(
        "--check-hdf5",
        action="store_true",
        help="Open existing HDF5 files with h5py and check groups, attrs, sample counts, and split coverage.",
    )
    parser.add_argument(
        "--allow-absolute",
        action="store_true",
        help="Allow absolute HDF5 filenames in the JSON config. Relative paths are recommended.",
    )
    parser.add_argument(
        "--strict-two-column",
        action="store_true",
        help="Require every row to be exactly [filename, sampling_factor]. By default source-compatible optional fields are warned about but allowed.",
    )
    return parser.parse_args(argv)


def load_json(path: Path, reporter: Reporter) -> Any:
    if not path.is_file():
        reporter.error(f"Config file not found: {path}")
        return None
    try:
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except json.JSONDecodeError as exc:
        reporter.error(f"Invalid JSON in {path}: line {exc.lineno} column {exc.colno}: {exc.msg}")
    except OSError as exc:
        reporter.error(f"Could not read {path}: {exc}")
    return None


def is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def normalize_row(
    split: str,
    index: int,
    row: Any,
    args: argparse.Namespace,
    reporter: Reporter,
) -> Optional[Tuple[str, float, Path]]:
    prefix = f"{split}[{index}]"
    if not isinstance(row, list):
        reporter.error(f"{prefix}: row must be a JSON array [filename, sampling_factor]")
        return None
    if args.strict_two_column and len(row) != 2:
        reporter.error(f"{prefix}: row must contain exactly 2 items, got {len(row)}")
        return None
    if len(row) < 2:
        reporter.error(f"{prefix}: row must contain at least filename and sampling_factor")
        return None
    if len(row) > 6:
        reporter.error(f"{prefix}: row has {len(row)} items; expected 2 portable fields or at most 6 source-compatible fields")
        return None
    if len(row) > 2:
        reporter.warn(
            f"{prefix}: row has optional advanced fields beyond [filename, sampling_factor]; "
            "keep two-column rows unless fallbacks/key caches are intentional"
        )

    filename = row[0]
    if not isinstance(filename, str) or not filename.strip():
        reporter.error(f"{prefix}: filename must be a non-empty string")
        return None
    filename = filename.strip()
    file_path = Path(filename)
    if file_path.is_absolute() and not args.allow_absolute:
        reporter.error(f"{prefix}: filename is absolute; use a path relative to --data-dir or pass --allow-absolute")
        return None
    if any(part == ".." for part in file_path.parts):
        reporter.warn(f"{prefix}: filename contains '..'; keep dataset configs portable and scoped to --data-dir")
    if not filename.lower().endswith((".hdf5", ".h5")):
        reporter.warn(f"{prefix}: filename does not end with .hdf5 or .h5: {filename}")

    factor = row[1]
    if not is_number(factor):
        reporter.error(f"{prefix}: sampling_factor must be a JSON number, got {type(factor).__name__}")
        return None
    factor_float = float(factor)
    if not math.isfinite(factor_float) or factor_float <= 0:
        reporter.error(f"{prefix}: sampling_factor must be finite and > 0, got {factor!r}")
        return None

    resolved = file_path if file_path.is_absolute() else args.data_dir / file_path
    return filename, factor_float, resolved


def validate_schema(data: Any, args: argparse.Namespace, reporter: Reporter) -> Dict[str, List[Tuple[str, float, Path]]]:
    rows_by_split: Dict[str, List[Tuple[str, float, Path]]] = {split: [] for split in REQUIRED_SPLITS}
    if not isinstance(data, dict):
        reporter.error("Config root must be a JSON object with train/valid/test keys")
        return rows_by_split

    extra = sorted(set(data) - set(REQUIRED_SPLITS))
    if extra:
        reporter.warn(f"Unexpected top-level keys ignored by the standard training dataloader: {', '.join(extra)}")

    for split in REQUIRED_SPLITS:
        value = data.get(split)
        if value is None:
            reporter.error(f"Missing required split: {split}")
            continue
        if not isinstance(value, list):
            reporter.error(f"Split {split!r} must be a list of [filename, sampling_factor] rows")
            continue
        if not value:
            reporter.error(f"Split {split!r} is empty")
            continue
        for index, row in enumerate(value):
            normalized = normalize_row(split, index, row, args, reporter)
            if normalized is not None:
                rows_by_split[split].append(normalized)
    return rows_by_split


def check_files(rows_by_split: Dict[str, List[Tuple[str, float, Path]]], args: argparse.Namespace, reporter: Reporter) -> None:
    seen: Set[Path] = set()
    for split, rows in rows_by_split.items():
        for filename, _factor, path in rows:
            # Avoid duplicate messages for the same resolved file while still preserving split context.
            if path in seen:
                continue
            seen.add(path)
            if not path.is_file():
                msg = f"{split}: referenced HDF5 file not found under --data-dir: {filename} -> {path}"
                if args.require_files:
                    reporter.error(msg)
                else:
                    reporter.warn(msg)


def import_h5py(reporter: Reporter):
    try:
        import h5py  # type: ignore

        return h5py
    except Exception as exc:  # pragma: no cover - depends on caller environment
        reporter.warn(f"--check-hdf5 requested but h5py is unavailable ({type(exc).__name__}: {exc}); skipping HDF5 internals")
        return None


def scalar_attr(attrs: Any, name: str) -> Any:
    value = attrs.get(name)
    # h5py may return bytes or numpy scalars; normalize common cases for checks.
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    try:
        if hasattr(value, "item"):
            return value.item()
    except Exception:
        pass
    return value


def first_sample_attrs(group: Any) -> Tuple[Optional[str], Dict[str, Any], Optional[Tuple[int, ...]], Optional[str]]:
    try:
        first_key = next(iter(group.keys()))
    except StopIteration:
        return None, {}, None, None
    ds = group[first_key]
    dtype = str(getattr(ds, "dtype", "")) or None
    shape = tuple(int(x) for x in getattr(ds, "shape", ()))
    attrs = {name: scalar_attr(ds.attrs, name) for name in ds.attrs.keys()}
    return first_key, attrs, shape, dtype


def inspect_hdf5_file(path: Path, h5py: Any, reporter: Reporter) -> Set[str]:
    groups_found: Set[str] = set()
    try:
        with h5py.File(path, "r") as handle:
            raw_groups = list(handle.keys())
            lower_to_raw = {g.lower(): g for g in raw_groups}
            groups_found = set(lower_to_raw) & KNOWN_GROUPS
            if not groups_found:
                reporter.error(f"{path}: no recognized top-level group; expected one of {sorted(KNOWN_GROUPS)}")
            unrecognized = sorted(set(lower_to_raw) - KNOWN_GROUPS)
            if unrecognized:
                reporter.warn(f"{path}: unrecognized top-level groups present: {', '.join(unrecognized)}")

            codec = scalar_attr(handle.attrs, "codec")
            if codec is None:
                reporter.warn(f"{path}: missing file attr 'codec' (readers may assume pcm)")
            else:
                codec_s = str(codec).lower()
                if codec_s not in KNOWN_CODECS:
                    reporter.error(f"{path}: unsupported codec attr {codec!r}; expected one of {sorted(KNOWN_CODECS)}")

            dtype = scalar_attr(handle.attrs, "dtype")
            if dtype is None:
                reporter.warn(f"{path}: missing file attr 'dtype'")
            elif str(dtype).lower() not in KNOWN_DTYPES:
                reporter.error(f"{path}: unsupported dtype attr {dtype!r}; expected one of {sorted(KNOWN_DTYPES)}")

            sr = scalar_attr(handle.attrs, "sr")
            if sr is None:
                reporter.warn(f"{path}: missing file attr 'sr'")
            else:
                try:
                    sr_i = int(sr)
                    if sr_i <= 0:
                        reporter.error(f"{path}: sr must be positive, got {sr!r}")
                    elif sr_i != 48000:
                        reporter.warn(f"{path}: sr is {sr_i}; DeepFilterNet defaults are usually 48000")
                except Exception:
                    reporter.error(f"{path}: sr attr is not an integer: {sr!r}")

            max_freq = scalar_attr(handle.attrs, "max_freq")
            if max_freq is None:
                reporter.warn(f"{path}: missing file attr 'max_freq'")
            else:
                try:
                    if int(max_freq) <= 0:
                        reporter.error(f"{path}: max_freq must be positive, got {max_freq!r}")
                except Exception:
                    reporter.error(f"{path}: max_freq attr is not an integer: {max_freq!r}")

            for group_lower in sorted(groups_found):
                group = handle[lower_to_raw[group_lower]]
                n = len(group)
                if n <= 0:
                    reporter.error(f"{path}: group {group_lower!r} has no samples")
                    continue
                first_key, sample_attrs, shape, sample_dtype = first_sample_attrs(group)
                if first_key is None:
                    reporter.error(f"{path}: group {group_lower!r} has no readable sample keys")
                    continue
                if "n_samples" not in sample_attrs:
                    reporter.warn(f"{path}: first sample {first_key!r} in group {group_lower!r} lacks n_samples attr")
                else:
                    try:
                        n_samples = int(sample_attrs["n_samples"])
                        if n_samples <= 0:
                            reporter.error(f"{path}: first sample {first_key!r} has non-positive n_samples={n_samples}")
                    except Exception:
                        reporter.warn(f"{path}: first sample {first_key!r} has non-scalar n_samples={sample_attrs['n_samples']!r}")
                if shape is not None:
                    if len(shape) == 0:
                        reporter.error(f"{path}: first sample {first_key!r} has scalar dataset shape")
                    if (str(codec).lower() if codec is not None else "pcm") == "pcm" and len(shape) >= 2 and shape[0] > 16:
                        reporter.error(f"{path}: first PCM sample {first_key!r} appears to have >16 channels: shape={shape}")
                if sample_dtype:
                    if (str(codec).lower() if codec is not None else "pcm") in {"flac", "vorbis"} and "uint8" not in sample_dtype:
                        reporter.warn(f"{path}: encoded sample {first_key!r} dtype is {sample_dtype}, expected uint8-like bytes")
    except OSError as exc:
        reporter.error(f"{path}: could not open HDF5 file: {exc}")
    except Exception as exc:
        reporter.error(f"{path}: HDF5 inspection failed: {type(exc).__name__}: {exc}")
    return groups_found


def check_hdf5(rows_by_split: Dict[str, List[Tuple[str, float, Path]]], args: argparse.Namespace, reporter: Reporter) -> None:
    h5py = import_h5py(reporter)
    if h5py is None:
        return

    groups_cache: Dict[Path, Set[str]] = {}
    for rows in rows_by_split.values():
        for _filename, _factor, path in rows:
            if path in groups_cache:
                continue
            if not path.is_file():
                continue
            groups_cache[path] = inspect_hdf5_file(path, h5py, reporter)

    for split, rows in rows_by_split.items():
        split_groups: Set[str] = set()
        for _filename, _factor, path in rows:
            split_groups.update(groups_cache.get(path, set()))
        if rows and "speech" not in split_groups:
            reporter.error(f"{split}: no HDF5 with recognized 'speech' group found")
        if rows and "noise" not in split_groups:
            reporter.error(f"{split}: no HDF5 with recognized 'noise' group found")
        if "noisy" in split_groups:
            reporter.warn(f"{split}: 'noisy' HDF5 group is present; standard training still requires speech and noise groups")


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    reporter = Reporter()
    data = load_json(args.config, reporter)
    rows_by_split: Dict[str, List[Tuple[str, float, Path]]] = {split: [] for split in REQUIRED_SPLITS}
    if data is not None:
        rows_by_split = validate_schema(data, args, reporter)
        check_files(rows_by_split, args, reporter)
        if args.check_hdf5:
            check_hdf5(rows_by_split, args, reporter)

    reporter.print()
    n_rows = sum(len(rows) for rows in rows_by_split.values())
    if reporter.ok():
        print(f"OK: {args.config} has {n_rows} dataset row(s) across train/valid/test")
        return 0
    print(f"FAILED: {args.config} has {len(reporter.errors)} error(s) and {len(reporter.warnings)} warning(s)", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
