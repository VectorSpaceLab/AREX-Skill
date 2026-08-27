#!/usr/bin/env python3
"""Validate a Fill50K-style ControlNet training dataset.

This script is intentionally standalone: it does not import ControlNet, PyTorch,
model configs, checkpoints, or training code. It performs safe filesystem and
image checks, and it can write a tiny example fixture for local self-tests.
"""

from __future__ import annotations

import argparse
import binascii
import json
import struct
import sys
import zlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    from PIL import Image as PILImage
except ImportError:  # pragma: no cover - depends on host environment.
    PILImage = None  # type: ignore[assignment]

try:
    import cv2
except Exception:  # pragma: no cover - depends on host environment.
    cv2 = None  # type: ignore[assignment]

REQUIRED_KEYS = ("source", "target", "prompt")
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
PNG_COLOR_TYPES = {
    0: "grayscale",
    2: "RGB",
    3: "palette",
    4: "grayscale+alpha",
    6: "RGBA",
}


@dataclass
class ImageInfo:
    width: int
    height: int
    mode: str
    bit_depth: int | None
    loader: str


@dataclass
class ValidationStats:
    rows_seen: int = 0
    rows_checked: int = 0
    range_checks: int = 0
    warnings: int = 0
    errors: int = 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate Fill50K-style ControlNet prompt.json and image pairs."
    )
    parser.add_argument(
        "--dataset-root",
        type=Path,
        help="Directory containing prompt.json, source/, and target/.",
    )
    parser.add_argument(
        "--max-items",
        type=int,
        default=100,
        help="Maximum prompt rows to image-check; use 0 for all rows. Default: 100.",
    )
    parser.add_argument(
        "--allow-empty-prompt",
        action="store_true",
        help="Do not warn when a row has an empty prompt string.",
    )
    parser.add_argument(
        "--write-example-fixture",
        type=Path,
        help="Create a tiny valid Fill50K-style fixture at this directory and exit unless validation is requested.",
    )
    parser.add_argument(
        "--validate-written-fixture",
        action="store_true",
        help="After writing --write-example-fixture, validate it in the same run.",
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        help="Accepted for agent workflows that pass a checkout root; unused by this standalone dataset validator.",
    )
    return parser.parse_args()


def fail(stats: ValidationStats, message: str) -> None:
    stats.errors += 1
    print(f"ERROR: {message}", file=sys.stderr)


def warn(stats: ValidationStats, message: str) -> None:
    stats.warnings += 1
    print(f"WARNING: {message}", file=sys.stderr)


def resolve_inside(root: Path, relative_path: str, stats: ValidationStats, row_number: int, key: str) -> Path | None:
    if not relative_path:
        fail(stats, f"row {row_number}: {key} is empty")
        return None
    candidate = Path(relative_path)
    if candidate.is_absolute():
        fail(stats, f"row {row_number}: {key} must be relative, got absolute path {relative_path!r}")
        return None
    resolved_root = root.resolve()
    resolved_path = (root / candidate).resolve()
    try:
        resolved_path.relative_to(resolved_root)
    except ValueError:
        fail(stats, f"row {row_number}: {key} escapes dataset root: {relative_path!r}")
        return None
    return resolved_path


def read_png_info_stdlib(path: Path) -> ImageInfo:
    """Read enough PNG structure to prove a PNG is well-formed and get dimensions.

    This fallback keeps --write-example-fixture usable in minimal environments
    that do not have Pillow or OpenCV. It validates chunk CRCs and IDAT zlib
    streams, but it is not intended to replace full image libraries for every
    possible image format.
    """

    with path.open("rb") as handle:
        if handle.read(len(PNG_SIGNATURE)) != PNG_SIGNATURE:
            raise ValueError("not a PNG file")

        width = height = bit_depth = color_type = None
        saw_idat = False
        saw_iend = False
        decompressor = zlib.decompressobj()

        while True:
            length_bytes = handle.read(4)
            if len(length_bytes) != 4:
                raise ValueError("truncated PNG chunk length")
            chunk_length = struct.unpack(">I", length_bytes)[0]
            chunk_type = handle.read(4)
            chunk_data = handle.read(chunk_length)
            crc_bytes = handle.read(4)
            if len(chunk_type) != 4 or len(chunk_data) != chunk_length or len(crc_bytes) != 4:
                raise ValueError("truncated PNG chunk")
            expected_crc = struct.unpack(">I", crc_bytes)[0]
            actual_crc = binascii.crc32(chunk_type)
            actual_crc = binascii.crc32(chunk_data, actual_crc) & 0xFFFFFFFF
            if actual_crc != expected_crc:
                raise ValueError(f"bad PNG CRC in {chunk_type.decode('ascii', errors='replace')} chunk")

            if chunk_type == b"IHDR":
                if chunk_length != 13:
                    raise ValueError("invalid IHDR length")
                width, height, bit_depth, color_type, compression, filter_method, interlace = struct.unpack(
                    ">IIBBBBB", chunk_data
                )
                if width <= 0 or height <= 0:
                    raise ValueError(f"invalid PNG size {width}x{height}")
                if compression != 0 or filter_method != 0:
                    raise ValueError("unsupported PNG compression or filter method")
                if interlace not in {0, 1}:
                    raise ValueError("unsupported PNG interlace method")
            elif chunk_type == b"IDAT":
                saw_idat = True
                decompressor.decompress(chunk_data)
            elif chunk_type == b"IEND":
                saw_iend = True
                decompressor.flush()
                break

        if width is None or height is None or bit_depth is None or color_type is None:
            raise ValueError("missing PNG IHDR")
        if not saw_idat:
            raise ValueError("missing PNG IDAT")
        if not saw_iend:
            raise ValueError("missing PNG IEND")

        return ImageInfo(
            width=width,
            height=height,
            mode=PNG_COLOR_TYPES.get(color_type, f"png-color-type-{color_type}"),
            bit_depth=bit_depth,
            loader="stdlib-png",
        )


def load_image_with_pillow(path: Path) -> ImageInfo:
    if PILImage is None:
        raise RuntimeError("Pillow unavailable")
    with PILImage.open(path) as image:
        image.load()
        mode = image.mode
        width, height = image.size
        bit_depth = 8 if mode in {"RGB", "RGBA", "L", "P"} else None
    return ImageInfo(width=width, height=height, mode=mode, bit_depth=bit_depth, loader="pillow")


def load_image_with_cv2(path: Path) -> ImageInfo:
    if cv2 is None:
        raise RuntimeError("OpenCV unavailable")
    image = cv2.imread(str(path), cv2.IMREAD_UNCHANGED)
    if image is None:
        raise ValueError("OpenCV could not decode image")
    height, width = image.shape[:2]
    channels = 1 if image.ndim == 2 else image.shape[2]
    mode = {1: "grayscale", 3: "BGR", 4: "BGRA"}.get(channels, f"{channels}-channel")
    bit_depth = int(image.dtype.itemsize * 8) if hasattr(image, "dtype") else None
    return ImageInfo(width=width, height=height, mode=mode, bit_depth=bit_depth, loader="opencv")


def load_image(path: Path, stats: ValidationStats, row_number: int, key: str) -> ImageInfo | None:
    if not path.exists():
        fail(stats, f"row {row_number}: {key} image does not exist: {path}")
        return None
    if not path.is_file():
        fail(stats, f"row {row_number}: {key} is not a file: {path}")
        return None

    errors: list[str] = []
    for loader in (load_image_with_pillow, load_image_with_cv2):
        try:
            info = loader(path)
            break
        except Exception as exc:  # noqa: BLE001 - collect loader fallback reasons.
            errors.append(str(exc))
    else:
        if path.suffix.lower() == ".png":
            try:
                info = read_png_info_stdlib(path)
            except Exception as exc:  # noqa: BLE001 - report PNG parse failure.
                errors.append(str(exc))
                fail(stats, f"row {row_number}: {key} image is unreadable: {path} ({'; '.join(errors)})")
                return None
        else:
            fail(
                stats,
                f"row {row_number}: {key} image needs Pillow or OpenCV for non-PNG validation: {path} ({'; '.join(errors)})",
            )
            return None

    if info.width <= 0 or info.height <= 0:
        fail(stats, f"row {row_number}: {key} image has invalid size {info.width}x{info.height}: {path}")
        return None
    if info.mode not in {"RGB", "RGBA", "BGR", "BGRA", "L", "P", "grayscale", "palette", "grayscale+alpha"}:
        warn(stats, f"row {row_number}: {key} image mode {info.mode!r} will need RGB conversion verification")
    if info.bit_depth is not None and info.bit_depth != 8:
        warn(stats, f"row {row_number}: {key} image bit depth is {info.bit_depth}; tutorial normalization assumes 8-bit image loading")
    return info


def check_range_contract(
    source_info: ImageInfo,
    target_info: ImageInfo,
    stats: ValidationStats,
    row_number: int,
) -> None:
    if source_info.bit_depth == 8 and target_info.bit_depth == 8:
        stats.range_checks += 1
        return
    warn(
        stats,
        f"row {row_number}: normalization range check is approximate because source/target bit depth could not both be confirmed as 8-bit",
    )


def check_row_object(row: Any, stats: ValidationStats, row_number: int, allow_empty_prompt: bool) -> dict[str, str] | None:
    if not isinstance(row, dict):
        fail(stats, f"row {row_number}: expected a JSON object, got {type(row).__name__}")
        return None

    missing = [key for key in REQUIRED_KEYS if key not in row]
    if missing:
        fail(stats, f"row {row_number}: missing required key(s): {', '.join(missing)}")
        return None

    cleaned: dict[str, str] = {}
    for key in REQUIRED_KEYS:
        value = row[key]
        if not isinstance(value, str):
            fail(stats, f"row {row_number}: {key} must be a string, got {type(value).__name__}")
            return None
        cleaned[key] = value

    if not allow_empty_prompt and not cleaned["prompt"].strip():
        warn(stats, f"row {row_number}: prompt is empty")

    extra_keys = sorted(set(row) - set(REQUIRED_KEYS))
    if extra_keys:
        warn(stats, f"row {row_number}: extra key(s) ignored by the tutorial loader: {', '.join(extra_keys)}")

    return cleaned


def validate_dataset(dataset_root: Path, max_items: int, allow_empty_prompt: bool) -> ValidationStats:
    stats = ValidationStats()
    root = dataset_root.expanduser().resolve()
    prompt_path = root / "prompt.json"

    print(f"Dataset root: {root}")
    print(f"Prompt file:  {prompt_path}")

    if max_items < 0:
        fail(stats, "--max-items must be >= 0")
        return stats
    if not root.exists() or not root.is_dir():
        fail(stats, f"dataset root does not exist or is not a directory: {root}")
        return stats
    if not prompt_path.exists():
        fail(stats, f"prompt.json not found: {prompt_path}")
        return stats
    if not prompt_path.is_file():
        fail(stats, f"prompt.json is not a file: {prompt_path}")
        return stats

    check_limit = None if max_items == 0 else max_items

    with prompt_path.open("rt", encoding="utf-8") as handle:
        for row_number, raw_line in enumerate(handle, start=1):
            line = raw_line.strip()
            if not line:
                warn(stats, f"row {row_number}: blank line ignored")
                continue
            stats.rows_seen += 1
            if check_limit is not None and stats.rows_checked >= check_limit:
                continue
            try:
                parsed = json.loads(line)
            except json.JSONDecodeError as exc:
                fail(stats, f"row {row_number}: invalid JSON ({exc.msg} at column {exc.colno})")
                continue
            row = check_row_object(parsed, stats, row_number, allow_empty_prompt)
            if row is None:
                continue

            source_path = resolve_inside(root, row["source"], stats, row_number, "source")
            target_path = resolve_inside(root, row["target"], stats, row_number, "target")
            source_info = load_image(source_path, stats, row_number, "source") if source_path else None
            target_info = load_image(target_path, stats, row_number, "target") if target_path else None

            if source_info and target_info:
                if (source_info.width, source_info.height) != (target_info.width, target_info.height):
                    warn(
                        stats,
                        f"row {row_number}: source size {source_info.width}x{source_info.height} differs from target size {target_info.width}x{target_info.height}",
                    )
                check_range_contract(source_info, target_info, stats, row_number)
                stats.rows_checked += 1

    if stats.rows_seen == 0:
        fail(stats, "prompt.json contains no JSON rows")

    print(f"Rows seen:    {stats.rows_seen}")
    print(f"Rows checked: {stats.rows_checked}{' (all)' if max_items == 0 else ''}")
    print(f"Range checks: {stats.range_checks} row(s) confirmed compatible with source [0,1] and target [-1,1] normalization")
    print("Expected model-facing keys after loading: jpg=target[-1,1], txt=prompt, hint=source[0,1]")
    print(f"Warnings:     {stats.warnings}")
    print(f"Errors:       {stats.errors}")
    if stats.errors == 0:
        print("Validation passed.")
    else:
        print("Validation failed.", file=sys.stderr)
    return stats


def png_chunk(chunk_type: bytes, chunk_data: bytes) -> bytes:
    crc = binascii.crc32(chunk_type)
    crc = binascii.crc32(chunk_data, crc) & 0xFFFFFFFF
    return struct.pack(">I", len(chunk_data)) + chunk_type + chunk_data + struct.pack(">I", crc)


def write_png(path: Path, width: int, height: int, pixels: list[tuple[int, int, int]]) -> None:
    if len(pixels) != width * height:
        raise ValueError("pixel count does not match image dimensions")
    scanlines = bytearray()
    for row_start in range(0, len(pixels), width):
        scanlines.append(0)  # PNG filter type 0.
        for red, green, blue in pixels[row_start : row_start + width]:
            scanlines.extend((red, green, blue))
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    path.write_bytes(
        PNG_SIGNATURE
        + png_chunk(b"IHDR", ihdr)
        + png_chunk(b"IDAT", zlib.compress(bytes(scanlines)))
        + png_chunk(b"IEND", b"")
    )


def write_example_fixture(fixture_root: Path) -> None:
    root = fixture_root.expanduser().resolve()
    source_dir = root / "source"
    target_dir = root / "target"
    source_dir.mkdir(parents=True, exist_ok=True)
    target_dir.mkdir(parents=True, exist_ok=True)

    write_png(
        source_dir / "0.png",
        2,
        2,
        [(0, 0, 0), (255, 255, 255), (255, 0, 0), (0, 255, 0)],
    )
    write_png(
        target_dir / "0.png",
        2,
        2,
        [(255, 255, 255), (0, 0, 255), (255, 255, 0), (0, 0, 0)],
    )
    with (root / "prompt.json").open("wt", encoding="utf-8") as handle:
        handle.write(json.dumps({"source": "source/0.png", "target": "target/0.png", "prompt": "tiny fixture circle"}) + "\n")
    print(f"Wrote example fixture: {root}")


def main() -> int:
    args = parse_args()

    if args.write_example_fixture:
        try:
            write_example_fixture(args.write_example_fixture)
        except Exception as exc:  # noqa: BLE001 - keep CLI failures concise.
            print(f"ERROR: could not write example fixture: {exc}", file=sys.stderr)
            return 1
        if not args.validate_written_fixture:
            return 0
        dataset_root = args.write_example_fixture
    else:
        dataset_root = args.dataset_root

    if dataset_root is None:
        print("ERROR: provide --dataset-root or --write-example-fixture", file=sys.stderr)
        return 2

    stats = validate_dataset(dataset_root, args.max_items, args.allow_empty_prompt)
    return 0 if stats.errors == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
