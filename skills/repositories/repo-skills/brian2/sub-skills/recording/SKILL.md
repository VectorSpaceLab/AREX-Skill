---
name: recording
description: "Record Brian2 2.9.0 spikes, state variables, custom events, rates,
  subsets, and monitor data with explicit timing, memory, and export choices."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Brian2 recording

Use this route after the model and its inputs/events exist. It owns monitor
selection, recording semantics, timing of observations, monitor data access,
subsets, rates, and export. It does **not** own model equations or the run
lifecycle.

## Route quickly

- Read [API reference](references/api-reference.md) for constructor arguments,
  shapes, units, indexing, event/spike summaries, `EventClock`, endpoint
  sampling, and rate methods.
- Read [workflows](references/workflows.md) for the attach/run/validate pattern,
  late monitors, timing diagnosis, subgroup recording, and export.
- Read [data and memory](references/data-and-memory.md) before using
  `record=True`, recording many variables, or keeping a long trace.
- Read [troubleshooting](references/troubleshooting.md) for import and optional
  dependency failures, missing variables/events, timing shifts, standalone
  limits, and data/configuration mistakes.
- Run the plotting-free tiny contract with
  `python scripts/monitor_smoke.py --help`, then
  `python scripts/monitor_smoke.py` in an installed Brian2 2.9.0 environment.

## Choose the monitor

- `SpikeMonitor(source, variables=None, record=True, when=None, order=None)`
  records spike indices/times and per-source-neuron counts. Set `record=False`
  when only counts are needed.
- `EventMonitor(source, event, variables=None, record=True, when=None,
  order=None)` records a named event declared by the source. It is the route
  for custom events; `SpikeMonitor` is the spike-event specialization.
- `StateMonitor(source, variables, record, dt=None, clock=None,
  when="start")` records selected state variables as time-by-index arrays.
  `record=True` means every source index and may consume substantial memory.
- `PopulationRateMonitor(source)` records the instantaneous population rate at
  the source clock resolution. Use `binned_rate` or `smooth_rate` after the
  run for derived rates.

## Safe operating sequence

1. Create the monitor before the run and keep a strong reference. Prefer an
   explicit `Network` when monitors are created, activated, or removed between
   runs; a monitor cannot recover events or state values from before it was
   attached.
2. Choose the smallest set of variables, indices, source subgroup, and time
   resolution needed. For `StateMonitor`, `record=[...]` and a slower `dt`
   are usually safer than `record=True` at the source clock.
3. Decide `when`, `order`, and `dt` deliberately when a value can change from
   integration, thresholding, reset, event handlers, or same-step code. The
   default `StateMonitor` slot is `start`; spike/event monitors follow the
   emitted event; `PopulationRateMonitor` records at `end`. For a final
   post-run state, initialize the monitor with a run and then use
   `record_single_timestep()` rather than shifting the time array.
4. Run through the simulation lifecycle route, then check time origin,
   counts, array shape, units, and subgroup index meaning before analysis. For
   a late monitor, distinguish the population-rate bin origin from the
   spike/event binning behavior described in the API reference.
5. Export selected monitor state with `get_states(...)` (copies) rather than
   internal storage. Preserve units and the recording metadata; use
   `units=False` only when the consumer explicitly requires unitless arrays.
6. For a long run, checkpoint or export a bounded segment, stop/deactivate or
   remove the monitor, release its arrays, and attach a new monitor for the
   next segment. Do not silently retain all segments in memory.

## Boundaries

- Network construction, `run`, clocks, schedules, `active`, `store`/`restore`,
  devices, and execution lifecycle route to **simulation-and-recording**.
- NeuronGroup/Synapses equations, thresholds, resets, custom event definition,
  inputs, and subgroup/model construction route to **modeling/synapses-and-inputs**.
- Plotting packages, GUI backends, and figure rendering route to the root
  troubleshooting route. This skill and its smoke script intentionally do not
  plot.

## Acceptance gates

A recording is usable only when the monitor was attached to the intended
source, the first and last times are understood, the array shape matches the
selected indices, and units or the unitless conversion are explicit. Treat
`record=False`, an empty `record` selection, incomplete final bins, a monitor
attached mid-run, and standalone result deletion as intentional choices that
must be documented in the handoff or experiment output.
