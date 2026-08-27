#!/usr/bin/env python3
"""Build and validate a tiny Brian2 model without plotting or network I/O."""

from __future__ import annotations

import argparse
import sys

import numpy as np


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build a tiny heterogeneous Brian2 LIF population with a threshold, "
            "reset, refractory period, subgroup initialization, shared input, "
            "and a custom event."
        )
    )
    parser.add_argument(
        "--target",
        default="numpy",
        choices=("numpy",),
        help="Brian2 runtime target; this safe smoke intentionally supports NumPy only.",
    )
    parser.add_argument(
        "--duration-ms",
        type=float,
        default=4.0,
        help="Positive simulation duration in milliseconds (default: 4.0).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.duration_ms <= 0:
        raise SystemExit("--duration-ms must be positive")

    try:
        from brian2 import Network, NeuronGroup, ms, prefs, start_scope
    except ImportError as exc:
        raise SystemExit(
            "Brian2 could not be imported. Install Brian2 in this Python environment "
            "before running the smoke."
        ) from exc

    start_scope()
    prefs.codegen.target = args.target

    group = NeuronGroup(
        6,
        """
        dv/dt = (drive + shared_bias - v) / tau : 1 (unless refractory)
        drive : 1
        tau : second
        shared_bias : 1 (shared)
        event_count : integer
        """,
        threshold="v > 1",
        reset="v = 0",
        refractory=0.5 * ms,
        events={"high_voltage": "v > 0.8"},
        method="euler",
        dt=0.1 * ms,
        namespace={},
    )
    group.shared_bias = 0.0
    group.drive = np.linspace(1.4, 1.9, len(group))
    group.v = 0.0
    group.event_count = 0

    # Subgroups are views: these assignments must update parent storage.
    fast = group[:3]
    slow = group[3:]
    fast.tau = 1.0 * ms
    slow.tau = 2.0 * ms
    assert np.allclose(group.tau_[:3], 1.0e-3)
    assert np.allclose(group.tau_[3:], 2.0e-3)

    group.run_on_event("high_voltage", "event_count += 1")
    network = Network(group)
    network.run(0 * ms, namespace={})  # validate strings/namespaces early
    network.run(args.duration_ms * ms, namespace={})

    # The event code and reset must have had observable effects.
    assert np.any(group.event_count_ > 0), "custom event never executed"
    assert np.any(group.v_ < 0.8), "reset/refractory behavior left no subthreshold state"
    assert network.t == args.duration_ms * ms, "network did not advance expected duration"

    print(
        "model smoke passed: "
        f"target={args.target} duration_ms={args.duration_ms:g} "
        f"event_counts={group.event_count_[:].tolist()}"
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AssertionError as exc:
        print(f"model smoke failed: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
