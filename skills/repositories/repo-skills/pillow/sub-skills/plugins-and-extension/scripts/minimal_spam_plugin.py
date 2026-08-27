#!/usr/bin/env python3
"""Minimal self-contained Pillow image plugin example.

The toy SPAM format used here is deliberately simple:

- 128-byte ASCII header: "SPAM <width> <height> <bits>" padded with spaces.
- Pixel data follows immediately after the header.
- Supported bit depths are 8-bit grayscale (L) and 24-bit RGB.

Run:
    python minimal_spam_plugin.py --help
    python minimal_spam_plugin.py --self-test
"""

from __future__ import annotations

import argparse
import io
from dataclasses import dataclass

try:
    from PIL import Image, ImageFile
except ImportError:
    Image = None
    ImageFile = None

HEADER_SIZE = 128
FORMAT = "SPAM"
EXTENSIONS = [".spam", ".spa"]


def _accept(prefix: bytes) -> bool:
    """Return true when the file prefix looks like this toy SPAM format."""
    return prefix.startswith(b"SPAM ")


if Image is not None and ImageFile is not None:

    class SpamImageFile(ImageFile.ImageFile):
        """Pillow ImageFile implementation for the toy SPAM raster format."""

        format = FORMAT
        format_description = "Toy SPAM raster image"

        def _open(self) -> None:
            if self.fp is None:
                raise SyntaxError("missing file object")

            header = self.fp.read(HEADER_SIZE)
            if not _accept(header):
                raise SyntaxError("not a SPAM file")

            fields = header.split()
            if len(fields) < 4:
                raise SyntaxError("incomplete SPAM header")

            try:
                width = int(fields[1])
                height = int(fields[2])
                bits = int(fields[3])
            except ValueError as exc:
                raise SyntaxError("invalid SPAM dimensions or bit depth") from exc

            if width <= 0 or height <= 0:
                raise SyntaxError("SPAM dimensions must be positive")

            if bits == 8:
                self._mode = "L"
                raw_mode = "L"
            elif bits == 24:
                self._mode = "RGB"
                raw_mode = "RGB"
            else:
                raise SyntaxError("SPAM bit depth must be 8 or 24")

            self._size = (width, height)
            self.tile = [
                ImageFile._Tile(
                    "raw", (0, 0) + self.size, HEADER_SIZE, (raw_mode, 0, 1)
                )
            ]

    Image.register_open(SpamImageFile.format, SpamImageFile, _accept)
    Image.register_extensions(SpamImageFile.format, EXTENSIONS)
else:
    SpamImageFile = None


@dataclass(frozen=True)
class SpamFixture:
    mode: str
    size: tuple[int, int]
    data: bytes


def make_spam_bytes(fixture: SpamFixture) -> bytes:
    """Create bytes for the toy SPAM format."""
    if fixture.mode == "L":
        bits = 8
        expected = fixture.size[0] * fixture.size[1]
    elif fixture.mode == "RGB":
        bits = 24
        expected = fixture.size[0] * fixture.size[1] * 3
    else:
        raise ValueError("fixture mode must be L or RGB")

    if len(fixture.data) != expected:
        raise ValueError(f"fixture data must contain {expected} bytes")

    header_text = f"SPAM {fixture.size[0]} {fixture.size[1]} {bits}".encode("ascii")
    if len(header_text) > HEADER_SIZE:
        raise ValueError("header is too large")

    return header_text.ljust(HEADER_SIZE, b" ") + fixture.data


def run_self_test() -> None:
    """Create and open tiny SPAM images using Pillow dispatch."""
    if Image is None:
        raise SystemExit("Pillow is required for --self-test")

    gray_fixture = SpamFixture("L", (2, 2), bytes([0, 64, 128, 255]))
    rgb_fixture = SpamFixture(
        "RGB",
        (2, 1),
        bytes([255, 0, 0, 0, 128, 255]),
    )

    for fixture in (gray_fixture, rgb_fixture):
        payload = make_spam_bytes(fixture)
        with Image.open(io.BytesIO(payload), formats=[FORMAT]) as image:
            assert image.format == FORMAT
            assert image.mode == fixture.mode
            assert image.size == fixture.size
            image.load()
            assert image.tobytes() == fixture.data

    assert _accept(b"SPAM 1 1 8") is True
    assert _accept(b"PNG\r\n\x1a\n") is False
    assert Image.EXTENSION[".spam"] == FORMAT
    print("minimal SPAM plugin self-test passed")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Register and self-test a minimal Pillow SPAM image plugin."
    )
    parser.add_argument(
        "--self-test",
        action="store_true",
        help="create tiny in-memory SPAM fixtures and verify Image.open dispatch",
    )
    args = parser.parse_args()

    if args.self_test:
        run_self_test()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
