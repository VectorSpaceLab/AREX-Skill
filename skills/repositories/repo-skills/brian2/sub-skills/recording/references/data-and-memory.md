# Monitor data, serialization, and memory

Monitor arrays are the experiment's data product, not a free diagnostic. Plan
storage before running a large network.

## Estimate and bound storage

For a `StateMonitor`, the approximate payload is

`number_of_variables × number_of_recorded_indices × number_of_samples × itemsize`.

The source implementation stores dynamic arrays and grows them as samples are
recorded. A single variable for a large population at the source `dt` can reach
many gigabytes. Spike/event arrays grow with event count and store indices,
times, and any requested event variables. A population rate monitor stores only
one rate and one time value per source-clock sample.

Use these controls, in order:

1. record only the variables needed for the analysis;
2. pass explicit `record=[...]` indices to `StateMonitor` instead of `True`;
3. use a slower monitor `dt` or a dedicated `clock` where resolution permits;
4. use a contiguous subgroup for spike/event/population monitors; for a
   non-contiguous spike/event subset, define a masked custom event rather than
   pretending a parent-index list is supported (see workflows);
5. use `SpikeMonitor(record=False)` or `EventMonitor(record=False)` for counts
   only when individual events are unnecessary;
6. use `PopulationRateMonitor` or an explicitly maintained aggregate when the
   analysis needs a population summary, not every trace;
7. split a long runtime run into exported segments and release each segment
   before the next one. This remove/recreate memory strategy is not available
   in C++ standalone; plan explicit output there and clean generated results
   only after post-run access.

`StateMonitor(..., variables=True, record=True)` is an especially broad choice:
it includes all equation variables and all source indices and should be treated
as an explicit high-memory decision.

## Export selected state

`get_states` returns copies, so it is safe to serialize and then release the
monitor's live arrays:

```python
import pickle

import numpy as np

states = monitor.get_states(["t", "v"], units=True)
metadata = {
    "record_indices": list(np.asarray(monitor.record, dtype=int)),
    "when": monitor.when,
    "dt": monitor.clock.dt,
}
with open("segment-000.pickle", "wb") as handle:
    pickle.dump({"states": states, "metadata": metadata}, handle)
```

The exact output format is a Brian dictionary of copies. For a `StateMonitor`,
public `monitor.v` is shaped `(recorded_index, time)`, while exported state
storage can be time-first; inspect each shape before writing downstream code.
Keep `units=True` unless the consumer has a documented unit convention. A
unitless export is deliberate:

```python
raw = monitor.get_states(["t", "v"], units=False)
# Equivalently for direct access: monitor.t_, monitor.v_
```

When using `units=False`, store the dimensions or a unit manifest next to the
arrays. Do not infer a quantity's unit from its numeric magnitude. `i` and
counts are already integer/index data; `t_` and variable underscore forms are
raw SI-scaled arrays rather than display values.

`get_states` can also be called without a variable list, but that may include
public read-only values such as `N` and is less stable as an interchange
contract. Select names explicitly for durable files.

## Export versus Network.store

These operations serve different purposes:

- `monitor.get_states(...)` exports copies for analysis or documentation.
  It does not make an executable continuation checkpoint.
- `Network.store(name, filename=None)` captures internal object/clock state for
  a later `restore`. All objects must already exist with the same names when
  restoring. Equations and thresholds are not serialized, and the stored
  format is not promised across Brian versions or platforms. It also captures
  runtime state such as undelivered spikes, so it is not a substitute for a
  selected monitor-data export.
- C++ standalone does not support the `Network.store`/`restore` mechanism.
  Choose an explicit data export after the compiled run instead.

For a reproducible analysis artifact, save the monitor data plus source size,
selected indices, monitor `dt`, `when`, variable names, units policy, and the
Brian version used. A checkpoint alone does not record those semantic choices.

## Segment and release a long recording

With an explicit `Network`, export before releasing:

```python
segment = monitor.get_states(["t", "v"])
# write segment to a durable file here
network.remove(monitor)
del monitor
# create a new monitor for the next interval and add it to network
```

If the object is not removed from an explicit network, the network can retain
it even after a local `del`. Setting `monitor.active = False` pauses recording
without freeing existing arrays; use removal and release when memory is the
priority. Delete or overwrite only files owned by the experiment, never an
unknown path.

For a standalone run, generated result files back monitor/state access after
the program has run. Do not rely on reading dynamically created values from
Python before the compiled program executes. Runtime monitor removal/recreation
is not a standalone memory-management strategy; choose bounded/generated
outputs in the standalone program instead. After analysis, a device data
cleanup operation can invalidate all monitor/state access; perform and save
analysis first. Standalone output can also occupy substantial disk space even
when Python heap usage looks small.

## Subsets and unitless consumers

A selected subgroup changes the local meaning of event `i`/`count` and the
population-rate denominator; `PopulationRateMonitor.rate` is one series, not
per-neuron rows. Store the parent range alongside the data. A selected
`StateMonitor` index list changes the row mapping but not the parent indices
used by `monitor[index]`.
For a non-contiguous event subset, store the mask and custom-event name with the
export; the event condition is evaluated separately from the main threshold.
For a unitless consumer, export `units=False` and write a small manifest rather
than silently stripping units from a Brian `Quantity`. This is particularly
important when mixing dimensionless state variables, volts/amps, and rates.
