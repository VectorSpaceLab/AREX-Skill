# Recording workflows

These examples are intentionally plotting-free. Analysis can consume the
returned arrays later; recording itself does not require Matplotlib.

## 1. Attach, run, and validate

Use an explicit network if a monitor is stored in a list, is added after a
first run, or will be removed later.

```python
import numpy as np
from brian2 import *

start_scope()
group = NeuronGroup(
    4,
    "dv/dt = (drive - v) / tau : 1\n drive : 1\n tau : second",
    threshold="v > 1",
    reset="v = 0",
    method="exact",
)
group.tau = 5 * ms
group.drive = [0.8, 1.1, 1.4, 1.8]
group.v = 0

spikes = SpikeMonitor(group, record=True)
states = StateMonitor(group, "v", record=[1, 3], dt=1 * ms)
rates = PopulationRateMonitor(group)
network = Network(group, spikes, states, rates)
network.run(10 * ms)

assert int(spikes.num_spikes) == int(np.sum(spikes.count[:]))
assert states.v.shape == (2, len(states.t))
assert len(rates.rate[:]) == len(rates.t[:])
assert states.t[0] == 0 * ms
```

The model and input definitions belong to the modeling/input route; the key
recording contract is that monitors are included in the same network that is
run and are checked before interpretation.

## 2. Record only a segment

A monitor records only while it exists and is active. It does not backfill
values from an earlier run.

```python
network = Network(group)
network.run(1 * second)              # no monitor yet
states = StateMonitor(group, "v", record=[0], dt=10 * ms)
network.add(states)
network.run(2 * second)              # states.t starts at the attach time
# Either pause the existing monitor:
states.active = False
network.run(1 * second)
# Or export, remove, and release it before a later segment:
segment = states.get_states(["t", "v"])
network.remove(states)
del states
next_states = StateMonitor(group, "v", record=[0], dt=10 * ms)
network.add(next_states)
```

For a short magic-network script, `monitor.active = False/True` is also useful,
but explicit `Network` membership makes the lifecycle unambiguous. A late
`PopulationRateMonitor` similarly begins its first rate sample at its own
attachment time, and a late `SpikeMonitor` misses earlier spikes.

## 3. Diagnose a shifted trace

When a trace appears one step early/late, write down these four times:

1. source clock `dt` and monitor `dt` (or clock),
2. monitor creation/attachment time,
3. monitor `when` and `order`,
4. the slots that update, threshold, reset, and handle events.

The default `StateMonitor(..., when="start")` samples before the current
step's group update and threshold/reset slots. It is therefore normal that a
trace's last sample is the state at the beginning of the last step, not the
final post-update state. Choose `when="before_resets"` (or another deliberate
slot) to observe a thresholded value before reset, then use
`scheduling_summary(network)` and a tiny run to verify the result. Do not fix a
shift by manually moving the time array.

If an event monitor samples a variable, its default timing follows event
emission and records immediately after that event. To distinguish pre- and
post-reset values, make `when` explicit for the monitor and for any event
handler, and use `order` only within a known slot.

## 4. Relative versus absolute StateMonitor indexing

Use the two indexing forms intentionally:

```python
states = StateMonitor(group, "v", record=[2, 5])
network.add(states)
network.run(2 * ms)

relative_row_for_source_5 = states.v[1]
absolute_source_5 = states[5].v
assert np.allclose(relative_row_for_source_5, absolute_source_5)
# states[4] is an error: source index 4 was not recorded.
```

The attribute (`states.v`) indexes rows of the compact recorded array. The
monitor (`states[5]`) maps a source index to its recorded row. For a source
subgroup, the monitor's source indices are relative to that subgroup.

## 5. Custom events and event-time variables

Define an event in the model/input route, then observe it here:

```python
group = NeuronGroup(
    2,
    "x : 1\nvalue_at_event : 1",
    events={"pulse": "x > 0.5"},
)
group.x = 1
events = EventMonitor(group, "pulse", variables="x")
network = Network(group, events)
network.run(2 * ms)
assert int(np.sum(events.count[:])) == events.num_events
pulse_times = events.event_trains()
pulse_values = events.values("x")
```

If the named event is not declared, creation fails. If the event condition is
true on many steps, repeated events are expected; add a model-side reset,
refractory rule, or edge condition when a one-shot event is intended.

## 6. Per-neuron and population rates

Use a spike/event monitor for a matrix of per-source-neuron rates and a
population monitor for one population-average time series:

```python
bins, per_neuron = spikes.binned_rate(10 * ms)
assert per_neuron.shape[0] == len(spikes.source)

population_bins, population_rate = rates.binned_rate(10 * ms)
smoothed = rates.smooth_rate(window="gaussian", width=5 * ms)
assert smoothed.shape == rates.rate.shape
```

The bin arrays contain starts. Add `bin_size / 2` only for a display convention;
do not treat that shifted display coordinate as the event time. `bin_size` must
be an integer multiple of the clock `dt`; trailing incomplete bins are omitted.
A late `PopulationRateMonitor` bins from its first recorded time, whereas a
late `SpikeMonitor`/`EventMonitor` can return leading zero bins on the elapsed
source-clock grid; preserve the attachment time and do not merge those grids
without an explicit alignment rule. For custom smoothing, pass an odd-length
one-dimensional NumPy array without a `width` argument.

## 7. Subgroup recording

`SpikeMonitor`, `EventMonitor`, and `PopulationRateMonitor` can observe a
contiguous subgroup directly:

```python
selected = group[100:120]
sub_spikes = SpikeMonitor(selected)
sub_rate = PopulationRateMonitor(selected)
network = Network(group, sub_spikes, sub_rate)
```

Indices in `sub_spikes.i` are relative to `selected`, not the parent group.
`sub_rate` is one population-rate series whose denominator is `len(selected)`;
it has no per-neuron rows. `StateMonitor` instead accepts an explicit
parent-index list, so use
`record=[100, 104, 119]` when arbitrary parent indices are needed. If physical
position matters, do not confuse shuffled/contiguous storage order with model
position; keep a model variable for the semantic index.

For a non-contiguous spike/event subset, define a second custom event with a
constant boolean mask and monitor that event. This evaluates the event
condition separately; if the source uses refractoriness, include
`not_refractory` in the custom-event condition yourself because Brian only
adds it automatically to the main threshold event:

```python
subset = NeuronGroup(
    4,
    "v : 1\nrecord_this : boolean (constant)",
    threshold="v > 1",
    reset="v = 0",
    events={"recorded_spike": "v > 1 and record_this"},
)
subset.record_this = [True, False, True, False]
selected_events = EventMonitor(subset, "recorded_spike")
network = Network(subset, selected_events)
```

`PopulationRateMonitor` has no arbitrary index-list argument; use a contiguous
subgroup or maintain an explicitly aggregated quantity for a non-contiguous
population summary.
