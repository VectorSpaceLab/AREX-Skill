#!/usr/bin/env python3
"""Run a tiny plotting-free contract for Brian2 monitor recording."""

from __future__ import annotations

import argparse
import sys

import numpy as np


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check tiny deterministic SpikeMonitor, StateMonitor, "
            "EventMonitor, and PopulationRateMonitor recordings."
        )
    )
    parser.add_argument(
        "--duration-ms",
        type=float,
        default=3.0,
        help="Whole-number runtime from 1 to 10 ms (default: 3.0).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if (
        args.duration_ms < 1
        or args.duration_ms > 10
        or not args.duration_ms.is_integer()
    ):
        raise SystemExit("--duration-ms must be a whole number from 1 to 10")

    try:
        from brian2 import (
            EventMonitor,
            Network,
            NeuronGroup,
            PopulationRateMonitor,
            SpikeGeneratorGroup,
            SpikeMonitor,
            StateMonitor,
            defaultclock,
            ms,
            prefs,
            start_scope,
        )
    except ImportError as exc:
        raise SystemExit(
            "Brian2 could not be imported. Install Brian2 2.9.0 in this "
            "Python environment before running the monitor smoke."
        ) from exc

    start_scope()
    # Keep all clocks tiny and deterministic; use NumPy and avoid compilation.
    prefs.codegen.target = "numpy"
    defaultclock.dt = 0.1 * ms
    duration = args.duration_ms * ms
    spike_times_ms = (0, 1, 2)
    spike_indices = (0, 1, 0)
    expected_spike_counts = [
        sum(index == neuron and time_ms < args.duration_ms
            for index, time_ms in zip(spike_indices, spike_times_ms))
        for neuron in range(2)
    ]
    expected_spikes = sum(expected_spike_counts)
    expected_samples = int(args.duration_ms)
    expected_events = expected_samples * 10  # event source runs at 0.1 ms

    spike_source = SpikeGeneratorGroup(
        2,
        indices=spike_indices,
        times=list(spike_times_ms) * ms,
        dt=1 * ms,
    )
    spike_monitor = SpikeMonitor(spike_source)
    rate_monitor = PopulationRateMonitor(spike_source)

    state_source = NeuronGroup(
        2,
        "dv/dt = (1 - v) / (1 * ms) : 1",
        method="exact",
    )
    state_source.v = 0
    state_monitor = StateMonitor(state_source, "v", record=[1], dt=1 * ms)

    event_source = NeuronGroup(
        1,
        "x : 1",
        events={"pulse": "x > 0.5"},
    )
    event_source.x = 1
    event_monitor = EventMonitor(event_source, "pulse")

    network = Network(
        spike_source,
        spike_monitor,
        rate_monitor,
        state_source,
        state_monitor,
        event_source,
        event_monitor,
    )
    network.run(duration)

    # SpikeMonitor: individual events, counts, and per-neuron trains.
    assert int(spike_monitor.num_spikes) == expected_spikes
    assert spike_monitor.i.shape == (expected_spikes,)
    assert spike_monitor.t.shape == (expected_spikes,)
    trains = spike_monitor.spike_trains()
    assert [len(trains[neuron]) for neuron in range(2)] == expected_spike_counts
    assert int(np.sum(spike_monitor.count[:])) == expected_spikes

    # StateMonitor: sparse selection is one compact row and one sample per ms.
    assert state_monitor.v.shape == (1, expected_samples)
    assert state_monitor.t.shape == (expected_samples,)
    assert np.allclose(state_monitor[1].v[:], state_monitor.v[0, :])
    assert state_monitor.t[0] == 0 * ms

    # EventMonitor: custom event counts and event arrays are available.
    assert int(event_monitor.num_events) == expected_events
    assert int(event_monitor.num_events) == int(np.sum(event_monitor.count[:]))
    assert event_monitor.num_events > 0
    assert event_monitor.i.shape == event_monitor.t.shape

    # Population rates and derived rates have matching time dimensions. Use
    # slices here because dynamic VariableView shape metadata can lag until a
    # value is explicitly accessed (notably in standalone mode).
    rate_values = rate_monitor.rate[:]
    rate_times = rate_monitor.t[:]
    assert len(rate_values) == len(rate_times) == expected_samples
    bins, binned = rate_monitor.binned_rate(1 * ms)
    assert np.asarray(bins).shape == np.asarray(binned).shape == (expected_samples,)
    smoothed = rate_monitor.smooth_rate(window="flat", width=1 * ms)
    assert len(smoothed) == len(rate_values)

    print(
        "monitor smoke passed: "
        f"spikes={int(spike_monitor.num_spikes)} "
        f"events={int(event_monitor.num_events)} "
        f"state_shape={state_monitor.v.shape} "
        f"rate_samples={len(rate_values)}"
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AssertionError as exc:
        print(f"monitor smoke failed: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
