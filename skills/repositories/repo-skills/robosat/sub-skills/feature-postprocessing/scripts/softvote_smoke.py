#!/usr/bin/env python3
"""Tiny smoke test for robosat.tools.masks.softvote.

The --help path intentionally avoids importing RoboSat so agents can inspect
usage even before the package is installed. Running the smoke requires an
installed RoboSat package plus NumPy.
"""

import argparse
import sys


def build_parser():
    parser = argparse.ArgumentParser(
        description="Run a tiny deterministic soft-vote check against robosat.tools.masks.softvote."
    )
    parser.add_argument(
        "--weights",
        type=float,
        nargs=2,
        metavar=("W_A", "W_B"),
        help="optional two-model weights; default uses an unweighted average",
    )
    parser.add_argument(
        "--show-arrays",
        action="store_true",
        help="print the tiny foreground probabilities and voted mask",
    )
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)

    try:
        import numpy as np
        from robosat.tools.masks import softvote
    except Exception as exc:  # pragma: no cover - environment diagnostic path
        print("ERROR: could not import NumPy and robosat.tools.masks.softvote: {}".format(exc), file=sys.stderr)
        print("Install RoboSat and its runtime dependencies, then rerun this smoke.", file=sys.stderr)
        return 2

    # Two binary model outputs with shape (classes, height, width).  Each pixel's
    # background channel is 1 - foreground, matching RoboSat's PNG convention.
    fg_a = np.array(
        [
            [0.10, 0.60, 0.50],
            [0.90, 0.20, 0.51],
        ],
        dtype=np.float32,
    )
    fg_b = np.array(
        [
            [0.20, 0.70, 0.40],
            [0.80, 0.10, 0.52],
        ],
        dtype=np.float32,
    )

    probs = [np.stack([1.0 - fg_a, fg_a]), np.stack([1.0 - fg_b, fg_b])]
    voted = softvote(probs, axis=0, weights=args.weights)

    expected = np.argmax(np.average(probs, axis=0, weights=args.weights), axis=0)
    if not np.array_equal(voted, expected):
        print("ERROR: softvote output did not match independent NumPy calculation", file=sys.stderr)
        print("voted=\n{}".format(voted), file=sys.stderr)
        print("expected=\n{}".format(expected), file=sys.stderr)
        return 1

    if args.weights is None:
        default_expected = np.array([[0, 1, 0], [1, 0, 1]])
        if not np.array_equal(voted, default_expected):
            print("ERROR: default smoke mask changed unexpectedly", file=sys.stderr)
            print("voted=\n{}".format(voted), file=sys.stderr)
            return 1

    if args.show_arrays:
        print("foreground_a=\n{}".format(fg_a))
        print("foreground_b=\n{}".format(fg_b))
        if args.weights:
            print("weights={}".format(args.weights))
        print("voted_mask=\n{}".format(voted.astype(np.uint8)))

    print("softvote smoke passed: shape={} classes={}".format(voted.shape, sorted(set(voted.ravel().tolist()))))
    return 0


if __name__ == "__main__":
    sys.exit(main())
