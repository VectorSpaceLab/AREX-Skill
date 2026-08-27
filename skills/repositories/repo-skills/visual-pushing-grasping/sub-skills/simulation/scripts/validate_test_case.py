#!/usr/bin/env python3
"""Validate a VPG simulation preset without importing or starting a simulator.

The historical loader expects one mesh name and nine numeric values per line.
This tool checks that representation, finite values, normalized colors, an
optional exact object count, and optional mesh existence under a trusted root.
"""

from __future__ import annotations

import argparse
import math
from pathlib import Path
import sys
from typing import Iterable, List, Optional, Tuple


FIELD_COUNT = 10
COLOR_INDICES = range(1, 4)
POSE_INDICES = range(4, 10)


def positive_int(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be an integer") from exc
    if parsed <= 0:
        raise argparse.ArgumentTypeError("must be greater than zero")
    return parsed


def finite_number(token: str) -> Optional[float]:
    try:
        value = float(token)
    except ValueError:
        return None
    return value if math.isfinite(value) else None


def path_is_below(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def mesh_error(mesh_name: str, mesh_root: Path) -> Optional[str]:
    # A preset is data, not a request to escape the approved mesh directory.
    candidate = Path(mesh_name)
    if candidate.is_absolute() or ".." in candidate.parts:
        return "mesh path must be relative and contain no '..'"
    if candidate.suffix.lower() != ".obj":
        return "mesh name must have a .obj suffix"
    resolved = (mesh_root / candidate).resolve()
    if not path_is_below(resolved, mesh_root):
        return "mesh path resolves outside --mesh-dir"
    if not resolved.is_file():
        return "mesh file does not exist below --mesh-dir"
    return None


def validate(
    preset_file: Path,
    expected_count: Optional[int],
    mesh_dir: Optional[Path],
) -> Tuple[List[str], int]:
    errors: List[str] = []
    try:
        text = preset_file.read_text(encoding="utf-8")
    except OSError as exc:
        return [f"cannot read preset: {exc}"], 0
    except UnicodeError as exc:
        return [f"preset is not valid UTF-8 text: {exc}"], 0

    lines = text.splitlines()
    if not lines:
        errors.append("preset is empty")

    mesh_root: Optional[Path] = None
    if mesh_dir is not None:
        try:
            mesh_root = mesh_dir.resolve(strict=True)
        except OSError as exc:
            errors.append(f"cannot resolve --mesh-dir: {exc}")
        else:
            if not mesh_root.is_dir():
                errors.append("--mesh-dir is not a directory")

    object_count = 0
    for line_number, raw_line in enumerate(lines, start=1):
        if not raw_line.strip():
            errors.append(
                f"line {line_number}: blank lines are not source-compatible; "
                "remove the line"
            )
            continue
        fields = raw_line.split()
        object_count += 1
        if len(fields) != FIELD_COUNT:
            errors.append(
                f"line {line_number}: expected {FIELD_COUNT} fields, found {len(fields)}"
            )
            continue

        mesh_name = fields[0]
        if not mesh_name:
            errors.append(f"line {line_number}: mesh name is empty")
        elif mesh_root is not None:
            problem = mesh_error(mesh_name, mesh_root)
            if problem:
                errors.append(f"line {line_number}: {problem}: {mesh_name!r}")
        else:
            mesh_path = Path(mesh_name)
            if (
                mesh_path.is_absolute()
                or ".." in mesh_path.parts
                or mesh_path.suffix.lower() != ".obj"
            ):
                errors.append(
                    f"line {line_number}: mesh name must be a relative .obj path "
                    "without '..'"
                )

        for index in COLOR_INDICES:
            value = finite_number(fields[index])
            if value is None:
                errors.append(
                    f"line {line_number}: color field {index + 1} must be finite numeric data"
                )
            elif not 0.0 <= value <= 1.0:
                errors.append(
                    f"line {line_number}: color field {index + 1} must be in [0, 1]"
                )

        for index in POSE_INDICES:
            if finite_number(fields[index]) is None:
                errors.append(
                    f"line {line_number}: field {index + 1} must be finite numeric data"
                )

    if expected_count is not None and object_count != expected_count:
        errors.append(
            f"object count mismatch: found {object_count}, expected {expected_count}"
        )
    return errors, object_count


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Validate a VPG simulation preset without starting V-REP/CoppeliaSim. "
            "Each object line must contain one mesh name plus nine finite numbers."
        )
    )
    parser.add_argument("preset_file", type=Path, help="preset text file to validate")
    parser.add_argument(
        "--expected-object-count",
        type=positive_int,
        help="require exactly this many object lines (normally the --num_obj value)",
    )
    parser.add_argument(
        "--mesh-dir",
        type=Path,
        help="optional trusted mesh root; verify every referenced .obj exists below it",
    )
    return parser


def main(argv: Optional[Iterable[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    errors, count = validate(args.preset_file, args.expected_object_count, args.mesh_dir)
    if errors:
        print(f"INVALID {args.preset_file}: {len(errors)} error(s)", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    mesh_note = "; mesh names checked" if args.mesh_dir is not None else "; mesh existence not checked"
    expected_note = (
        f"; expected count {args.expected_object_count}"
        if args.expected_object_count is not None
        else ""
    )
    print(f"VALID {args.preset_file}: {count} object line(s){expected_note}{mesh_note}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
