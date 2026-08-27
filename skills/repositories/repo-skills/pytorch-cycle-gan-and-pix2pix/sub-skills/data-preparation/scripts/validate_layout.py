#!/usr/bin/env python3
"""Validate standard pytorch-CycleGAN-and-pix2pix dataset layouts.

The script is intentionally self-contained: it imports no repository modules,
performs no network access, and only reads the paths supplied on the command
line.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

IMG_EXTENSIONS: Tuple[str, ...] = (
    ".jpg", ".JPG", ".jpeg", ".JPEG", ".png", ".PNG", ".ppm", ".PPM",
    ".bmp", ".BMP", ".tif", ".TIF", ".tiff", ".TIFF",
)
STANDARD_PHASES: Tuple[str, ...] = ("train", "test", "val")


def is_image_file(path: Path) -> bool:
    return path.is_file() and path.name.endswith(IMG_EXTENSIONS)


def iter_files(directory: Path, recursive: bool) -> Iterable[Path]:
    if recursive:
        yield from directory.rglob("*")
    else:
        yield from directory.iterdir()


def list_images(directory: Path, recursive: bool) -> List[Path]:
    return sorted(path for path in iter_files(directory, recursive) if is_image_file(path))


def list_unsupported_files(directory: Path, recursive: bool, limit: int = 8) -> List[str]:
    examples: List[str] = []
    for path in iter_files(directory, recursive):
        if path.is_file() and not is_image_file(path):
            try:
                examples.append(str(path.relative_to(directory)))
            except ValueError:
                examples.append(str(path))
            if len(examples) >= limit:
                break
    return examples


def phase_exists(root: Path, mode: str, phase: str) -> bool:
    if mode == "unaligned":
        return (root / f"{phase}A").exists() or (root / f"{phase}B").exists()
    return (root / phase).exists()


def resolve_phases(root: Path, mode: str, phase: str) -> List[Optional[str]]:
    if mode == "single":
        return [None]
    if phase != "auto":
        return [phase]
    existing = [candidate for candidate in STANDARD_PHASES if phase_exists(root, mode, candidate)]
    return existing if existing else ["train"]


def verify_openable(images: List[Path], max_open: int) -> List[str]:
    try:
        from PIL import Image
    except Exception as exc:  # pragma: no cover - depends on runtime deps
        return [f"Pillow import failed while --check-open was requested: {exc}"]

    problems: List[str] = []
    for image_path in images[:max_open]:
        try:
            with Image.open(image_path) as image:
                image.verify()
        except Exception as exc:  # Pillow reports format-specific exceptions.
            problems.append(f"{image_path}: cannot be opened as an image ({exc})")
    return problems


def check_aligned_widths(images: List[Path], max_open: int) -> List[str]:
    try:
        from PIL import Image
    except Exception as exc:  # pragma: no cover - depends on runtime deps
        return [f"Pillow import failed while --check-aligned-width was requested: {exc}"]

    warnings: List[str] = []
    for image_path in images[:max_open]:
        try:
            with Image.open(image_path) as image:
                width, height = image.size
        except Exception as exc:
            warnings.append(f"{image_path}: cannot inspect dimensions ({exc})")
            continue
        if width < 2:
            warnings.append(f"{image_path}: aligned AB image width {width} is too small to split")
        elif width % 2 != 0:
            warnings.append(f"{image_path}: aligned AB image width {width} is odd; the loader will truncate the split point")
        if height < 1:
            warnings.append(f"{image_path}: image height {height} is invalid")
    return warnings


def check_directory(
    *,
    label: str,
    path: Path,
    recursive: bool,
    allow_empty: bool,
    check_open: bool,
    check_aligned_width: bool,
    max_open: int,
    errors: List[str],
    warnings: List[str],
) -> Dict[str, object]:
    record: Dict[str, object] = {"label": label, "path": str(path), "exists": path.is_dir(), "image_count": 0}
    if not path.is_dir():
        errors.append(f"missing required directory for {label}: {path}")
        return record

    images = list_images(path, recursive=recursive)
    record["image_count"] = len(images)
    if not images and not allow_empty:
        unsupported = list_unsupported_files(path, recursive=recursive)
        extra = f" Unsupported files include: {', '.join(unsupported)}" if unsupported else ""
        errors.append(f"no supported image files found for {label} in {path}.{extra}")
        return record

    if check_open and images:
        open_errors = verify_openable(images, max_open=max_open)
        errors.extend(open_errors)
        if open_errors:
            record["open_errors"] = open_errors[:5]

    if check_aligned_width and images:
        width_warnings = check_aligned_widths(images, max_open=max_open)
        warnings.extend(width_warnings)
        if width_warnings:
            record["width_warnings"] = width_warnings[:5]

    return record


def validate(args: argparse.Namespace) -> Tuple[int, Dict[str, object]]:
    root = Path(args.dataroot).expanduser()
    recursive = not args.non_recursive
    errors: List[str] = []
    warnings: List[str] = []
    checks: List[Dict[str, object]] = []

    result: Dict[str, object] = {
        "mode": args.mode,
        "dataroot": str(root),
        "phase": args.phase,
        "recursive": recursive,
        "checks": checks,
        "warnings": warnings,
        "errors": errors,
    }

    if not root.is_dir():
        errors.append(f"dataroot is not a directory: {root}")
        return 1, result

    phases = resolve_phases(root, args.mode, args.phase)
    result["resolved_phases"] = phases

    if args.mode == "single":
        checks.append(
            check_directory(
                label="single input root",
                path=root,
                recursive=recursive,
                allow_empty=args.allow_empty,
                check_open=args.check_open,
                check_aligned_width=False,
                max_open=args.max_open,
                errors=errors,
                warnings=warnings,
            )
        )
    elif args.mode == "unaligned":
        for phase in phases:
            assert phase is not None
            for side in ("A", "B"):
                checks.append(
                    check_directory(
                        label=f"{phase}{side}",
                        path=root / f"{phase}{side}",
                        recursive=recursive,
                        allow_empty=args.allow_empty,
                        check_open=args.check_open,
                        check_aligned_width=False,
                        max_open=args.max_open,
                        errors=errors,
                        warnings=warnings,
                    )
                )
        if args.phase == "auto" and not phase_exists(root, args.mode, "test") and not args.require_test:
            warnings.append("optional testA/testB split not found; pass --phase test or --require-test if test data is required")
    else:
        for phase in phases:
            assert phase is not None
            checks.append(
                check_directory(
                    label=phase,
                    path=root / phase,
                    recursive=recursive,
                    allow_empty=args.allow_empty,
                    check_open=args.check_open,
                    check_aligned_width=args.check_aligned_width and args.mode == "aligned",
                    max_open=args.max_open,
                    errors=errors,
                    warnings=warnings,
                )
            )
        if args.phase == "auto" and not phase_exists(root, args.mode, "test") and not args.require_test:
            warnings.append("optional test split not found; pass --phase test or --require-test if test data is required")

    if args.require_test and args.mode != "single" and not phase_exists(root, args.mode, "test"):
        if args.mode == "unaligned":
            errors.append("--require-test requested but testA/testB are not both present")
        else:
            errors.append("--require-test requested but test/ is not present")

    if args.mode == "unaligned":
        by_label = {str(record["label"]): int(record.get("image_count", 0)) for record in checks}
        for phase in phases:
            if phase is None:
                continue
            a_count = by_label.get(f"{phase}A", 0)
            b_count = by_label.get(f"{phase}B", 0)
            if a_count and b_count and a_count != b_count:
                warnings.append(f"{phase}A has {a_count} images and {phase}B has {b_count}; this is allowed for unaligned data")

    return (1 if errors else 0), result


def print_human(result: Dict[str, object]) -> None:
    print(f"mode: {result['mode']}")
    print(f"dataroot: {result['dataroot']}")
    print(f"phase: {result['phase']} -> {result.get('resolved_phases')}")
    for record in result["checks"]:  # type: ignore[index]
        status = "OK" if record.get("exists") and int(record.get("image_count", 0)) > 0 else "CHECK"
        print(f"{status}: {record['label']}: {record['image_count']} image(s) at {record['path']}")
    warnings = result["warnings"]  # type: ignore[assignment]
    errors = result["errors"]  # type: ignore[assignment]
    if warnings:
        print("warnings:", file=sys.stderr)
        for warning in warnings:  # type: ignore[union-attr]
            print(f"  - {warning}", file=sys.stderr)
    if errors:
        print("errors:", file=sys.stderr)
        for error in errors:  # type: ignore[union-attr]
            print(f"  - {error}", file=sys.stderr)
    else:
        print("validation passed")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Safely validate CycleGAN/pix2pix dataset layouts without importing the repository.",
    )
    parser.add_argument("--mode", required=True, choices=("unaligned", "aligned", "single", "colorization"), help="Dataset mode to validate.")
    parser.add_argument("--dataroot", required=True, help="Dataset root or single-image input root to inspect.")
    parser.add_argument("--phase", default="auto", choices=("auto", "train", "test", "val"), help="Specific phase to validate; auto checks standard phase folders that exist.")
    parser.add_argument("--require-test", action="store_true", help="Fail if the standard test split is absent.")
    parser.add_argument("--allow-empty", action="store_true", help="Allow required directories to contain zero supported images.")
    parser.add_argument("--non-recursive", action="store_true", help="Only inspect direct children; default matches the recursive repository loader.")
    parser.add_argument("--check-open", action="store_true", help="Use Pillow to verify that sampled image files can be opened.")
    parser.add_argument("--check-aligned-width", action="store_true", help="For aligned mode, warn if sampled AB image widths are not cleanly splittable.")
    parser.add_argument("--max-open", type=int, default=100, help="Maximum images to open/dimension-check when optional checks are enabled.")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON summary.")
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.max_open < 1:
        parser.error("--max-open must be positive")
    status, result = validate(args)
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print_human(result)
    return status


if __name__ == "__main__":
    raise SystemExit(main())
