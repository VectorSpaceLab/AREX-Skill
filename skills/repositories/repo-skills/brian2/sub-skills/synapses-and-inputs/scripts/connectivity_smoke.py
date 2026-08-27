#!/usr/bin/env python3
"""Tiny, deterministic Brian2 synapse/input smoke check.

This only uses the runtime NumPy target and in-memory groups. It verifies that
explicit connections, per-synapse weights, a propagation delay, and source
spikes produce the expected target state. Use --help for the safe parser check.
"""

from __future__ import annotations

import argparse

import numpy as np


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run a tiny deterministic Brian2 connectivity smoke check."
    )
    parser.add_argument(
        "--tiny",
        action="store_true",
        help="Use the default two-edge fixture (kept for harness compatibility).",
    )
    return parser


def run_smoke() -> None:
    from brian2 import (
        Network,
        NeuronGroup,
        SpikeGeneratorGroup,
        Synapses,
        defaultclock,
        ms,
        prefs,
        start_scope,
    )

    start_scope()
    prefs.codegen.target = "numpy"
    defaultclock.dt = 0.1 * ms

    # Two explicit source events drive the opposite target neurons. The times
    # and delay are all integer multiples of dt, so the expected bins are clear.
    source = SpikeGeneratorGroup(2, indices=[0, 1], times=[0.3, 0.7] * ms)
    target = NeuronGroup(2, "v : 1")
    syn = Synapses(source, target, model="w : 1", on_pre="v_post += w", delay=0.2 * ms)
    syn.connect(i=[0, 1], j=[1, 0])
    syn.w = [0.25, 0.5]

    assert len(syn) == 2, f"expected two connections, got {len(syn)}"
    np.testing.assert_array_equal(syn.i[:], [0, 1])
    np.testing.assert_array_equal(syn.j[:], [1, 0])
    np.testing.assert_allclose(syn.delay[:], [0.2, 0.2] * ms)
    np.testing.assert_allclose(syn.w[:], [0.25, 0.5])

    net = Network(source, target, syn)
    net.run(1.2 * ms)
    # 0 -> 1 carries 0.25 and 1 -> 0 carries 0.5.
    np.testing.assert_allclose(target.v[:], [0.5, 0.25], rtol=0, atol=1e-12)

    print("connectivity smoke passed: 2 edges, delayed events, weights asserted")


def main() -> None:
    args = build_parser().parse_args()
    # --tiny intentionally selects the same bounded fixture; accepting it makes
    # the script convenient for generic skill harnesses without changing scope.
    if args.tiny:
        run_smoke()
    else:
        run_smoke()


if __name__ == "__main__":
    main()
