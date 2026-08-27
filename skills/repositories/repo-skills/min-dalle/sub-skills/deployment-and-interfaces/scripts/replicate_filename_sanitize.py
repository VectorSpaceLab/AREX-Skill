#!/usr/bin/env python3
"""Preview min(DALL·E) Replicate-style output basenames without Cog or model loading."""

from __future__ import annotations

import argparse
import string
import sys

try:
    from emoji import demojize
except ImportError:  # keep helper usable enough to report missing optional dep
    demojize = None


def filename_from_text(text: str) -> str:
    if demojize is None:
        raise RuntimeError("emoji package is required for exact Replicate-style demojize behavior")
    text = demojize(text, delimiters=["", ""])
    text = text.lower().encode("ascii", errors="ignore").decode()
    allowed_chars = string.ascii_lowercase + " "
    text = "".join(ch for ch in text.lower() if ch in allowed_chars)
    text = text[:64]
    text = "-".join(text.strip().split())
    return text or "blank"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Sanitize a prompt into the basename used by the min-dalle Replicate predictor.")
    parser.add_argument("--text", default="Dali painting of WALL-E", help="Prompt text to sanitize.")
    parser.add_argument("--self-test", action="store_true", help="Run deterministic examples and exit.")
    return parser


def run_self_test() -> int:
    cases = {
        "Dali painting of WALL-E": "dali-painting-of-walle",
        "123 !!!": "blank",
        "Cute 🤖 robot": "cute-robot-robot",
        "  Many     Spaces  ": "many-spaces",
    }
    for text, expected in cases.items():
        actual = filename_from_text(text)
        print(f"{text!r} -> {actual}")
        if actual != expected:
            print(f"expected {expected!r}, got {actual!r}", file=sys.stderr)
            return 1
    print("replicate filename sanitation self-test passed")
    return 0


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if demojize is None:
        print("missing dependency: install emoji for exact demojize behavior", file=sys.stderr)
        return 2
    if args.self_test:
        return run_self_test()
    print(filename_from_text(args.text))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
