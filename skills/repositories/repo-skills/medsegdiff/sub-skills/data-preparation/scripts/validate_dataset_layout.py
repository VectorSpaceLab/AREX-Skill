#!/usr/bin/env python3
"""Offline, deterministic checks for MedSegDiff dataset layouts.

This helper checks filenames, pair counts, CSV targets, and (when nibabel is
installed) NIfTI headers. It deliberately does not import the project loaders,
open a network connection, modify data, or claim to replace a one-item loader
smoke test.
"""

from __future__ import annotations

import argparse
import csv
import struct
import sys
from pathlib import Path
from typing import Iterable, List, Optional, Sequence, Tuple


EXPECTED_BRATS = ("t1", "t1ce", "t2", "flair", "seg")
TEST_BRATS = ("t1", "t1ce", "t2", "flair")
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


class Report:
    def __init__(self, max_errors: int = 50) -> None:
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.max_errors = max_errors

    def error(self, message: str) -> None:
        if len(self.errors) < self.max_errors:
            self.errors.append(message)
        elif len(self.errors) == self.max_errors:
            self.errors.append(
                f"additional errors suppressed (limit={self.max_errors}); fix the earlier errors first"
            )

    def warning(self, message: str) -> None:
        self.warnings.append(message)

    def finish(self) -> int:
        for message in self.errors:
            print(f"ERROR: {message}", file=sys.stderr)
        for message in self.warnings:
            print(f"WARNING: {message}", file=sys.stderr)
        if self.errors:
            print(
                f"layout validation failed: {len(self.errors)} error(s), "
                f"{len(self.warnings)} warning(s)",
                file=sys.stderr,
            )
            return 1
        print(f"layout validation passed ({len(self.warnings)} warning(s))")
        return 0


def is_nifti(path: Path) -> bool:
    return path.name.endswith(".nii") or path.name.endswith(".nii.gz")


def png_size(path: Path) -> Tuple[int, int]:
    """Read only the PNG signature/IHDR; no image library or network needed."""
    try:
        with path.open("rb") as handle:
            signature = handle.read(8)
            if signature != PNG_SIGNATURE:
                raise ValueError("missing PNG signature")
            header = handle.read(8)
            if len(header) != 8:
                raise ValueError("truncated PNG chunk header")
            length, chunk_type = struct.unpack(">I4s", header)
            if chunk_type != b"IHDR" or length < 8:
                raise ValueError("first PNG chunk is not a valid IHDR")
            payload = handle.read(length)
            if len(payload) < 8:
                raise ValueError("truncated PNG IHDR")
            width, height = struct.unpack(">II", payload[:8])
            if width == 0 or height == 0:
                raise ValueError("PNG has zero width or height")
            return width, height
    except OSError as exc:
        raise ValueError(str(exc)) from exc


def direct_files(directory: Path, suffix: str) -> List[Path]:
    return sorted(
        path for path in directory.glob(f"*{suffix}") if path.is_file()
    )


def validate_custom2d(root: Path, report: Report) -> None:
    images_dir = root / "images"
    masks_dir = root / "masks"
    if not images_dir.is_dir():
        report.error(f"missing directory {images_dir}; expected DATA_ROOT/images/*.png")
    if not masks_dir.is_dir():
        report.error(f"missing directory {masks_dir}; expected DATA_ROOT/masks/*.png")
    if not images_dir.is_dir() or not masks_dir.is_dir():
        return

    images = direct_files(images_dir, ".png")
    masks = direct_files(masks_dir, ".png")
    if not images:
        report.error(f"no lowercase .png files found in {images_dir}")
    if not masks:
        report.error(f"no lowercase .png files found in {masks_dir}")
    if len(images) != len(masks):
        report.error(
            f"image/mask count mismatch: {len(images)} images versus {len(masks)} masks; "
            "CustomDataset pairs independently sorted lists by position"
        )

    image_stems = {path.stem for path in images}
    mask_stems = {path.stem for path in masks}
    missing_masks = sorted(image_stems - mask_stems)
    missing_images = sorted(mask_stems - image_stems)
    if missing_masks:
        report.error("missing masks for image stems: " + ", ".join(missing_masks[:10]))
    if missing_images:
        report.error("missing images for mask stems: " + ", ".join(missing_images[:10]))

    image_sizes = {}
    for path in images + masks:
        try:
            image_sizes[path] = png_size(path)
        except ValueError as exc:
            report.error(f"cannot read PNG header {path}: {exc}")
    for image in images:
        mask = masks_dir / image.name
        if mask.exists() and image in image_sizes and mask in image_sizes:
            if image_sizes[image] != image_sizes[mask]:
                report.error(
                    f"shape mismatch for {image.name}: image {image_sizes[image]} versus "
                    f"mask {image_sizes[mask]}; choose an explicit mask-safe resize policy"
                )

    other_image_files = sorted(
        path for path in images_dir.iterdir() if path.is_file() and path.suffix != ".png"
    )
    other_mask_files = sorted(
        path for path in masks_dir.iterdir() if path.is_file() and path.suffix != ".png"
    )
    if other_image_files or other_mask_files:
        report.warning(
            "non-.png files are ignored by the source CustomDataset glob; remove or isolate them "
            "if they are intended as cases"
        )


def read_csv_rows(path: Path, report: Report) -> Optional[List[Sequence[str]]]:
    encodings = ("utf-8-sig", "gbk")
    last_error: Optional[Exception] = None
    for encoding in encodings:
        try:
            with path.open("r", encoding=encoding, newline="") as handle:
                return list(csv.reader(handle))
        except (OSError, UnicodeError, csv.Error) as exc:
            last_error = exc
    report.error(f"cannot parse CSV {path}: {last_error}")
    return None


def isic_csv_candidates(root: Path, mode: str) -> Tuple[Path, List[Path]]:
    part = "Training" if mode == "train" else "Test"
    source = root / f"ISBI2016_ISIC_Part3B_{part}_GroundTruth.csv"
    documented = root / f"ISBI2016_ISIC_Part1_{part}_GroundTruth.csv"
    return source, [documented]


def validate_isic(root: Path, mode: str, csv_override: Optional[Path], report: Report) -> None:
    if not root.is_dir():
        report.error(f"ISIC data path is not a directory: {root}")
        return
    source_csv, alternatives = isic_csv_candidates(root, mode)
    csv_path = csv_override if csv_override is not None else source_csv
    if not csv_path.is_absolute():
        csv_path = root / csv_path
    if not csv_path.is_file():
        found_alternatives = [path for path in alternatives if path.is_file()]
        if found_alternatives:
            report.error(
                f"source loader expects {source_csv.name}, but found {found_alternatives[0].name}; "
                "the README/checked-in Part1 layout needs an explicit filename or loader adaptation"
            )
            csv_path = found_alternatives[0]
        else:
            report.error(
                f"missing {source_csv.name} under {root}; pass --csv for a file to inspect, "
                "but remember the source constructor hard-codes the Part3B name"
            )
            return

    rows = read_csv_rows(csv_path, report)
    if rows is None:
        return
    if not rows:
        report.error(f"ISIC CSV is empty: {csv_path}")
        return
    data_rows = rows[1:] if len(rows[0]) >= 3 else rows
    if not data_rows:
        report.error(f"ISIC CSV has no data rows: {csv_path}")
        return
    bad_columns = [str(index + 1) for index, row in enumerate(data_rows) if len(row) < 3]
    if bad_columns:
        report.error(
            "ISIC CSV rows must have at least three columns because the source uses "
            f"iloc[:, 1] and iloc[:, 2]; short row numbers: {', '.join(bad_columns[:10])}"
        )
        return

    missing: List[str] = []
    for index, row in enumerate(data_rows, start=2):
        image_rel, mask_rel = row[1].strip(), row[2].strip()
        if not image_rel or not mask_rel:
            report.error(f"ISIC CSV row {index} has an empty image or mask path")
            continue
        image_path, mask_path = root / image_rel, root / mask_rel
        if not image_path.is_file():
            missing.append(f"row {index} image {image_path}")
        if not mask_path.is_file():
            missing.append(f"row {index} mask {mask_path}")
    if missing:
        report.error(
            "ISIC CSV references missing files: " + "; ".join(missing[:10])
        )
    if csv_override is not None:
        report.warning(
            "--csv changes only what this validator inspects; ISICDataset still uses its "
            "hard-coded Part3B filename"
        )
    print(f"checked ISIC {mode} CSV: {csv_path} ({len(data_rows)} data row(s))")


def leaf_case_dirs(root: Path) -> List[Path]:
    cases: List[Path] = []
    for directory in sorted(path for path in root.rglob("*") if path.is_dir()):
        if not any(child.is_dir() for child in directory.iterdir()):
            if any(is_nifti(child) for child in directory.iterdir() if child.is_file()):
                cases.append(directory)
    if any(is_nifti(child) for child in root.iterdir() if child.is_file()):
        cases.insert(0, root)
    return cases


def try_nifti_shape(path: Path) -> Optional[Tuple[int, ...]]:
    try:
        import nibabel as nib  # type: ignore
    except ImportError:
        return None
    image = nib.load(str(path))
    return tuple(int(value) for value in image.shape)


def validate_brats(root: Path, mode: str, report: Report) -> None:
    if not root.is_dir():
        report.error(f"BRATS data path is not a directory: {root}")
        return
    cases = leaf_case_dirs(root)
    if not cases:
        report.error(
            f"no leaf case directory containing .nii or .nii.gz files found under {root}; "
            "BRATSDataset scans leaf directories"
        )
        return

    required = set(TEST_BRATS if mode == "test" else EXPECTED_BRATS)
    all_shapes_available = True
    checked_cases = 0
    for case in cases:
        files = sorted(path for path in case.iterdir() if path.is_file())
        nifti_files = [path for path in files if is_nifti(path)]
        unrelated = [path for path in files if not is_nifti(path)]
        if unrelated:
            report.error(
                f"leaf {case} contains non-NIfTI files ({unrelated[0].name}); the source loops over all leaf files"
            )
        keys = {}
        for path in nifti_files:
            tokens = path.name.split("_")
            if len(tokens) <= 3:
                report.error(
                    f"malformed BRATS filename {path.name}: need underscore token index 3 "
                    "to be t1, t1ce, t2, flair, or seg"
                )
                continue
            key = tokens[3]
            if mode == "3d":
                key = key.split(".", 1)[0]
            if key in keys:
                report.error(f"duplicate BRATS modality {key!r} in {case}: {path.name} and {keys[key].name}")
            keys[key] = path
        actual = set(keys)
        if actual != required:
            missing = sorted(required - actual)
            extra = sorted(actual - required)
            detail = []
            if missing:
                detail.append("missing " + ", ".join(missing))
            if extra:
                detail.append("unexpected " + ", ".join(extra))
            report.error(
                f"BRATS leaf {case} modality set is {sorted(actual)!r}; "
                + "; ".join(detail)
                + ". Expected filenames with token index 3 = t1/t1ce/t2/flair"
                + ("/seg" if mode != "test" else "")
            )
            continue

        shapes = {}
        for key, path in sorted(keys.items()):
            try:
                shape = try_nifti_shape(path)
            except Exception as exc:  # nibabel decode errors are actionable data errors
                report.error(f"cannot read NIfTI header {path}: {exc}")
                continue
            if shape is None:
                all_shapes_available = False
                continue
            shapes[key] = shape
        if shapes:
            unique_shapes = set(shapes.values())
            if len(unique_shapes) != 1:
                report.error(f"BRATS case {case} has mismatched NIfTI shapes: {shapes}")
            for key, shape in shapes.items():
                if len(shape) < 3:
                    report.error(f"BRATS volume {case / keys[key]} is {shape}; loader indexes three axes")
                if mode == "3d" and len(shape) >= 3 and shape[2] < 155:
                    report.error(
                        f"BRATSDataset3D case {case} modality {key} has depth {shape[2]} but "
                        "the source always indexes slices 0..154"
                    )
        checked_cases += 1

    if not all_shapes_available:
        report.warning(
            "nibabel is unavailable; filename/modality checks ran, but NIfTI readability, shape, "
            "and fixed-depth checks were skipped"
        )
    print(f"checked BRATS {mode}: {checked_cases} leaf case(s)")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Validate common MedSegDiff dataset layouts offline. This checks layout only; "
            "it does not run the project loaders or download data."
        ),
        epilog=(
            "Examples: validate_dataset_layout.py ROOT --kind custom2d; "
            "validate_dataset_layout.py SPLIT --kind isic --mode train; "
            "validate_dataset_layout.py ROOT --kind brats --mode 3d"
        ),
    )
    parser.add_argument("root", type=Path, help="dataset root or ISIC split directory")
    parser.add_argument(
        "--kind",
        required=True,
        choices=("custom2d", "isic", "brats"),
        help="layout to validate",
    )
    parser.add_argument(
        "--mode",
        default="train",
        choices=("train", "test", "3d"),
        help=(
            "ISIC split or BRATS loader mode; BRATS 3d enforces the fixed 155-slice depth "
            "and otherwise requires seg"
        ),
    )
    parser.add_argument(
        "--csv",
        type=Path,
        help="optional ISIC CSV path (inspection override; does not change the loader's hard-coded name)",
    )
    parser.add_argument(
        "--max-errors",
        type=int,
        default=50,
        help="maximum individual errors to print (default: 50)",
    )
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.max_errors < 1:
        parser.error("--max-errors must be positive")
    report = Report(args.max_errors)
    root = args.root.expanduser()
    if args.kind == "custom2d":
        if args.mode != "train":
            parser.error("--mode is not used for custom2d; use --mode train or omit it")
        if args.csv:
            parser.error("--csv is only valid with --kind isic")
        validate_custom2d(root, report)
    elif args.kind == "isic":
        if args.mode == "3d":
            parser.error("ISIC supports --mode train or --mode test, not 3d")
        validate_isic(root, args.mode, args.csv, report)
    else:
        if args.csv:
            parser.error("--csv is only valid with --kind isic")
        validate_brats(root, args.mode, report)
    return report.finish()


if __name__ == "__main__":
    raise SystemExit(main())
