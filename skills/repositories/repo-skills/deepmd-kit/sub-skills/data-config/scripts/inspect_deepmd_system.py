#!/usr/bin/env python3
"""Inspect a DeePMD-kit NumPy-format system directory.

The script is intentionally standalone and read-only. It does not import
``deepmd`` and can run before DeePMD-kit is installed. If NumPy is unavailable it
still checks the directory tree and raw text metadata, but shape checks for
``.npy`` files are reported as skipped warnings.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

try:
    import numpy as np
except Exception:  # pragma: no cover - intentionally supports no-numpy hosts
    np = None  # type: ignore[assignment]


ATOMIC_NDOF = {
    "coord": 3,
    "force": 3,
    "atom_ener": 1,
    "atom_pref": 1,
    "dipole": 3,
    "atomic_dipole": 3,
    "polarizability": 9,
    "atomic_polarizability": 9,
    "spin": 3,
    "force_mag": 3,
    "efield": 3,
}
GLOBAL_NDOF = {
    "box": 9,
    "energy": 1,
    "virial": 9,
    "dipole": 3,
    "polarizability": 9,
}
SPECIAL_LABELS = {
    "hessian",
    "dos",
    "atom_dos",
    "real_atom_types",
    "fparam",
    "aparam",
    "numb_copy",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Read-only preflight inspection for a DeePMD-kit NumPy system "
            "directory containing type.raw and set.* subdirectories."
        )
    )
    parser.add_argument("system", type=Path, help="Path to a DeePMD NumPy system directory")
    parser.add_argument(
        "--expect-type-map",
        nargs="+",
        default=None,
        metavar="TYPE",
        help="Optional model type_map order to compare against type_map.raw",
    )
    parser.add_argument(
        "--max-sets",
        type=int,
        default=None,
        help="Inspect at most this many set.* directories after sorting",
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print JSON output with indentation",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit non-zero when warnings are emitted",
    )
    return parser.parse_args()


def warning(summary: dict[str, Any], message: str) -> None:
    summary.setdefault("warnings", []).append(message)


def read_ints(path: Path, summary: dict[str, Any]) -> list[int] | None:
    if not path.exists():
        warning(summary, "missing required type.raw")
        return None
    try:
        text = path.read_text(encoding="utf-8").strip()
    except UnicodeDecodeError:
        text = path.read_text().strip()
    if not text:
        warning(summary, "type.raw is empty")
        return []
    values: list[int] = []
    for token in text.split():
        try:
            values.append(int(token))
        except ValueError:
            warning(summary, f"type.raw contains non-integer token {token!r}")
            return None
    return values


def read_type_map(path: Path, summary: dict[str, Any]) -> list[str] | None:
    if not path.exists():
        return None
    try:
        values = path.read_text(encoding="utf-8").split()
    except UnicodeDecodeError:
        values = path.read_text().split()
    if not values:
        warning(summary, "type_map.raw exists but is empty")
    return values


def npy_shape(path: Path, summary: dict[str, Any]) -> tuple[int, ...] | None:
    if np is None:
        warning(summary, f"NumPy unavailable; skipped shape check for {path.as_posix()}")
        return None
    try:
        array = np.load(path, mmap_mode="r", allow_pickle=False)
    except Exception as exc:
        warning(summary, f"could not read {path.as_posix()}: {exc}")
        return None
    return tuple(int(dim) for dim in array.shape)


def raw_shape(path: Path, summary: dict[str, Any]) -> tuple[int, ...] | None:
    if np is None:
        warning(summary, f"NumPy unavailable; skipped raw text shape check for {path.as_posix()}")
        return None
    try:
        array = np.loadtxt(path, ndmin=2)
    except Exception as exc:
        warning(summary, f"could not read raw text file {path.as_posix()}: {exc}")
        return None
    return tuple(int(dim) for dim in array.shape)


def first_dim(shape: tuple[int, ...] | None) -> int | None:
    if not shape:
        return None
    return shape[0]


def flat_width(shape: tuple[int, ...] | None) -> int | None:
    if not shape:
        return None
    if len(shape) == 1:
        return 1
    width = 1
    for dim in shape[1:]:
        width *= dim
    return width


def check_width(
    summary: dict[str, Any],
    rel_path: str,
    shape: tuple[int, ...] | None,
    expected_width: int,
    description: str,
) -> None:
    width = flat_width(shape)
    if width is None:
        return
    if width != expected_width:
        warning(
            summary,
            f"{rel_path} has flattened width {width}, expected {expected_width} for {description}",
        )


def classify_label(stem: str) -> str:
    if stem in {"coord", "force", "atom_ener", "atom_pref", "spin", "force_mag", "efield"}:
        return "atomic"
    if stem in {"atomic_dipole", "atomic_polarizability"}:
        return "atomic"
    if stem in {"energy", "box", "virial", "dipole", "polarizability"}:
        return "global"
    if stem in SPECIAL_LABELS:
        return "special"
    return "unknown"


def inspect_set(
    set_dir: Path,
    system_dir: Path,
    natoms: int | None,
    pbc: bool,
    summary: dict[str, Any],
) -> dict[str, Any]:
    set_summary: dict[str, Any] = {
        "name": set_dir.name,
        "files": {},
        "nframes": None,
        "mixed_type": False,
    }
    npy_files = sorted(set_dir.glob("*.npy"))
    raw_files = sorted(set_dir.glob("*.raw"))
    if not npy_files and not raw_files:
        warning(summary, f"{set_dir.name} contains no .npy or .raw frame files")

    shapes: dict[str, tuple[int, ...] | None] = {}
    frame_counts: dict[str, int] = {}
    for file_path in [*npy_files, *raw_files]:
        stem = file_path.stem
        shape = npy_shape(file_path, summary) if file_path.suffix == ".npy" else raw_shape(file_path, summary)
        shapes[stem] = shape
        rel = file_path.relative_to(system_dir).as_posix()
        set_summary["files"][stem] = {
            "path": rel,
            "shape": list(shape) if shape is not None else None,
            "kind": classify_label(stem),
            "storage": file_path.suffix.lstrip("."),
        }
        nframes = first_dim(shape)
        if nframes is not None:
            frame_counts[stem] = nframes
        if file_path.suffix == ".raw":
            warning(summary, f"{rel} is a raw text frame file; convert raw data to NumPy/HDF5 before training")

    if "coord" not in shapes:
        warning(summary, f"{set_dir.name} is missing required coord.npy")
    else:
        coord_frames = first_dim(shapes["coord"])
        set_summary["nframes"] = coord_frames
        if natoms is not None:
            check_width(
                summary,
                f"{set_dir.name}/coord.npy",
                shapes["coord"],
                natoms * 3,
                "Natoms * 3 coordinates",
            )

    if pbc:
        if "box" not in shapes:
            warning(summary, f"{set_dir.name} is periodic but missing box.npy")
        else:
            check_width(summary, f"{set_dir.name}/box.npy", shapes["box"], 9, "periodic box")
    elif "box" in shapes:
        warning(summary, f"{set_dir.name} has box.npy although root nopbc marks non-periodic data")

    if "real_atom_types" in shapes:
        set_summary["mixed_type"] = True
        if natoms is not None:
            check_width(
                summary,
                f"{set_dir.name}/real_atom_types.npy",
                shapes["real_atom_types"],
                natoms,
                "mixed-type per-frame atom types",
            )

    coord_frames = frame_counts.get("coord")
    if coord_frames is not None:
        for stem, count in sorted(frame_counts.items()):
            if count != coord_frames:
                warning(
                    summary,
                    f"{set_dir.name}/{stem}.npy has {count} frames but coord.npy has {coord_frames}",
                )

    if natoms is not None:
        for stem, shape in sorted(shapes.items()):
            rel = f"{set_dir.name}/{stem}.npy"
            if stem in {"force", "coord", "spin", "force_mag", "efield"}:
                check_width(summary, rel, shape, natoms * 3, f"{stem} atomic vector")
            elif stem in {"atom_ener", "atom_pref"}:
                check_width(summary, rel, shape, natoms, f"{stem} atomic scalar")
            elif stem == "atomic_dipole":
                check_width(summary, rel, shape, natoms * 3, "atomic dipole")
            elif stem == "atomic_polarizability":
                check_width(summary, rel, shape, natoms * 9, "atomic polarizability")
            elif stem in {"energy", "numb_copy"}:
                check_width(summary, rel, shape, 1, f"{stem} scalar")
            elif stem == "virial":
                check_width(summary, rel, shape, 9, "virial")
            elif stem == "dipole":
                width = flat_width(shape)
                if width not in {None, 3, natoms * 3}:
                    warning(summary, f"{rel} has flattened width {width}; expected 3 or Natoms * 3")
            elif stem == "polarizability":
                width = flat_width(shape)
                if width not in {None, 9, natoms * 9}:
                    warning(summary, f"{rel} has flattened width {width}; expected 9 or Natoms * 9")
            elif stem == "hessian":
                expected = natoms * 3 * natoms * 3
                check_width(summary, rel, shape, expected, "full Hessian")
            elif stem == "aparam":
                width = flat_width(shape)
                if width is not None and width % natoms != 0:
                    warning(summary, f"{rel} width {width} is not divisible by Natoms {natoms}")
            elif stem == "atom_dos":
                width = flat_width(shape)
                if width is not None and width % natoms != 0:
                    warning(summary, f"{rel} width {width} is not divisible by Natoms {natoms}")

    return set_summary


def inspect_root_raw_files(
    system_dir: Path,
    summary: dict[str, Any],
    natoms: int | None,
    pbc: bool,
) -> list[dict[str, Any]]:
    raw_summaries: list[dict[str, Any]] = []
    for file_path in sorted(system_dir.glob("*.raw")):
        if file_path.name in {"type.raw", "type_map.raw"}:
            continue
        stem = file_path.stem
        shape = raw_shape(file_path, summary)
        rel = file_path.relative_to(system_dir).as_posix()
        raw_summaries.append(
            {
                "path": rel,
                "shape": list(shape) if shape is not None else None,
                "kind": classify_label(stem),
                "storage": "raw",
            }
        )
        warning(summary, f"{rel} is raw text conversion input, not a directly trainable NumPy set file")
        if natoms is not None:
            if stem in {"coord", "force", "spin", "force_mag", "efield"}:
                check_width(summary, rel, shape, natoms * 3, f"{stem} atomic vector")
            elif stem in {"atom_ener", "atom_pref"}:
                check_width(summary, rel, shape, natoms, f"{stem} atomic scalar")
            elif stem == "box" and pbc:
                check_width(summary, rel, shape, 9, "periodic box")
            elif stem == "energy":
                check_width(summary, rel, shape, 1, "energy scalar")
            elif stem == "virial":
                check_width(summary, rel, shape, 9, "virial")
            elif stem == "hessian":
                expected = natoms * 3 * natoms * 3
                check_width(summary, rel, shape, expected, "full Hessian")
    return raw_summaries


def build_summary(args: argparse.Namespace) -> dict[str, Any]:
    system_dir = args.system
    summary: dict[str, Any] = {
        "system": str(system_dir),
        "format": "numpy-directory",
        "exists": system_dir.exists(),
        "is_dir": system_dir.is_dir(),
        "numpy_available": np is not None,
        "warnings": [],
    }

    if not system_dir.exists() or not system_dir.is_dir():
        warning(summary, "system path does not exist or is not a directory")
        return summary

    atom_types = read_ints(system_dir / "type.raw", summary)
    type_map = read_type_map(system_dir / "type_map.raw", summary)
    pbc = not (system_dir / "nopbc").exists()
    set_dirs = sorted(path for path in system_dir.glob("set.*") if path.is_dir())
    inspected_set_dirs = set_dirs[: args.max_sets] if args.max_sets is not None else set_dirs

    natoms = len(atom_types) if atom_types is not None else None
    root_raw_files = inspect_root_raw_files(system_dir, summary, natoms, pbc)
    summary.update(
        {
            "natoms": natoms,
            "atom_type_min": min(atom_types) if atom_types else None,
            "atom_type_max": max(atom_types) if atom_types else None,
            "unique_atom_types": sorted(set(atom_types)) if atom_types else [],
            "type_map": type_map,
            "expected_type_map": args.expect_type_map,
            "pbc": pbc,
            "has_nopbc": not pbc,
            "root_raw_frame_files": root_raw_files,
            "set_count_total": len(set_dirs),
            "set_count_inspected": len(inspected_set_dirs),
            "sets": [],
        }
    )

    if not set_dirs:
        warning(summary, "no set.* directories found")

    if atom_types is not None:
        if any(value < 0 for value in atom_types):
            warning(summary, "type.raw contains negative ids; virtual atoms belong in real_atom_types.npy, not type.raw")
        if type_map is not None and atom_types and max(atom_types) >= len(type_map):
            warning(summary, "type_map.raw has fewer names than max(type.raw) + 1")

    if args.expect_type_map is not None:
        if type_map is None:
            warning(summary, "--expect-type-map was provided but type_map.raw is missing")
        else:
            missing = [name for name in type_map if name not in args.expect_type_map]
            if missing:
                warning(summary, f"type_map.raw names missing from expected model type_map: {missing}")
            if type_map != args.expect_type_map:
                summary["type_map_order_differs_from_expected"] = True

    mixed_modes: list[bool] = []
    for set_dir in inspected_set_dirs:
        set_summary = inspect_set(set_dir, system_dir, natoms, pbc, summary)
        mixed_modes.append(bool(set_summary["mixed_type"]))
        summary["sets"].append(set_summary)

    if mixed_modes:
        summary["mixed_type"] = all(mixed_modes)
        if any(mixed_modes) and not all(mixed_modes):
            warning(summary, "some inspected sets are mixed_type and others are standard")
        if any(mixed_modes) and type_map is None:
            warning(summary, "mixed_type data requires type_map.raw")
    else:
        summary["mixed_type"] = False

    label_stems = sorted(
        {
            stem
            for set_info in summary["sets"]
            for stem in set_info.get("files", {})
            if stem not in {"coord", "box", "real_atom_types"}
        }
    )
    summary["labels_detected"] = label_stems

    if "virial" in label_stems and not pbc:
        warning(summary, "virial labels detected in a nopbc system; verify loss/test expectations")
    if "hessian" in label_stems and "force" not in label_stems:
        warning(summary, "hessian labels detected without force labels; verify Hessian training target")
    if args.max_sets is not None and len(set_dirs) > len(inspected_set_dirs):
        warning(summary, f"only inspected {len(inspected_set_dirs)} of {len(set_dirs)} set.* directories")

    summary["ok"] = not summary["warnings"]
    return summary


def main() -> int:
    args = parse_args()
    summary = build_summary(args)
    indent = 2 if args.pretty else None
    print(json.dumps(summary, indent=indent, sort_keys=True))
    if args.strict and summary.get("warnings"):
        return 1
    if not summary.get("exists") or not summary.get("is_dir"):
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
