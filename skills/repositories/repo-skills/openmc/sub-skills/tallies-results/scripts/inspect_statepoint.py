#!/usr/bin/env python3
"""Inspect explicit OpenMC HDF5 output metadata without running transport."""
from __future__ import annotations

import argparse
from pathlib import Path
import sys
from typing import Any


def _text(value: Any) -> str:
    """Render common HDF5 scalar/array values without assuming a string type."""
    if hasattr(value, "tolist"):
        value = value.tolist()
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    if isinstance(value, (list, tuple)):
        return "[" + ", ".join(_text(item) for item in value) + "]"
    return str(value)


def _scalar(group: Any, name: str) -> str | None:
    """Return a dataset scalar or attribute as text, or ``None`` if absent."""
    try:
        if name in group:
            return _text(group[name][()])
        if name in group.attrs:
            return _text(group.attrs[name])
    except Exception as exc:  # diagnostic tool: continue with other metadata
        return f"<unreadable: {exc}>"
    return None


def _kind(obj: Any) -> str:
    """Identify an HDF5 group or dataset without relying on private APIs."""
    try:
        import h5py
    except ImportError:  # handled by the caller before any HDF5 work
        return "object"
    if isinstance(obj, h5py.Group):
        return "group"
    if isinstance(obj, h5py.Dataset):
        return "dataset"
    return type(obj).__name__


def _print_group_summary(h5: Any) -> None:
    print("root groups/datasets:")
    for key in sorted(h5.keys()):
        try:
            obj = h5[key]
            shape = getattr(obj, "shape", None)
            suffix = f" shape={shape}" if shape is not None else ""
            print(f"  {key}: {_kind(obj)}{suffix}")
        except Exception as exc:
            print(f"  {key}: <unreadable: {exc}>")


def _print_tallies(h5: Any) -> None:
    if "tallies" not in h5:
        print("tallies: absent")
        return

    group = h5["tallies"]
    print("tallies:")
    for name in ("n_tallies", "ids"):
        value = _scalar(group, name)
        if value is not None:
            print(f"  {name}: {value}")

    for key in sorted(group.keys()):
        if not key.startswith("tally "):
            continue
        tally = group[key]
        print(f"  {key}:")
        for name in (
            "name",
            "n_realizations",
            "n_filters",
            "filters",
            "nuclides",
            "n_score_bins",
            "score_bins",
            "estimator",
        ):
            value = _scalar(tally, name)
            if value is not None:
                print(f"    {name}: {value}")
        if "results" in tally:
            print(f"    results: dataset shape={tally['results'].shape}")
        for name in ("multiply_density", "higher_moments", "internal"):
            value = _scalar(tally, name)
            if value is not None:
                print(f"    {name}: {value}")


def inspect(path: Path, require_statepoint: bool = False) -> int:
    """Inspect one explicit path and return a stable diagnostic exit code."""
    if not path.exists():
        print(f"error: input file does not exist: {path}", file=sys.stderr)
        return 2
    if not path.is_file():
        print(f"error: input path is not a regular file: {path}", file=sys.stderr)
        return 2

    try:
        import h5py
    except ImportError:
        print("error: h5py is required to inspect HDF5 files", file=sys.stderr)
        return 4

    try:
        h5 = h5py.File(path, "r")
    except (OSError, ValueError) as exc:
        print(f"error: cannot read HDF5 file {path}: {exc}", file=sys.stderr)
        print(
            "hint: check permissions, truncation, and that the path is HDF5",
            file=sys.stderr,
        )
        return 3

    with h5:
        print(f"file: {path}")
        filetype = _scalar(h5, "filetype")
        version = _scalar(h5, "version")
        print(f"filetype: {filetype or '<missing>'}")
        print(f"format version: {version or '<missing>'}")
        for name in (
            "openmc_version",
            "git_sha1",
            "date_and_time",
            "path",
            "tallies_present",
            "source_present",
        ):
            value = _scalar(h5, name)
            if value is not None:
                print(f"{name}: {value}")
        _print_group_summary(h5)
        _print_tallies(h5)

        if require_statepoint and filetype != "statepoint":
            print(
                "error: filetype is not 'statepoint'; use the matching reader "
                "or omit --require-statepoint",
                file=sys.stderr,
            )
            return 5
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Print explicit OpenMC HDF5 metadata and tally layout without "
            "running OpenMC or searching for files."
        )
    )
    parser.add_argument(
        "path",
        type=Path,
        help="explicit statepoint or other OpenMC HDF5 file path",
    )
    parser.add_argument(
        "--require-statepoint",
        action="store_true",
        help="return an error unless the root filetype is statepoint",
    )
    args = parser.parse_args(argv)
    return inspect(args.path, args.require_statepoint)


if __name__ == "__main__":
    raise SystemExit(main())
