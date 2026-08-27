#!/usr/bin/env python3
"""Report installed Pillow format and codec capabilities."""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from typing import Any

CAPABILITY_NAMES = (
    "pil",
    "jpg",
    "jpg_2000",
    "zlib",
    "libtiff",
    "webp",
    "avif",
    "littlecms2",
    "libjpeg_turbo",
    "mozjpeg",
    "zlib_ng",
    "raqm",
    "libimagequant",
)

FORMAT_NAMES = (
    "PNG",
    "JPEG",
    "GIF",
    "TIFF",
    "WEBP",
    "AVIF",
    "JPEG2000",
    "PDF",
    "EPS",
)


def feature_status(features_module: Any, name: str) -> dict[str, Any]:
    try:
        available = features_module.check(name)
    except ValueError:
        available = False
    try:
        version = features_module.version(name)
    except ValueError:
        version = None
    return {"available": bool(available), "version": version}


def build_report() -> dict[str, Any]:
    try:
        import PIL
        from PIL import Image, features
    except ModuleNotFoundError as exc:
        raise RuntimeError("Pillow is not importable in this Python environment") from exc

    Image.init()

    extension_map = Image.registered_extensions()
    extensions_by_format: dict[str, list[str]] = defaultdict(list)
    for extension, format_name in sorted(extension_map.items()):
        extensions_by_format[format_name].append(extension)

    open_formats = set(Image.OPEN)
    save_formats = set(Image.SAVE)
    save_all_formats = set(Image.SAVE_ALL)

    report = {
        "pillow_version": getattr(PIL, "__version__", None),
        "features": {name: feature_status(features, name) for name in CAPABILITY_NAMES},
        "formats": {},
    }

    for format_name in FORMAT_NAMES:
        report["formats"][format_name] = {
            "can_open": format_name in open_formats,
            "can_save": format_name in save_formats,
            "can_save_all": format_name in save_all_formats,
            "extensions": extensions_by_format.get(format_name, []),
            "mime": Image.MIME.get(format_name),
        }

    extra_formats = sorted((open_formats | save_formats | save_all_formats) - set(FORMAT_NAMES))
    report["other_registered_formats"] = extra_formats
    return report


def print_text(report: dict[str, Any]) -> None:
    print(f"Pillow version: {report['pillow_version']}")
    print("\nCapabilities:")
    for name, status in report["features"].items():
        version = f" ({status['version']})" if status["version"] else ""
        marker = "yes" if status["available"] else "no"
        print(f"  {name:15} {marker}{version}")

    print("\nKey formats:")
    for format_name, data in report["formats"].items():
        flags = []
        if data["can_open"]:
            flags.append("open")
        if data["can_save"]:
            flags.append("save")
        if data["can_save_all"]:
            flags.append("save_all")
        flag_text = ", ".join(flags) if flags else "not registered"
        extensions = ", ".join(data["extensions"]) if data["extensions"] else "-"
        mime = data["mime"] or "-"
        print(f"  {format_name:10} {flag_text:20} extensions={extensions} mime={mime}")

    others = report.get("other_registered_formats", [])
    if others:
        print("\nOther registered formats:")
        print("  " + ", ".join(others))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Report installed Pillow feature, codec, and format support."
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="write the report as JSON instead of human-readable text",
    )
    args = parser.parse_args(argv)

    try:
        report = build_report()
    except RuntimeError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    if args.json:
        json.dump(report, sys.stdout, indent=2, sort_keys=True)
        print()
    else:
        print_text(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
