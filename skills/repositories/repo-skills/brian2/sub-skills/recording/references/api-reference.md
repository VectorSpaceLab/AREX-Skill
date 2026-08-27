# Recording API reference

This route targets Brian2 2.9.0 and the public import root `brian2`.

```python
from brian2 import (
    EventMonitor, PopulationRateMonitor, SpikeMonitor, StateMonitor,
)
```

All monitors are Brian objects/groups. Keep them in an explicit `Network` when
objects are held in containers or are added after an initial run.

## SpikeMonitor and EventMonitor

```python
SpikeMonitor(
    source, variables=None, record=True, when=None, order=None,
    name="spikemonitor*", codeobj_class=None,
)
EventMonitor(
    source, event, variables=None, record=True, when=None, order=None,
    name="eventmonitor*", codeobj_class=None,
)
```

- `source` must emit the relevant event. A spike monitor is for a spiking
  source; it is not a monitor for a `Synapses` object. `EventMonitor` requires
  an event name present in `source.events`.
- `variables` is one name or a sequence of names sampled at event time. The
  source variable must exist. `SpikeMonitor(..., variables="v")` exposes
  `mon.v` alongside `mon.i` and `mon.t`.
- With `record=True`, `i` and `t` contain every event. `i` is a source-relative
  integer index and `t` is a unit-bearing time array. The underscore forms
  (`i_`, `t_`, and recorded variable names ending in `_`) expose raw unitless
  arrays. `mon.it` and `mon.it_` return the corresponding pairs.
- With `record=False`, the monitor still maintains `count` and the total
  (`num_spikes` for `SpikeMonitor`, `num_events` for `EventMonitor`) but does
  not expose `i` or `t`. Extra `variables` can still be recorded per event.
- `count` has one entry per neuron in the monitored source (for a subgroup,
  these are subgroup-relative entries). `num_spikes`/`num_events` equals the
  sum of that count.
- `spike_trains()` and `event_trains()` return a dictionary from valid local
  source indices to sorted time arrays. `values("v")` returns a dictionary of
  per-index values at event time; `all_values()` returns all recorded event
  variables grouped the same way. These methods require event indices/times,
  so they are unavailable when `record=False`.
- `binned_rate(bin_size)` returns `(bin_starts, rates)`. For an event/spike
  monitor, `rates` has shape `(len(source), number_of_bins)` and unit `Hz`.
  Each bin time is its **start**, not its center; `bin_size` must be a
  multiple of the monitor clock `dt`.

Example for event-time state capture:

```python
spikes = SpikeMonitor(group, variables="v", when="after_thresholds")
# after a run:
threshold_values = spikes.values("v")
all_event_values = spikes.all_values()
```

Use `when`/`order` only with a clear schedule. If `when` is omitted, the
monitor follows the source's event-emission slot and records immediately after
that event. If an explicit `order` is supplied, also supply `when`.

## StateMonitor

```python
StateMonitor(
    source, variables, record, dt=None, clock=None, when="start", order=0,
    name="statemonitor*", codeobj_class=None,
)
```

- `variables` is a string, a sequence of strings, or `True` for all source
  equation variables. `record` is `True` (all source indices), `False` (none),
  one integer, or an explicit integer sequence. Validate the selected indices
  before a large run.
- `dt` and `clock` are alternative ways to choose the monitor clock; do not
  provide both. If neither is provided, the source clock is used. A slower
  explicit `dt` reduces storage and is often sufficient for analysis. Use an
  `EventClock(times=...)` when samples are needed at explicit, possibly
  irregular times.
- The default `when="start"` records at the beginning of a time step. The
  visible trace therefore represents pre-integration values at that slot, and
  after a prior step's reset. To capture a threshold-crossing value before its
  reset, choose an appropriate later slot such as `before_resets` and verify
  the schedule/order.
- After the run, `mon.t` has shape `(T,)` and each recorded variable `mon.v`
  has shape `(R, T)`, where `R` is the number of selected source indices.
  Arrays carry Brian units; `mon.t_` and `mon.v_` are unitless NumPy-style
  views/copies for consumers that explicitly need them.
- `mon.v[k]` uses **relative recorded-row** indexing. If `record=[2, 5]`,
  `mon.v[1]` is source index 5. `mon[5].v` uses the source's **absolute**
  index and returns the same row. `mon[4]` raises `IndexError` because source
  index 4 was not recorded. This distinction also applies to slices/arrays.
- The monitor can record Synapses variables, where indices are synapse
  indices, not neuron indices. In standalone workflows, prefer explicit
  synapse index arrays rather than `record=True` when the number of synapses
  is not known until generated code runs.
- `record_single_timestep()` appends one sample at the current time, but only
  after the monitor has been initialized by a run (a zero-duration run is
  enough to initialize it). It is useful for an end-of-run value because the
  default `start` monitor does not sample after the last integration step.

## PopulationRateMonitor and RateMonitor methods

```python
PopulationRateMonitor(source, name="ratemonitor*", codeobj_class=None,
                       dtype=numpy.float64)
```

`PopulationRateMonitor` exposes `t` and one-dimensional `rate` arrays. It
samples at the source clock and computes instantaneous population firing rate:
spikes in the step divided by the number of source neurons and the step
length. A subgroup's denominator and output refer to that subgroup.

- `binned_rate(bin_size)` returns `(bin_starts, rate)`, both with time/rate
  units. Bins are non-overlapping and their times are starts. Only complete
  bins are returned; a partial trailing interval is omitted. For a
  `PopulationRateMonitor` attached mid-run, the first bin starts at the first
  recorded monitor time. Do not generalize that origin to `SpikeMonitor` or
  `EventMonitor`: their binned-rate grid is derived from the source clock's
  elapsed timestep and starts at time zero, so leading empty bins can appear
  after a late attachment.
- `smooth_rate(window="gaussian", width=...)` or
  `smooth_rate(window="flat", width=...)` smooths at the original `dt`; it
  does not re-bin. The output length equals the raw recorded rate length.
  A custom NumPy window must be one-dimensional with an odd number of values;
  it is normalized automatically and cannot be combined with `width`.
- Predefined windows require `width`. `width` must be a Brian time quantity.
  `smooth_rate` uses NumPy convolution and does not require plotting or SciPy.
  The warning in the public API applies if recorded values have varying `dt`.

`SpikeMonitor` and `EventMonitor` inherit the same rate methods. Their smoothed
or binned output is two-dimensional `(source_neurons, time_bins)` rather than
the population monitor's one-dimensional output. For these event monitors,
a late attachment can therefore produce leading zero bins; retain the
attachment time with the export.

## State export methods

Monitors inherit the state export interface:

```python
states = monitor.get_states(["t", "v"], units=True)
raw_states = monitor.get_states(["t", "v"], units=False)
```

The returned data are copies. An explicit variable list is safer than exporting
every internal/public value. For a `StateMonitor`, exported multi-dimensional
variable storage follows the import/export orientation (time first), so check
`states["v"].shape` rather than assuming it matches the user-facing
`mon.v.shape`; the public attribute remains `(recorded_index, time)`.
`get_states()` includes public state such as `N` unless a variable list is
provided. Preserve the chosen `record` indices, source size, monitor `dt`,
`when`, and units beside an export.
