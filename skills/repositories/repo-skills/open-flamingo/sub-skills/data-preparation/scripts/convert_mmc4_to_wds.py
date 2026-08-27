#!/usr/bin/env python3
"""Convert downloaded MMC4 ZIP metadata plus image files into WebDataset tar shards.

This is a standalone, safety-hardened adaptation of OpenFlamingo's MMC4
conversion helper. It performs no repository-local imports and can be run from
any working directory.
"""

from __future__ import annotations

import argparse
import base64
import json
import sys
import uuid
import zipfile
from io import BytesIO, TextIOWrapper
from pathlib import Path
from typing import Any, Dict, Iterable, Iterator, List, Optional, Tuple


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Convert MMC4 ZIP shards and downloaded images into OpenFlamingo-compatible "
            "WebDataset tar shards containing JSON samples with base64 JPEG images."
        )
    )
    parser.add_argument(
        "--output_dir",
        required=True,
        help="Directory where output WebDataset .tar shards will be written.",
    )
    parser.add_argument(
        "--zip_files",
        required=True,
        help="Brace-expandable MMC4 ZIP pattern, e.g. 'path/to/shard_{0..23098}.zip'.",
    )
    parser.add_argument(
        "--image_dir",
        required=True,
        help="Root directory containing downloaded images as <image_dir>/<zip-position>/<image_name>.",
    )
    parser.add_argument(
        "--num_files_per_shard",
        required=True,
        type=int,
        help="Number of input ZIP metadata files to write before advancing to the next output tar stream.",
    )
    parser.add_argument(
        "--strict-images",
        action="store_true",
        help="Treat missing/corrupt image files as fatal instead of warning and continuing.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Read and validate ZIP/JSON structure without writing tar shards or opening images.",
    )
    return parser


def _load_runtime_dependencies():
    missing: List[str] = []
    try:
        import braceexpand  # type: ignore
    except Exception:  # noqa: BLE001
        braceexpand = None
        missing.append("braceexpand")
    try:
        import webdataset as wds  # type: ignore
    except Exception:  # noqa: BLE001
        wds = None
        if "--dry-run" not in sys.argv:
            missing.append("webdataset")
    try:
        from PIL import Image  # type: ignore
    except Exception:  # noqa: BLE001
        Image = None
        if "--dry-run" not in sys.argv:
            missing.append("Pillow")
    if missing:
        raise RuntimeError(
            "Missing required Python package(s): "
            + ", ".join(sorted(set(missing)))
            + ". Install them in the data-preparation environment before running conversion."
        )
    return braceexpand, wds, Image


def _first_json_member(zip_file: zipfile.ZipFile, zip_path: Path) -> str:
    names = [name for name in zip_file.namelist() if not name.endswith("/")]
    json_names = [name for name in names if name.lower().endswith((".json", ".jsonl"))]
    if json_names:
        return json_names[0]
    if names:
        # The native helper assumes the first archive member is the JSON data.
        return names[0]
    raise ValueError(f"{zip_path}: ZIP archive contains no files")


def _iter_zip_json_records(zip_path: Path) -> Iterator[Dict[str, Any]]:
    with zipfile.ZipFile(zip_path, "r") as zf:
        json_member = _first_json_member(zf, zip_path)
        with zf.open(json_member, "r") as raw:
            text = TextIOWrapper(raw, encoding="utf-8")
            for line_no, line in enumerate(text, start=1):
                stripped = line.strip()
                if not stripped:
                    continue
                try:
                    sample = json.loads(stripped)
                except json.JSONDecodeError as exc:
                    raise ValueError(f"{zip_path}:{json_member}:{line_no}: invalid JSON: {exc}") from exc
                if not isinstance(sample, dict):
                    raise ValueError(
                        f"{zip_path}:{json_member}:{line_no}: expected JSON object, got {type(sample).__name__}"
                    )
                yield sample


def _safe_image_path(image_root: Path, zip_position: int, image_name: str) -> Path:
    if not isinstance(image_name, str) or not image_name:
        raise ValueError(f"invalid image_name: {image_name!r}")
    rel = Path(image_name)
    if rel.is_absolute() or any(part in {"..", ""} for part in rel.parts):
        raise ValueError(f"unsafe image_name path component: {image_name!r}")
    return image_root / str(zip_position) / rel


def _attach_images(
    sample: Dict[str, Any],
    *,
    image_root: Path,
    zip_position: int,
    Image,
    strict_images: bool,
) -> Tuple[int, int]:
    """Attach base64 JPEG strings to sample['image_info'].

    Returns (attached_count, warning_count).
    """
    image_info = sample.get("image_info")
    if not isinstance(image_info, list):
        raise ValueError("sample missing list field 'image_info'")

    attached = 0
    warnings = 0
    for img_idx, image_meta in enumerate(image_info):
        if not isinstance(image_meta, dict):
            raise ValueError(f"image_info[{img_idx}] is not an object")
        image_name = image_meta.get("image_name")
        try:
            image_path = _safe_image_path(image_root, zip_position, image_name)
            with Image.open(image_path) as img:
                img = img.convert("RGB")
                buffered = BytesIO()
                img.save(buffered, format="JPEG")
            image_meta["image_base64"] = base64.b64encode(buffered.getvalue()).decode("utf-8")
            attached += 1
        except FileNotFoundError:
            message = (
                f"warning: missing image for ZIP position {zip_position}: {image_name!r}. "
                "This can happen when a source URL is unavailable."
            )
            if strict_images:
                raise FileNotFoundError(message)
            print(message, file=sys.stderr)
            warnings += 1
        except Exception as exc:  # noqa: BLE001 - image decode/save failures are data issues.
            message = f"warning: error processing image {image_name!r} for ZIP position {zip_position}: {exc}"
            if strict_images:
                raise RuntimeError(message) from exc
            print(message, file=sys.stderr)
            warnings += 1
    return attached, warnings


def convert(args: argparse.Namespace) -> int:
    if args.num_files_per_shard <= 0:
        raise ValueError("--num_files_per_shard must be positive")

    braceexpand, wds, Image = _load_runtime_dependencies()
    output_dir = Path(args.output_dir)
    image_root = Path(args.image_dir)
    doc_shards = [Path(p) for p in braceexpand.braceexpand(args.zip_files)]
    if not doc_shards:
        raise ValueError("--zip_files expanded to zero paths")

    missing_zips = [str(p) for p in doc_shards if not p.exists()]
    if missing_zips:
        preview = ", ".join(missing_zips[:5])
        more = "" if len(missing_zips) <= 5 else f" ... and {len(missing_zips) - 5} more"
        raise FileNotFoundError(f"expanded ZIP path(s) do not exist: {preview}{more}")

    if not args.dry_run:
        if not image_root.exists():
            raise FileNotFoundError(f"--image_dir does not exist: {image_root}")
        output_dir.mkdir(parents=True, exist_ok=True)

    processed_zips = 0
    processed_records = 0
    attached_images = 0
    image_warnings = 0

    if args.dry_run:
        for zip_position, zip_path in enumerate(doc_shards):
            zip_records = 0
            for _sample in _iter_zip_json_records(zip_path):
                zip_records += 1
            processed_zips += 1
            processed_records += zip_records
            print(f"dry-run: {zip_path} records={zip_records}", file=sys.stderr)
    else:
        output_pattern = str(output_dir / "%09d.tar")
        with wds.ShardWriter(output_pattern) as sink:
            for zip_position, zip_path in enumerate(doc_shards):
                zip_records = 0
                for sample in _iter_zip_json_records(zip_path):
                    attached, warnings = _attach_images(
                        sample,
                        image_root=image_root,
                        zip_position=zip_position,
                        Image=Image,
                        strict_images=args.strict_images,
                    )
                    attached_images += attached
                    image_warnings += warnings
                    sink.write({"__key__": uuid.uuid4().hex, "json": sample})
                    zip_records += 1
                    processed_records += 1
                processed_zips += 1
                print(f"converted: {zip_path} records={zip_records}", file=sys.stderr)
                if (
                    (zip_position + 1) % args.num_files_per_shard == 0
                    and (zip_position + 1) < len(doc_shards)
                ):
                    sink.next_stream()

    summary = {
        "output_dir": str(output_dir),
        "zip_files": len(doc_shards),
        "processed_zips": processed_zips,
        "processed_records": processed_records,
        "attached_images": attached_images,
        "image_warnings": image_warnings,
        "dry_run": bool(args.dry_run),
    }
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return convert(args)
    except Exception as exc:  # noqa: BLE001 - CLI should emit concise fatal errors.
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
