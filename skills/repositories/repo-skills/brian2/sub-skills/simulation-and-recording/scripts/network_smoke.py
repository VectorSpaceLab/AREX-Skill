#!/usr/bin/env python3
"""Tiny explicit-Network and store/restore smoke for Brian2.

The script performs one short, in-memory run and replays it from a named
snapshot. It intentionally has no plotting, network access, source-checkout
assumptions, or output files.
"""

from __future__ import annotations

import argparse


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run a tiny explicit Brian2 Network store/restore smoke."
    )
    parser.add_argument(
        "--duration-ms",
        type=float,
        default=1.0,
        help="short positive simulation duration in milliseconds (default: 1)",
    )
    parser.add_argument(
        "--profile",
        action="store_true",
        help="collect and print a profiling summary for the smoke run",
    )
    parser.add_argument(
        "--report",
        action="store_true",
        help="print built-in text progress for the smoke run",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.duration_ms <= 0:
        raise SystemExit("--duration-ms must be positive")

    # Keep the import after argparse so --help and argument validation are
    # useful even when an installation's optional compiled extension is absent.
    from brian2 import (
        Network,
        NeuronGroup,
        defaultclock,
        ms,
        prefs,
        profiling_summary,
    )

    # Keep this smoke on the in-memory NumPy runtime. It is a core network
    # lifecycle check, not a Cython/compiler or standalone-device check.
    prefs.codegen.target = "numpy"
    defaultclock.dt = 0.1 * ms
    duration = args.duration_ms * ms
    group = NeuronGroup(
        1,
        "dv/dt = 1/ms : 1",
        method="euler",
        name="network_smoke_group",
    )
    group.v = 0
    net = Network(group, name="network_smoke")
    net.store("initial")

    run_kwargs = {
        "profile": args.profile,
        "report": "text" if args.report else None,
    }
    net.run(duration, **run_kwargs)
    first_value = float(group.v[0])
    first_time = net.t

    net.restore("initial")
    if net.t != 0 * ms or float(group.v[0]) != 0.0:
        raise RuntimeError("store/restore did not return the initial state")
    net.run(duration, **run_kwargs)
    second_value = float(group.v[0])
    second_time = net.t

    if first_time != second_time or first_value != second_value:
        raise RuntimeError("restored run did not reproduce the deterministic result")

    print(
        f"explicit Network OK: t={second_time}, "
        f"v={second_value:.6g}, objects={len(net)}"
    )
    if args.profile:
        print(profiling_summary(net, show=5))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
