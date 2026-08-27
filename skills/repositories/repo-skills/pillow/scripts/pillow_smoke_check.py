#!/usr/bin/env python3
"""Run a safe in-memory Pillow smoke check.

This script does not need repository checkout files. It verifies that Pillow imports,
creates an image, draws text, saves/opens PNG bytes, and reports selected
feature flags.
"""

from __future__ import annotations

import argparse
import io
import json
import sys
from typing import Any

FEATURES = (
    "jpg",
    "zlib",
    "libtiff",
    "webp",
    "avif",
    "jpg_2000",
    "freetype2",
    "littlecms2",
    "raqm",
)


def check_feature(features_module: Any, name: str) -> dict[str, Any]:
    try:
        available = bool(features_module.check(name))
    except ValueError:
        available = False
    try:
        version = features_module.version(name)
    except ValueError:
        version = None
    return {"available": available, "version": version}


def run_check() -> dict[str, Any]:
    try:
        import PIL
        from PIL import Image, ImageDraw, features
    except ModuleNotFoundError as exc:
        raise RuntimeError("Pillow is not importable in this Python environment") from exc

    image = Image.new("RGBA", (32, 24), (255, 255, 255, 0))
    draw = ImageDraw.Draw(image)
    draw.rectangle((2, 2, 29, 21), outline=(0, 128, 255, 255), width=2)
    draw.text((4, 6), "PIL", fill=(0, 0, 0, 255))

    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    payload_size = buffer.tell()
    buffer.seek(0)
    with Image.open(buffer) as reopened:
        reopened.load()
        reopened_facts = {
            "format": reopened.format,
            "mode": reopened.mode,
            "size": list(reopened.size),
        }

    return {
        "pillow_version": getattr(PIL, "__version__", None),
        "created_mode": image.mode,
        "created_size": list(image.size),
        "png_bytes": payload_size,
        "reopened": reopened_facts,
        "features": {name: check_feature(features, name) for name in FEATURES},
    }


def print_text(report: dict[str, Any]) -> None:
    print(f"Pillow version: {report['pillow_version']}")
    print(f"Created image: {report['created_mode']} {tuple(report['created_size'])}")
    print(f"PNG bytes: {report['png_bytes']}")
    reopened = report["reopened"]
    print(f"Reopened: {reopened['format']} {reopened['mode']} {tuple(reopened['size'])}")
    print("Features:")
    for name, status in report["features"].items():
        marker = "yes" if status["available"] else "no"
        version = f" ({status['version']})" if status["version"] else ""
        print(f"  {name:12} {marker}{version}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run a safe installed-Pillow smoke check.")
    parser.add_argument("--json", action="store_true", help="write machine-readable JSON")
    args = parser.parse_args(argv)

    try:
        report = run_check()
    except RuntimeError as exc:
        print(f"pillow_smoke_check.py: error: {exc}", file=sys.stderr)
        return 2

    if args.json:
        json.dump(report, sys.stdout, indent=2, sort_keys=True)
        print()
    else:
        print_text(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
