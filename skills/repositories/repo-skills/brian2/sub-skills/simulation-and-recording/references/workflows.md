# Simulation control workflows

These workflows were checked against Brian2 2.9.0's public running and
scheduling topics, core network/magic/clock/operation behavior, and focused
network and clock cases. The source topics are provenance only; follow the
public APIs shown here.

## 1. Use an explicit network by default for experiments

1. Construct groups, synapses, operations, and monitors.
2. Keep every top-level object in named variables; also keep objects created in
   lists/dicts or late phases.
3. Build `net = Network(group, synapses, operation, monitors)` (or
   `Network(collect())` followed by `net.add(hidden_objects)`) **before the
   first run**. Do not use this pattern to transfer objects already simulated
   by magic.
4. Inspect `net.schedule` or `net.scheduling_summary()` before a timing-
   sensitive run.
5. Run with units: `net.run(duration)`. For staged work, make each phase a
   separate `net.run(...)`; `net.t` continues from the prior endpoint.

The explicit membership is the repair for magic ambiguity, hidden containers,
late input sources, and monitor/snapshot membership that must be controlled
precisely. A built-in monitor is non-invalidating for magic continuation, but an
explicit network is still safer for stable train/test snapshots. A network may
include a parent object and its contained objects automatically; do not
manually add a contained state updater as an independent object.

## 2. Use magic for a simple visible scope

For a small script, create visible Brian objects and call `run(10*ms)`. A
second run with the same invalidating objects continues from the first run. A
new set of all-new objects starts at zero. `collect()` is the inspection step
when you need to see what magic will include.

Before creating a second independent model in the same Python process, call
`start_scope()` and create the new objects afterward. This changes collection
membership only; it is not a replacement for an explicit network when old
objects and new objects need to coexist, and it does not reset an explicit
network or restore object state.

## 3. Choose and audit clocks

Set `defaultclock.dt` before constructing most objects when a common regular
step is desired. Give a monitor or operation `dt=...` when it should run at a
lower sampling frequency. Use one explicitly created `Clock` when several
objects must share a later `dt` change. Use `EventClock([0*ms, 0.7*ms, ...])`
for sparse, predefined event times; times must have time units and no
duplicates.

Objects with different clocks are interleaved by the earliest current clock
time. Objects whose clocks have the same time are updated in schedule/order
sequence. A run's endpoint is represented by each clock's integer timestep;
check a proposed `dt` change is compatible with the current endpoint before
changing it.

## 4. Make scheduling intentional

The default slot order is `start → groups → thresholds → synapses → resets →
end`. Each object's `when` selects a slot and its `order` sorts ascending in
that slot. Use `before_<slot>` or `after_<slot>` for a precise boundary, or
insert a named custom slot into `net.schedule`; do not put `before_`/`after_`
names in the schedule itself.

Use `scheduling_summary(net)` before a timing-sensitive run and after changing
`active`, `when`, `order`, clock, or schedule. If a device has a fixed schedule,
Brian can warn when `net.schedule` differs; device/target decisions belong to
the code-generation route.

## 5. Integrate a control operation

Use a `NetworkOperation` or `@network_operation` for lightweight Python-side
control that should execute on the simulation clock. The callback can take no
argument or exactly one argument `t`. Pick `dt`, `clock`, `when`, and `order`
explicitly when it is not a default-start operation. Add the resulting object
to an explicit network. A callback can call `net.stop()` when it owns the
network, or global `stop()` when it deliberately stops the current run.

Example pattern:

```python
stopper = NetworkOperation(check_condition, dt=1*ms, when="end")
net = Network(group, monitor, stopper)
net.run(100*ms)
```

Keep callbacks small: inspect existing model/monitor state, update a bounded
control variable, or stop. Do not hide required Brian objects inside callback
closures and expect magic collection to discover them.

## 6. Add progress and profiling only when useful

For a user-facing long run, use `net.run(duration, report="text",
report_period=1*second)`. A custom callback receives real elapsed time,
completion fraction, biological start, and biological duration; it is called at
0 and 1 even when the run is shorter than the reporting period.

For a diagnostic run, use `net.run(duration, profile=True)` and then inspect
`net.profiling_info` or `profiling_summary(net, show=5)`. Profiling is timing
information for code objects, not a correctness metric. `profiling_summary()`
with no argument is for the magic network; pass `net` for explicit networks.
