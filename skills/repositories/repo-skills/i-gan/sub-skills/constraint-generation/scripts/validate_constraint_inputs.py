#!/usr/bin/env python3
"""Safely validate iGAN constraint image inputs without OpenCV.

This helper checks file existence, readability, image header metadata, dimensions,
and channel-family expectations for the color/mask/edge triplet consumed by
headless iGAN constrained generation. It does not decode pixels, import cv2,
import Theano, run training, download artifacts, or touch the GPU.
"""

from __future__ import annotations

import argparse
import json
import os
import struct
import sys
from dataclasses import asdict, dataclass, field
from typing import BinaryIO, Dict, Iterable, List, Optional, Tuple


PNG_COLOR_TYPES = {
    0: ("grayscale", 1),
    2: ("rgb", 3),
    3: ("indexed", 1),
    4: ("grayscale-alpha", 2),
    6: ("rgba", 4),
}

JPEG_SOF_MARKERS = set(range(0xC0, 0xC4)) | set(range(0xC5, 0xC8)) | set(range(0xC9, 0xCC)) | set(range(0xCD, 0xD0))


@dataclass
class ImageInfo:
    role: str
    path: str
    exists: bool = False
    is_file: bool = False
    readable: bool = False
    format: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    bit_depth: Optional[int] = None
    color_type: Optional[str] = None
    channels: Optional[int] = None
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    @property
    def size(self) -> Optional[Tuple[int, int]]:
        if self.width is None or self.height is None:
            return None
        return (self.width, self.height)


def inspect_png(handle: BinaryIO, info: ImageInfo) -> None:
    handle.seek(0)
    header = handle.read(33)
    if len(header) < 33:
        info.errors.append("truncated PNG header")
        return
    if header[:8] != b"\x89PNG\r\n\x1a\n":
        info.errors.append("invalid PNG signature")
        return
    ihdr_len = struct.unpack(">I", header[8:12])[0]
    chunk_type = header[12:16]
    if ihdr_len != 13 or chunk_type != b"IHDR":
        info.errors.append("PNG missing first IHDR chunk")
        return
    width, height, bit_depth, color_type = struct.unpack(">IIBB", header[16:26])
    info.format = "PNG"
    info.width = width
    info.height = height
    info.bit_depth = bit_depth
    name, channels = PNG_COLOR_TYPES.get(color_type, (f"unknown-{color_type}", None))
    info.color_type = name
    info.channels = channels
    if channels is None:
        info.errors.append(f"unsupported PNG color type {color_type}")


def read_segment_length(handle: BinaryIO) -> Optional[int]:
    data = handle.read(2)
    if len(data) != 2:
        return None
    return struct.unpack(">H", data)[0]


def next_jpeg_marker(handle: BinaryIO) -> Optional[int]:
    while True:
        byte = handle.read(1)
        if not byte:
            return None
        if byte == b"\xff":
            break
    while True:
        byte = handle.read(1)
        if not byte:
            return None
        value = byte[0]
        if value != 0xFF:
            return value


def inspect_jpeg(handle: BinaryIO, info: ImageInfo) -> None:
    handle.seek(0)
    if handle.read(2) != b"\xff\xd8":
        info.errors.append("invalid JPEG signature")
        return
    info.format = "JPEG"
    while True:
        marker = next_jpeg_marker(handle)
        if marker is None:
            info.errors.append("JPEG ended before a size marker was found")
            return
        if marker in (0xD9, 0xDA):  # EOI or start of scan
            info.errors.append("JPEG size marker not found before image data")
            return
        if 0xD0 <= marker <= 0xD7 or marker == 0x01:
            continue
        length = read_segment_length(handle)
        if length is None or length < 2:
            info.errors.append("invalid JPEG segment length")
            return
        payload_length = length - 2
        if marker in JPEG_SOF_MARKERS:
            payload = handle.read(payload_length)
            if len(payload) < 6:
                info.errors.append("truncated JPEG SOF segment")
                return
            precision = payload[0]
            height, width, components = struct.unpack(">HHB", payload[1:6])
            info.width = width
            info.height = height
            info.bit_depth = precision
            info.channels = components
            info.color_type = {1: "grayscale", 3: "rgb/ycbcr", 4: "cmyk"}.get(components, f"{components}-component")
            return
        handle.seek(payload_length, os.SEEK_CUR)


def inspect_bmp(handle: BinaryIO, info: ImageInfo) -> None:
    handle.seek(0)
    header = handle.read(54)
    if len(header) < 30 or header[:2] != b"BM":
        info.errors.append("invalid or truncated BMP header")
        return
    dib_size = struct.unpack("<I", header[14:18])[0]
    if dib_size < 40:
        info.errors.append("unsupported BMP DIB header")
        return
    width = struct.unpack("<i", header[18:22])[0]
    height = struct.unpack("<i", header[22:26])[0]
    bit_depth = struct.unpack("<H", header[28:30])[0]
    info.format = "BMP"
    info.width = abs(width)
    info.height = abs(height)
    info.bit_depth = bit_depth
    info.channels = max(1, bit_depth // 8)
    info.color_type = f"{bit_depth}-bit-bmp"


def inspect_gif(handle: BinaryIO, info: ImageInfo) -> None:
    handle.seek(0)
    header = handle.read(10)
    if len(header) < 10 or header[:6] not in (b"GIF87a", b"GIF89a"):
        info.errors.append("invalid or truncated GIF header")
        return
    width, height = struct.unpack("<HH", header[6:10])
    info.format = "GIF"
    info.width = width
    info.height = height
    info.bit_depth = None
    info.channels = 3
    info.color_type = "indexed-rgb"
    info.warnings.append("GIF is accepted for coarse header checks only; convert to PNG for native runs")


def inspect_image(role: str, path: str) -> ImageInfo:
    info = ImageInfo(role=role, path=path)
    info.exists = os.path.exists(path)
    if not info.exists:
        info.errors.append("missing path")
        return info
    info.is_file = os.path.isfile(path)
    if not info.is_file:
        info.errors.append("path is not a regular file")
        return info
    try:
        with open(path, "rb") as handle:
            signature = handle.read(12)
            info.readable = True
            if signature.startswith(b"\x89PNG\r\n\x1a\n"):
                inspect_png(handle, info)
            elif signature.startswith(b"\xff\xd8"):
                inspect_jpeg(handle, info)
            elif signature.startswith(b"BM"):
                inspect_bmp(handle, info)
            elif signature[:6] in (b"GIF87a", b"GIF89a"):
                inspect_gif(handle, info)
            else:
                info.errors.append("unsupported or unrecognized image header")
    except OSError as exc:
        info.errors.append(f"unreadable file: {exc}")
    return info


def positive_int(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"expected an integer, got {value!r}") from exc
    if parsed <= 0:
        raise argparse.ArgumentTypeError("must be positive")
    return parsed


def add_role_expectations(
    info: ImageInfo,
    *,
    strict_channels: bool,
    strict_bit_depth: bool,
) -> None:
    if info.errors:
        return
    if info.width is not None and info.height is not None and (info.width <= 0 or info.height <= 0):
        info.errors.append("image dimensions must be positive")
    if info.bit_depth is not None and info.bit_depth != 8:
        message = f"expected 8-bit image data for native iGAN workflow, observed {info.bit_depth}-bit"
        if strict_bit_depth:
            info.errors.append(message)
        else:
            info.warnings.append(message)
    if info.role == "input_color":
        if info.channels is not None and info.channels < 3:
            message = "color constraint is not a color image; OpenCV may expand it but color semantics are weak"
            if strict_channels:
                info.errors.append(message)
            else:
                info.warnings.append(message)
    elif info.role == "input_color_mask":
        if info.channels not in (1, None):
            message = "color mask is not grayscale; native script uses only the first channel as the mask"
            if strict_channels:
                info.errors.append(message)
            else:
                info.warnings.append(message)
    elif info.role == "input_edge":
        if info.channels is not None and info.channels not in (1, 3, 4):
            message = "edge image has an unusual channel count; first channel will be used as edge mask"
            if strict_channels:
                info.errors.append(message)
            else:
                info.warnings.append(message)
        elif info.channels == 4:
            info.warnings.append("edge image has alpha; native script uses color channels after OpenCV loading")


def check_dimensions(
    infos: Iterable[ImageInfo],
    *,
    target_size: Optional[int],
    require_same_size: bool,
    strict_size: bool,
) -> Tuple[List[str], List[str]]:
    errors: List[str] = []
    warnings: List[str] = []
    valid_infos = [info for info in infos if not info.errors and info.size is not None]
    if require_same_size and valid_infos:
        expected = valid_infos[0].size
        for info in valid_infos[1:]:
            if info.size != expected:
                errors.append(
                    f"dimension mismatch: {info.role} is {info.width}x{info.height}, "
                    f"expected {expected[0]}x{expected[1]}"
                )
    if target_size is not None:
        for info in valid_infos:
            if info.width != target_size or info.height != target_size:
                message = (
                    f"{info.role} is {info.width}x{info.height}, which does not match "
                    f"target size {target_size}x{target_size}; native script would resize it"
                )
                if strict_size:
                    errors.append(message)
                else:
                    warnings.append(message)
    return errors, warnings


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Validate the color image, color mask, and edge image headers for "
            "iGAN headless constrained generation without importing OpenCV."
        )
    )
    parser.add_argument("--input-color", required=True, help="Color constraint image path.")
    parser.add_argument("--input-color-mask", required=True, help="Color mask image path.")
    parser.add_argument("--input-edge", required=True, help="Edge/sketch constraint image path.")
    parser.add_argument(
        "--target-size",
        type=positive_int,
        default=64,
        help="Expected square model image size for warnings or strict checks (default: 64).",
    )
    parser.add_argument(
        "--no-target-size",
        action="store_true",
        help="Disable target-size checks while still checking that input dimensions match each other.",
    )
    parser.add_argument(
        "--strict-size",
        action="store_true",
        help="Fail instead of warn when an image differs from --target-size.",
    )
    parser.add_argument(
        "--no-require-same-size",
        action="store_true",
        help="Do not fail when the three inputs have different dimensions.",
    )
    parser.add_argument(
        "--strict-channels",
        action="store_true",
        help="Fail instead of warn on non-preferred channel families.",
    )
    parser.add_argument(
        "--strict-bit-depth",
        action="store_true",
        help="Fail instead of warn on non-8-bit image headers.",
    )
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    role_paths = [
        ("input_color", args.input_color),
        ("input_color_mask", args.input_color_mask),
        ("input_edge", args.input_edge),
    ]
    infos = [inspect_image(role, path) for role, path in role_paths]
    for info in infos:
        add_role_expectations(
            info,
            strict_channels=args.strict_channels,
            strict_bit_depth=args.strict_bit_depth,
        )

    target_size = None if args.no_target_size else args.target_size
    dim_errors, dim_warnings = check_dimensions(
        infos,
        target_size=target_size,
        require_same_size=not args.no_require_same_size,
        strict_size=args.strict_size,
    )

    all_errors = [message for info in infos for message in info.errors] + dim_errors
    all_warnings = [message for info in infos for message in info.warnings] + dim_warnings
    ok = not all_errors

    payload: Dict[str, object] = {
        "ok": ok,
        "inputs": [asdict(info) for info in infos],
        "errors": all_errors,
        "warnings": all_warnings,
        "notes": [
            "Header validation only; pixel values and mask sparsity are not decoded.",
            "Native iGAN execution still requires OpenCV, Theano, PyQt4, model artifacts, and the requested backend.",
        ],
    }

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        for info in infos:
            if info.format and info.size:
                print(
                    f"{info.role}: {info.path} -> {info.format} {info.width}x{info.height}, "
                    f"bit_depth={info.bit_depth}, color_type={info.color_type}, channels={info.channels}"
                )
            else:
                print(f"{info.role}: {info.path} -> unavailable header metadata")
            for warning in info.warnings:
                print(f"  WARN: {warning}")
            for error in info.errors:
                print(f"  ERROR: {error}")
        for warning in dim_warnings:
            print(f"WARN: {warning}")
        for error in dim_errors:
            print(f"ERROR: {error}")
        if ok:
            print(f"RESULT: ok ({len(all_warnings)} warning(s)); native execution not attempted")
        else:
            print(f"RESULT: failed ({len(all_errors)} error(s), {len(all_warnings)} warning(s)); native execution not attempted")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
