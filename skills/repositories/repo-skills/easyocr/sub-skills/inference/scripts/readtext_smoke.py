#!/usr/bin/env python3
"""Run a tiny EasyOCR readtext call against one image."""

from __future__ import annotations

import argparse
from pprint import pprint


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a tiny EasyOCR OCR smoke test.")
    parser.add_argument("image", help="Image path or raw image URL to OCR.")
    parser.add_argument("--lang", nargs="+", default=["en"], help="Language codes to load.")
    parser.add_argument(
        "--gpu",
        default="auto",
        choices=["auto", "cpu", "cuda", "mps"],
        help="Backend hint for Reader.",
    )
    parser.add_argument("--detail", type=int, default=1, choices=[0, 1], help="Output detail level.")
    parser.add_argument(
        "--output-format",
        default="standard",
        choices=["standard", "dict", "json", "free_merge"],
        help="Reader output format.",
    )
    parser.add_argument("--allowlist", default=None, help="Keep only these characters.")
    parser.add_argument("--blocklist", default=None, help="Exclude these characters.")
    parser.add_argument("--paragraph", action=argparse.BooleanOptionalAction, default=False, help="Merge nearby boxes into paragraphs.")
    parser.add_argument(
        "--download-enabled",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Allow model downloads if the cache is missing.",
    )
    return parser.parse_args()


def resolve_gpu(value: str) -> bool | str:
    if value == "auto":
        return True
    if value == "cpu":
        return False
    return value


def main() -> int:
    args = parse_args()

    import easyocr

    reader = easyocr.Reader(
        args.lang,
        gpu=resolve_gpu(args.gpu),
        download_enabled=args.download_enabled,
        verbose=False,
    )
    result = reader.readtext(
        args.image,
        detail=args.detail,
        output_format=args.output_format,
        allowlist=args.allowlist,
        blocklist=args.blocklist,
        paragraph=args.paragraph,
    )
    pprint(result, sort_dicts=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
