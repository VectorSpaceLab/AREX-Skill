#!/usr/bin/env python3
"""Run a safe, deterministic SAHI postprocess backend smoke test.

The script uses tiny in-memory numpy arrays, writes no files, contacts no
network services, downloads no assets, trains nothing, and reads no credentials.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

import numpy as np


def _ensure_repo_importable() -> None:
    """Allow direct execution from arbitrary working directories."""
    for parent in Path(__file__).resolve().parents:
        if (parent / "sahi" / "postprocess" / "backends.py").is_file():
            sys.path.insert(0, str(parent))
            return


_ensure_repo_importable()

from sahi.postprocess.backends import get_postprocess_backend, resolve_backend, set_postprocess_backend
from sahi.postprocess.combine import batched_nms, greedy_nmm, nmm, nms

VALID_BACKENDS = ("auto", "numpy", "numba", "torchvision")


def _normalise_mapping(mapping: dict[Any, list[Any]]) -> dict[int, list[int]]:
    """Convert backend return mappings to plain int dictionaries."""
    return {int(key): [int(value) for value in values] for key, values in mapping.items()}


def _assert_equal(actual: Any, expected: Any, label: str) -> None:
    """Raise AssertionError with a compact labelled mismatch message."""
    if actual != expected:
        raise AssertionError(f"{label}: expected {expected!r}, got {actual!r}")


def run_smoke(print_backend: bool = False) -> None:
    """Exercise deterministic NMS, batched NMS, GreedyNMM, NMM, IOU, and IOS cases."""
    configured = get_postprocess_backend()
    resolved = resolve_backend()
    if print_backend:
        print(f"configured={configured} resolved={resolved}")

    predictions = np.array(
        [
            [0, 0, 10, 10, 0.90, 1],
            [1, 1, 9, 9, 0.80, 1],
            [0, 0, 10, 10, 0.70, 2],
            [30, 30, 40, 40, 0.60, 1],
        ],
        dtype=np.float32,
    )

    _assert_equal(nms(predictions, match_metric="IOU", match_threshold=0.5), [0, 3], "nms IOU")
    _assert_equal(
        batched_nms(predictions, match_metric="IOU", match_threshold=0.5),
        [0, 2, 3],
        "batched_nms IOU",
    )
    _assert_equal(
        _normalise_mapping(greedy_nmm(predictions, match_metric="IOU", match_threshold=0.5)),
        {0: [1, 2], 3: []},
        "greedy_nmm IOU",
    )
    _assert_equal(
        _normalise_mapping(nmm(predictions, match_metric="IOU", match_threshold=0.5)),
        {0: [1, 2], 3: []},
        "nmm IOU",
    )

    nested = np.array(
        [
            [0, 0, 100, 100, 0.90, 1],
            [10, 10, 20, 20, 0.80, 1],
        ],
        dtype=np.float32,
    )
    _assert_equal(nms(nested, match_metric="IOU", match_threshold=0.5), [0, 1], "nested nms IOU")
    _assert_equal(nms(nested, match_metric="IOS", match_threshold=0.5), [0], "nested nms IOS")
    _assert_equal(
        _normalise_mapping(greedy_nmm(nested, match_metric="IOS", match_threshold=0.5)),
        {0: [1]},
        "nested greedy_nmm IOS",
    )
    _assert_equal(
        _normalise_mapping(nmm(nested, match_metric="IOS", match_threshold=0.5)),
        {0: [1]},
        "nested nmm IOS",
    )


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Safely smoke-test SAHI postprocess backend dispatch with tiny deterministic arrays."
    )
    parser.add_argument(
        "--backend",
        choices=VALID_BACKENDS,
        default="numpy",
        help="Backend to configure before the smoke test. Defaults to numpy for safe reproducibility.",
    )
    parser.add_argument(
        "--print-backend",
        action="store_true",
        help="Print configured and resolved backend names before assertions.",
    )
    return parser.parse_args()


def main() -> None:
    """Configure the requested backend and run the smoke assertions."""
    args = parse_args()
    set_postprocess_backend(args.backend)
    try:
        run_smoke(print_backend=args.print_backend)
    except ImportError as exc:
        raise SystemExit(
            f"Selected backend {args.backend!r} could not import its optional dependencies. "
            "Re-run with --backend numpy or install the required backend packages."
        ) from exc
    print("postprocess backend smoke passed")


if __name__ == "__main__":
    main()
