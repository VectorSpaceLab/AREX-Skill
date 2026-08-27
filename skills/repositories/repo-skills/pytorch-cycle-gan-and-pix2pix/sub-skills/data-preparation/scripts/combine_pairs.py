#!/usr/bin/env python3
"""Combine matching A/B image folders into side-by-side RGB AB images.

This is a safe, Pillow-based adapter for pix2pix aligned data preparation. It
imports no repository modules, performs no downloads, never deletes inputs, and
refuses to overwrite outputs unless --overwrite is supplied.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

from PIL import Image

IMG_EXTENSIONS: Tuple[str, ...] = (
    ".jpg", ".JPG", ".jpeg", ".JPEG", ".png", ".PNG", ".ppm", ".PPM",
    ".bmp", ".BMP", ".tif", ".TIF", ".tiff", ".TIFF",
)


class PairingError(RuntimeError):
    """Raised for user-fixable pairing problems."""


def is_image_file(path: Path) -> bool:
    return path.is_file() and path.name.endswith(IMG_EXTENSIONS)


def iter_image_files(root: Path, recursive: bool) -> List[Path]:
    if not root.is_dir():
        raise PairingError(f"input directory does not exist: {root}")
    iterator: Iterable[Path] = root.rglob("*") if recursive else root.iterdir()
    return sorted(path for path in iterator if is_image_file(path))


def parse_splits(value: Optional[str]) -> List[str]:
    if not value:
        return []
    splits = [part.strip() for part in value.split(",") if part.strip()]
    if not splits:
        raise PairingError("--splits was supplied but no split names were parsed")
    return splits


def has_direct_images(root: Path) -> bool:
    if not root.is_dir():
        return False
    return any(is_image_file(child) for child in root.iterdir())


def common_subdirs(fold_a: Path, fold_b: Path) -> List[str]:
    if not fold_a.is_dir() or not fold_b.is_dir():
        return []
    names_a = {path.name for path in fold_a.iterdir() if path.is_dir()}
    names_b = {path.name for path in fold_b.iterdir() if path.is_dir()}
    return sorted(names_a & names_b)


def normalize_extension(value: Optional[str]) -> str:
    if not value:
        return ""
    return value if value.startswith(".") else f".{value}"


def suffix_pair_rel(a_rel: Path) -> Tuple[Optional[Path], Optional[Path]]:
    """Return (b_rel, output_rel) for source-style *_A.ext -> *_B.ext pairs."""
    name = a_rel.name
    if "_A." not in name:
        return None, None
    b_name = name.replace("_A.", "_B.")
    out_name = name.replace("_A.", ".")
    return a_rel.with_name(b_name), a_rel.with_name(out_name)


def output_rel_for(a_rel: Path, index: int, args: argparse.Namespace) -> Path:
    if args.sequential_names:
        ext = normalize_extension(args.output_extension) or ".jpg"
        return Path(f"{index:04d}{ext}")

    if args.use_ab_suffix:
        _, out_rel = suffix_pair_rel(a_rel)
        if out_rel is None:
            out_rel = a_rel
    else:
        out_rel = a_rel

    ext = normalize_extension(args.output_extension)
    if ext:
        out_rel = out_rel.with_suffix(ext)
    return out_rel


def pair_jobs_for_folder(
    fold_a: Path,
    fold_b: Path,
    fold_ab: Path,
    args: argparse.Namespace,
) -> Tuple[List[Tuple[Path, Path, Path]], List[str]]:
    a_images = iter_image_files(fold_a, recursive=args.recursive)
    b_images = iter_image_files(fold_b, recursive=args.recursive)
    if args.use_ab_suffix:
        a_images = [path for path in a_images if "_A." in path.name]
    if args.limit is not None:
        a_images = a_images[: args.limit]

    b_by_rel: Dict[Path, Path] = {path.relative_to(fold_b): path for path in b_images}
    expected_b_rels = set()
    missing: List[str] = []
    jobs: List[Tuple[Path, Path, Path]] = []

    for index, a_path in enumerate(a_images):
        a_rel = a_path.relative_to(fold_a)
        if args.use_ab_suffix:
            b_rel, _ = suffix_pair_rel(a_rel)
            if b_rel is None:
                continue
        else:
            b_rel = a_rel
        expected_b_rels.add(b_rel)
        b_path = b_by_rel.get(b_rel)
        if b_path is None:
            missing.append(str(b_rel))
            continue
        out_rel = output_rel_for(a_rel, index=index, args=args)
        jobs.append((a_path, b_path, fold_ab / out_rel))

    if missing:
        examples = ", ".join(missing[:8])
        more = "" if len(missing) <= 8 else f" ... and {len(missing) - 8} more"
        raise PairingError(f"missing B-side files for {len(missing)} A-side image(s): {examples}{more}")

    extra = sorted(str(rel) for rel in set(b_by_rel) - expected_b_rels)
    if extra:
        examples = ", ".join(extra[:8])
        more = "" if len(extra) <= 8 else f" ... and {len(extra) - 8} more"
        message = f"B-side has {len(extra)} extra image(s) not used: {examples}{more}"
        if args.strict_extra:
            raise PairingError(message)
        print(f"warning: {message}", file=sys.stderr)

    if not jobs:
        raise PairingError(f"no matching image pairs found between {fold_a} and {fold_b}")

    return jobs, extra


def preflight_jobs(jobs: Sequence[Tuple[Path, Path, Path]], overwrite: bool) -> None:
    existing = [str(out_path) for _, _, out_path in jobs if out_path.exists()]
    if existing and not overwrite:
        examples = ", ".join(existing[:8])
        more = "" if len(existing) <= 8 else f" ... and {len(existing) - 8} more"
        raise PairingError(f"refusing to overwrite {len(existing)} existing output file(s): {examples}{more}")

    size_errors: List[str] = []
    for a_path, b_path, _ in jobs:
        try:
            with Image.open(a_path) as img_a, Image.open(b_path) as img_b:
                if img_a.size != img_b.size:
                    size_errors.append(f"{a_path.name}: A size {img_a.size} != B size {img_b.size}")
        except Exception as exc:
            size_errors.append(f"{a_path} / {b_path}: cannot inspect image pair ({exc})")
        if len(size_errors) >= 8:
            break
    if size_errors:
        examples = "; ".join(size_errors)
        raise PairingError(f"pair size/open checks failed: {examples}")


def write_jobs(jobs: Sequence[Tuple[Path, Path, Path]], *, overwrite: bool, quality: int, dry_run: bool) -> int:
    preflight_jobs(jobs, overwrite=overwrite)
    if dry_run:
        return len(jobs)

    for a_path, b_path, out_path in jobs:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with Image.open(a_path) as img_a, Image.open(b_path) as img_b:
            img_a = img_a.convert("RGB")
            img_b = img_b.convert("RGB")
            width, height = img_a.size
            combined = Image.new("RGB", (width * 2, height))
            combined.paste(img_a, (0, 0))
            combined.paste(img_b, (width, 0))
            save_kwargs = {}
            if out_path.suffix.lower() in {".jpg", ".jpeg"}:
                save_kwargs = {"quality": quality, "subsampling": 0}
            combined.save(out_path, **save_kwargs)
    return len(jobs)


def planned_folders(args: argparse.Namespace) -> List[Tuple[str, Path, Path, Path]]:
    if args.dataset_path:
        dataset = Path(args.dataset_path).expanduser()
        splits = parse_splits(args.splits) or ["train", "test"]
        return [(split, dataset / f"{split}A", dataset / f"{split}B", dataset / split) for split in splits]

    if not (args.fold_a and args.fold_b and args.fold_ab):
        raise PairingError("provide either --dataset-path or all of --fold-a, --fold-b, and --fold-ab")

    fold_a = Path(args.fold_a).expanduser()
    fold_b = Path(args.fold_b).expanduser()
    fold_ab = Path(args.fold_ab).expanduser()
    splits = parse_splits(args.splits)
    if splits:
        return [(split, fold_a / split, fold_b / split, fold_ab / split) for split in splits]

    if args.split_subdirs or (not has_direct_images(fold_a) and not has_direct_images(fold_b)):
        detected = common_subdirs(fold_a, fold_b)
        if detected:
            return [(split, fold_a / split, fold_b / split, fold_ab / split) for split in detected]
        if args.split_subdirs:
            raise PairingError(f"--split-subdirs requested but no common split subdirectories were found under {fold_a} and {fold_b}")

    return [("direct", fold_a, fold_b, fold_ab)]


def run(args: argparse.Namespace) -> int:
    folders = planned_folders(args)
    total = 0
    for label, fold_a, fold_b, fold_ab in folders:
        jobs, _ = pair_jobs_for_folder(fold_a, fold_b, fold_ab, args)
        count = write_jobs(jobs, overwrite=args.overwrite, quality=args.quality, dry_run=args.dry_run)
        total += count
        action = "would write" if args.dry_run else "wrote"
        print(f"{label}: {action} {count} AB image(s) to {fold_ab}")
    print(f"done: {total} pair(s) processed")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Combine matching A/B image folders into side-by-side RGB pix2pix AB images.",
    )
    parser.add_argument("--dataset-path", help="Dataset root containing trainA/trainB and testA/testB; outputs train/ and test/.")
    parser.add_argument("--fold-a", "--fold_A", dest="fold_a", help="Input A directory or A root containing split subdirectories.")
    parser.add_argument("--fold-b", "--fold_B", dest="fold_b", help="Input B directory or B root containing split subdirectories.")
    parser.add_argument("--fold-ab", "--fold_AB", dest="fold_ab", help="Explicit output directory/root for combined AB images.")
    parser.add_argument("--splits", help="Comma-separated splits to process, e.g. train,test. Defaults to train,test for --dataset-path.")
    parser.add_argument("--split-subdirs", action="store_true", help="Require fold mode to process common split subdirectories.")
    parser.add_argument("--recursive", action="store_true", help="Match images recursively by relative path instead of only direct children.")
    parser.add_argument("--use-ab-suffix", "--use_AB", dest="use_ab_suffix", action="store_true", help="Match A files named *_A.ext to B files named *_B.ext and remove _A in output names.")
    parser.add_argument("--limit", "--num-imgs", dest="limit", type=int, help="Maximum number of A-side images to process per split.")
    parser.add_argument("--output-extension", help="Force output extension, e.g. jpg or .png; default preserves A filename extension.")
    parser.add_argument("--sequential-names", action="store_true", help="Name outputs 0000.jpg, 0001.jpg, ... instead of preserving filenames.")
    parser.add_argument("--quality", type=int, default=100, help="JPEG quality for .jpg/.jpeg outputs.")
    parser.add_argument("--overwrite", action="store_true", help="Allow replacing existing output files.")
    parser.add_argument("--strict-extra", action="store_true", help="Fail if B contains images that are not matched by A.")
    parser.add_argument("--dry-run", action="store_true", help="Check pairing and sizes without writing output files.")
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.dataset_path and (args.fold_a or args.fold_b or args.fold_ab):
        parser.error("--dataset-path cannot be combined with --fold-a/--fold-b/--fold-ab")
    if args.limit is not None and args.limit < 1:
        parser.error("--limit/--num-imgs must be positive")
    if not (1 <= args.quality <= 100):
        parser.error("--quality must be between 1 and 100")
    try:
        return run(args)
    except PairingError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
