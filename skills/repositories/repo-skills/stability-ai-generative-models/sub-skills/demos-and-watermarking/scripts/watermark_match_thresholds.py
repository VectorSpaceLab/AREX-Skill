#!/usr/bin/env python3
"""Classify generative-models invisible watermark bit-match counts.

This mirrors scripts/demo/detect.py threshold classification without importing
OpenCV, invisible-watermark, imwatermark, NumPy, Torch, or repository modules.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from typing import Iterable, Sequence

WATERMARK_MESSAGE = 0b101100111110110010010000011110111011000110011110
WATERMARK_BITS = [int(bit) for bit in bin(WATERMARK_MESSAGE)[2:]]
WATERMARK_LENGTH = len(WATERMARK_BITS)

MATCH_THRESHOLDS = [
    (27, "No watermark detected"),
    (33, "Partial watermark match. Cannot determine with certainty."),
    (
        35,
        'Likely watermarked. In the repository test, 0.02% of real images were falsely detected as "Likely watermarked".',
    ),
    (
        49,
        'Very likely watermarked. In the repository test, no real images were falsely detected as "Very likely watermarked".',
    ),
]


@dataclass(frozen=True)
class Classification:
    bit_matches: int
    total_bits: int
    bucket: str
    message: str


def classify_count(bit_matches: int) -> Classification:
    """Classify a single integer bit-match count from 0 through 48."""
    if isinstance(bit_matches, bool) or not isinstance(bit_matches, int):
        raise TypeError(f"bit match count must be an integer, got {type(bit_matches).__name__}")
    if bit_matches < 0 or bit_matches > WATERMARK_LENGTH:
        raise ValueError(f"bit match count must be between 0 and {WATERMARK_LENGTH}: {bit_matches}")

    for limit, message in MATCH_THRESHOLDS:
        if bit_matches <= limit:
            return Classification(
                bit_matches=bit_matches,
                total_bits=WATERMARK_LENGTH,
                bucket=_bucket_for_limit(limit),
                message=message,
            )

    raise AssertionError("unreachable threshold state")


def classify_counts(counts: Iterable[int]) -> list[Classification]:
    return [classify_count(count) for count in counts]


def _bucket_for_limit(limit: int) -> str:
    if limit == 27:
        return "no_watermark"
    if limit == 33:
        return "partial_match"
    if limit == 35:
        return "likely_watermarked"
    if limit == 49:
        return "very_likely_watermarked"
    raise ValueError(f"unknown threshold limit: {limit}")


def _coerce_count_token(raw_token: str) -> list[int]:
    try:
        return [int(raw_token)]
    except ValueError:
        pass

    value = json.loads(raw_token)
    if isinstance(value, int):
        return [value]
    if not isinstance(value, list):
        raise ValueError("JSON input must be an integer or a list of integers")
    if not all(isinstance(item, int) and not isinstance(item, bool) for item in value):
        raise ValueError("JSON list must contain only integers")
    return value


def _render_text(results: Sequence[Classification]) -> str:
    lines = []
    for result in results:
        lines.append(
            f"{result.bit_matches}/{result.total_bits}: {result.message} [{result.bucket}]"
        )
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Classify invisible watermark bit-match counts using the "
            "generative-models detect.py thresholds. This does not decode images."
        )
    )
    parser.add_argument(
        "counts",
        nargs="*",
        help="Integer bit-match counts, or JSON integers/lists such as '[27, 34, 48]'.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON instead of text.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        counts = []
        for token in args.counts:
            counts.extend(_coerce_count_token(token))
    except (json.JSONDecodeError, ValueError) as error:
        parser.error(str(error))
    if not counts:
        parser.error("provide at least one count or JSON list input")

    try:
        results = classify_counts(counts)
    except (TypeError, ValueError) as error:
        parser.error(str(error))

    if args.json:
        print(json.dumps([asdict(result) for result in results], indent=2))
    else:
        print(_render_text(results))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
