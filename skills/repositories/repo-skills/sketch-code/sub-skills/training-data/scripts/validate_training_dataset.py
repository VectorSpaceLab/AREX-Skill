#!/usr/bin/env python3
"""Validate a SketchCode training dataset without importing TensorFlow/Keras.

Checks paired .png/.gui stems, optional Pillow image readability, duplicate GUI
texts, vocabulary coverage, and split-directory hazards before running the
legacy SketchCode training workflow.
"""
import argparse
import hashlib
import json
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

DEFAULT_VOCAB = [
    ",",
    "{",
    "}",
    "small-title",
    "text",
    "quadruple",
    "row",
    "btn-inactive",
    "btn-orange",
    "btn-green",
    "btn-red",
    "double",
    "<START>",
    "header",
    "btn-active",
    "<END>",
    "single",
]
REQUIRED_VOCAB = {",", "{", "}", "<START>", "<END>"}
MARKER_TOKENS = {"<START>", "<END>"}
TOKEN_SPLIT_RE = re.compile(r"\s+")


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Validate paired SketchCode .png/.gui training data without importing "
            "TensorFlow, Keras, OpenCV, or NumPy."
        )
    )
    parser.add_argument(
        "dataset_dir",
        type=Path,
        help="Flat directory containing paired sample_id.png and sample_id.gui files.",
    )
    parser.add_argument(
        "--vocab-file",
        type=Path,
        default=None,
        help="Optional single-line SketchCode vocabulary file. Defaults to the bundled vocabulary facts.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat warnings such as duplicate GUI text or existing split directories as failures.",
    )
    parser.add_argument(
        "--no-pillow",
        action="store_true",
        help="Skip optional Pillow image-open checks even if Pillow is installed.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit a machine-readable JSON summary in addition to the text report.",
    )
    parser.add_argument(
        "--max-duplicate-examples",
        type=int,
        default=5,
        help="Maximum duplicate GUI groups to print in the text report. Default: 5.",
    )
    return parser.parse_args(argv)


def load_vocab(path: Optional[Path]) -> Tuple[List[str], List[str]]:
    warnings: List[str] = []
    if path is None:
        return list(DEFAULT_VOCAB), warnings

    try:
        text = path.read_text(encoding="utf-8").splitlines()[0]
    except IndexError:
        return [], [f"Vocabulary file is empty: {path}"]
    except OSError as exc:
        return [], [f"Could not read vocabulary file {path}: {exc}"]

    vocab = [tok for tok in text.split() if tok]
    if not vocab:
        warnings.append(f"Vocabulary file contains no tokens: {path}")
    return vocab, warnings


def tokenize_gui(text: str) -> List[str]:
    # Match the legacy loader's important normalization: collapse whitespace and
    # separate commas before Keras Tokenizer(split=' ', filters='', lower=False).
    normalized = " ".join(text.split())
    normalized = normalized.replace(",", " ,")
    return [tok for tok in TOKEN_SPLIT_RE.split(normalized.strip()) if tok]


def duplicate_key(text: str) -> str:
    # Mirrors the intent of the legacy duplicate hash: ignore spaces/newlines.
    compact = text.replace(" ", "").replace("\n", "")
    return hashlib.sha256(compact.encode("utf-8")).hexdigest()


def collect_files(dataset_dir: Path) -> Tuple[Dict[str, Path], Dict[str, Path], List[str]]:
    warnings: List[str] = []
    pngs: Dict[str, Path] = {}
    guis: Dict[str, Path] = {}

    for path in sorted(dataset_dir.iterdir()):
        if not path.is_file():
            continue
        suffix = path.suffix
        lower_suffix = suffix.lower()
        if lower_suffix in {".png", ".gui"} and suffix != lower_suffix:
            warnings.append(
                f"Legacy code expects lowercase suffixes; found {path.name} with suffix {suffix!r}."
            )
        if suffix == ".png":
            pngs[path.stem] = path
        elif suffix == ".gui":
            guis[path.stem] = path

    return pngs, guis, warnings


def check_pillow_images(png_paths: Iterable[Path], skip: bool) -> Tuple[List[str], List[str]]:
    warnings: List[str] = []
    errors: List[str] = []
    if skip:
        warnings.append("Pillow image checks skipped by --no-pillow.")
        return warnings, errors

    try:
        from PIL import Image  # type: ignore
    except Exception:
        warnings.append("Pillow is not installed/importable; skipped PNG readability checks.")
        return warnings, errors

    for path in png_paths:
        try:
            with Image.open(path) as image:
                fmt = image.format
                width, height = image.size
                image.verify()
            if fmt != "PNG":
                warnings.append(f"{path.name}: Pillow reports format {fmt!r}, not PNG.")
            if width <= 0 or height <= 0:
                errors.append(f"{path.name}: invalid image dimensions {width}x{height}.")
        except Exception as exc:
            errors.append(f"{path.name}: Pillow could not open/verify image: {exc}")
    return warnings, errors


def analyze_guis(gui_paths: Dict[str, Path], vocab: Sequence[str]) -> Tuple[List[str], List[str], Dict[str, List[str]], Dict[str, List[str]]]:
    vocab_set = set(vocab)
    warnings: List[str] = []
    errors: List[str] = []
    duplicate_groups_by_hash: Dict[str, List[str]] = defaultdict(list)
    unknown_tokens_by_stem: Dict[str, List[str]] = {}

    missing_required = sorted(REQUIRED_VOCAB - vocab_set)
    if missing_required:
        errors.append("Vocabulary is missing required tokens: " + ", ".join(missing_required))

    for stem, path in sorted(gui_paths.items()):
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            try:
                text = path.read_text(encoding="utf-8-sig")
                warnings.append(f"{path.name}: read using utf-8-sig after UTF-8 decode failed.")
            except Exception as exc:
                errors.append(f"{path.name}: could not read GUI text as UTF-8: {exc}")
                continue
        except OSError as exc:
            errors.append(f"{path.name}: could not read GUI text: {exc}")
            continue

        tokens = tokenize_gui(text)
        if not tokens:
            warnings.append(f"{path.name}: GUI file is empty after whitespace normalization.")
        marker_present = sorted(MARKER_TOKENS.intersection(tokens))
        if marker_present:
            warnings.append(
                f"{path.name}: contains {', '.join(marker_present)}; legacy training wraps GUI text with markers again."
            )
        unknown = sorted({tok for tok in tokens if tok not in vocab_set})
        if unknown:
            unknown_tokens_by_stem[stem] = unknown
        duplicate_groups_by_hash[duplicate_key(text)].append(stem)

    for stem, unknown in sorted(unknown_tokens_by_stem.items()):
        errors.append(f"{stem}.gui uses tokens outside vocabulary: " + ", ".join(unknown))

    duplicates = {h: stems for h, stems in duplicate_groups_by_hash.items() if len(stems) > 1}
    return warnings, errors, duplicates, unknown_tokens_by_stem


def split_dir_warnings(dataset_dir: Path) -> List[str]:
    warnings: List[str] = []
    parent = dataset_dir.parent
    for name in ("training_set", "validation_set"):
        candidate = parent / name
        if candidate.exists():
            warnings.append(
                f"Existing sibling {name}/ will be deleted and recreated by legacy training for this data_input_path."
            )
    if dataset_dir.name in {"training_set", "validation_set"}:
        warnings.append(
            "Input directory itself is named training_set or validation_set; use a separate raw dataset directory."
        )
    return warnings


def print_text_report(summary: dict, max_duplicate_examples: int) -> None:
    print("SketchCode training dataset validation")
    print("=====================================")
    print(f"Dataset: {summary['dataset_dir']}")
    print(f"PNG files: {summary['png_count']}")
    print(f"GUI files: {summary['gui_count']}")
    print(f"Paired samples: {summary['paired_count']}")
    print(f"Vocabulary size: {summary['vocab_size']}")
    print(f"Pillow checked PNGs: {summary['pillow_checked']}")

    if summary["missing_png"]:
        print("\nGUI files missing matching PNG:")
        for stem in summary["missing_png"]:
            print(f"  - {stem}.gui")
    if summary["missing_gui"]:
        print("\nPNG files missing matching GUI:")
        for stem in summary["missing_gui"]:
            print(f"  - {stem}.png")

    duplicate_groups = summary["duplicate_gui_groups"]
    if duplicate_groups:
        print("\nDuplicate GUI text groups (whitespace-insensitive):")
        for group in duplicate_groups[:max_duplicate_examples]:
            print("  - " + ", ".join(f"{stem}.gui" for stem in group))
        remaining = len(duplicate_groups) - max_duplicate_examples
        if remaining > 0:
            print(f"  ... {remaining} more duplicate group(s) not shown")

    if summary["warnings"]:
        print("\nWarnings:")
        for warning in summary["warnings"]:
            print(f"  - {warning}")
    if summary["errors"]:
        print("\nErrors:")
        for error in summary["errors"]:
            print(f"  - {error}")

    print("\nResult: " + summary["status"])


def main(argv: Sequence[str]) -> int:
    args = parse_args(argv)
    dataset_dir = args.dataset_dir
    warnings: List[str] = []
    errors: List[str] = []

    if not dataset_dir.exists():
        errors.append(f"Dataset directory does not exist: {dataset_dir}")
        summary = make_summary(args, [], {}, {}, [], warnings, errors, [], pillow_checked=False)
        print_text_report(summary, args.max_duplicate_examples)
        if args.json:
            print(json.dumps(summary, indent=2, sort_keys=True))
        return 1
    if not dataset_dir.is_dir():
        errors.append(f"Dataset path is not a directory: {dataset_dir}")
        summary = make_summary(args, [], {}, {}, [], warnings, errors, [], pillow_checked=False)
        print_text_report(summary, args.max_duplicate_examples)
        if args.json:
            print(json.dumps(summary, indent=2, sort_keys=True))
        return 1

    vocab, vocab_warnings = load_vocab(args.vocab_file)
    warnings.extend(vocab_warnings)

    pngs, guis, file_warnings = collect_files(dataset_dir)
    warnings.extend(file_warnings)

    paired_stems = sorted(set(pngs).intersection(guis))
    missing_png = sorted(set(guis) - set(pngs))
    missing_gui = sorted(set(pngs) - set(guis))
    if missing_png:
        errors.append(f"{len(missing_png)} GUI file(s) have no matching lowercase .png file.")
    if missing_gui:
        errors.append(f"{len(missing_gui)} PNG file(s) have no matching lowercase .gui file.")
    if not paired_stems:
        errors.append("No paired .png/.gui samples found.")

    gui_warnings, gui_errors, duplicates, _unknown = analyze_guis({stem: guis[stem] for stem in paired_stems}, vocab)
    warnings.extend(gui_warnings)
    errors.extend(gui_errors)

    duplicate_groups = [sorted(stems) for _h, stems in sorted(duplicates.items(), key=lambda item: item[1][0])]
    if duplicate_groups:
        warnings.append(
            f"Found {len(duplicate_groups)} duplicate GUI text group(s); legacy validation split may not keep duplicates out of validation."
        )

    warnings.extend(split_dir_warnings(dataset_dir))

    pillow_warnings, pillow_errors = check_pillow_images([pngs[stem] for stem in paired_stems], args.no_pillow)
    warnings.extend(pillow_warnings)
    errors.extend(pillow_errors)
    pillow_checked = bool(paired_stems) and not args.no_pillow and not any(
        w.startswith("Pillow is not installed") for w in pillow_warnings
    )

    if args.strict and warnings:
        errors.append("Strict mode treats warnings as failures.")

    summary = make_summary(args, vocab, pngs, guis, paired_stems, warnings, errors, duplicate_groups, pillow_checked)
    summary["missing_png"] = missing_png
    summary["missing_gui"] = missing_gui

    print_text_report(summary, args.max_duplicate_examples)
    if args.json:
        print("\nJSON summary:")
        print(json.dumps(summary, indent=2, sort_keys=True))

    return 0 if not errors else 1


def make_summary(
    args: argparse.Namespace,
    vocab: Sequence[str],
    pngs: Dict[str, Path],
    guis: Dict[str, Path],
    paired_stems: Sequence[str],
    warnings: Sequence[str],
    errors: Sequence[str],
    duplicate_groups: Sequence[Sequence[str]],
    pillow_checked: bool,
) -> dict:
    return {
        "dataset_dir": str(args.dataset_dir),
        "vocab_file": str(args.vocab_file) if args.vocab_file else "bundled-default",
        "vocab_size": len(vocab),
        "png_count": len(pngs),
        "gui_count": len(guis),
        "paired_count": len(paired_stems),
        "paired_stems": list(paired_stems),
        "missing_png": [],
        "missing_gui": [],
        "duplicate_gui_groups": [list(group) for group in duplicate_groups],
        "warnings": list(warnings),
        "errors": list(errors),
        "strict": bool(args.strict),
        "pillow_checked": bool(pillow_checked),
        "status": "PASS" if not errors else "FAIL",
    }


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
