# Simulation-control troubleshooting

The failure modes below were checked against Brian2 2.9.0's running,
computation, and scheduling topics, core network/magic/clock/operation behavior,
and focused network/clock cases. They preserve explicit boundaries for
recording and code-generation rather than treating those as simulation-control
failures.

## Install/import failures

**Symptom:** `import brian2` fails with a message that a Cython extension such
as `cythondynamicarray` or the C++/Cython spike queue is unavailable.

**Action:** Treat this as an environment/install problem, not as a network or
model bug. Verify the Python interpreter and Brian2 version, install Brian2 in
the intended environment (editable installs from a source checkout need their
Cython extensions built), and retry a tiny import. Do not work around the
error by importing internal modules or by linking a checkout path into a
future agent instruction. The target package for this skill is Brian2 2.9.0,
with import root `brian2` and Python >=3.12 as established by the build
context.

**Symptom:** the package imports but the selected code-generation backend is
missing or falls back unexpectedly.

**Action:** keep this route on runtime-control semantics and send target/device,
compiler, standalone, CUDA, or other backend build decisions to the
code-generation route. A runtime smoke should be able to use the supported
fallback when configured, but an absent required backend must remain explicit.

## Optional dependency failures

Compiled runtime paths can require Cython, a C/C++ compiler, or backend-specific
packages. Plotting is not required for `Network.run`; avoid adding plotting or
notebook dependencies merely to inspect `t`, snapshots, or schedules. If a
progress callback or profile diagnostic fails because of an optional UI or
backend dependency, replace it with the built-in text reporter or plain string
summary and record the limitation.

Do not infer that a successful Python import proves every optional device is
usable. Probe the chosen device separately and route device preparation/build
issues out to code-generation.

## Data and configuration failures

- `run` durations and `report_period` need time quantities; a negative duration
  raises `ValueError`.
- `Clock`/`EventClock` times must have time dimensions. `EventClock` times must
  be unique; duplicate times raise `ValueError`.
- `dt` and `clock` are mutually exclusive when constructing a Brian object.
  An object's clock is not replaceable after construction.
- A regular clock's `dt` change after time has advanced must represent the
  current time as an integer number of new steps. An incompatible change
  raises `ValueError`; choose a compatible step or a separate clock.
- A custom `Network.schedule` must be a sequence of strings. Do not assign
  `before_...`/`after_...` entries to the schedule; those are generated around
  existing slots. Retain every slot needed by contained objects (normally the
  default `start`, `groups`, `thresholds`, `synapses`, `resets`, and `end`
  slots), and use only a slot or a valid derived `before_`/`after_` position for
  each object's `when`.
- Snapshot files are pickle-like, version/platform-sensitive state artifacts.
  The object names and network structure must match at restore time. Missing or
  extra objects produce restore errors. Do not load untrusted state files.

## API misuse

**Magic mixed old/new error:** If a magic run has both previously simulated
invalidating objects and new invalidating objects, Brian raises `MagicError`
because it cannot know whether to continue or start over. Do not use
`Network(collect())` *after* this error to transfer the old objects: they already
belong to the magic network and cannot be run by a new network. For future
runs, recreate the model and build complete explicit membership before its first
run:

```python
objects = collect()              # before any run
net = Network(objects)
net.add(objects_hidden_in_a_container)
net.run(duration)
```

`Network(collect())` fixes visibility only for objects currently visible; it
does not discover arbitrary lists/dicts that magic omitted. If the old magic
network must continue, remove the new invalidating objects from the active
scope and keep its membership consistent instead.

**Hidden objects:** a list of monitors or a dict of operations is not fully
seen by magic. Keep the container and call `net.add(container)` on an explicit
network. `Network.add` recursively accepts containers and mapping values.

**Late add/remove:** an object that has been simulated cannot be added to a
new network. An unrun monitor may be added to the same explicit network when its
source/dependencies are already present, but it is absent from snapshots taken
before the add. Do not remove a simulated object just to pause it; set
`active=False` and restore it later. Build a stable network for train/test
phases.

**Callback signature:** `NetworkOperation` callbacks take zero arguments or
exactly one time argument. More arguments, or applying `@network_operation` to
an instance method, raises `TypeError`. Use an explicit `NetworkOperation` for
bound methods. Add the returned operation to the explicit network.

**Wrong diagnostics target:** `profiling_summary()` and
`scheduling_summary()` without an argument inspect magic. Pass `net` for an
explicit network. Profiling requires `run(profile=True)` first; otherwise
`profiling_summary(net)` raises `ValueError`.

## Workflow failures

**Unexpected restart:** a new explicit `Network` starts at zero; a repeated
`net.run` continues. Magic decides by object membership. Use `net.t` and
`collect()` to verify, or use one explicit network.

**Snapshot does not replay stochastic behavior:** `restore()` does not restore
random state by default. Use `restore(restore_random_state=True)` for exact
replay, and remember that Brian restores runtime/NumPy state but not Python's
`random` module. Use `from brian2 import seed; seed(integer)` for a controlled
Brian runtime stream and seed Python's `random` module separately if needed.

**Late monitor or late input:** built-in monitors are non-invalidating, so a
late monitor alone does not cause magic ambiguity; it is still absent from any
earlier snapshot and cannot recover earlier activity. Construct it before the
first snapshot and toggle `active`, or add an unrun monitor to the same explicit
network and take a new snapshot afterward. A late invalidating input, synapse,
or group can cause `MagicError`; construct the complete explicit network before
the first run, or recreate the model if objects have already run in magic.

**Callback is not called:** confirm it is in the network, `active` is true, its
clock reaches the run interval, and its `when` slot is in the network schedule.
An operation can also stop its owning network early; inspect `net.t` after the
run.

**Wrong ordering:** print `scheduling_summary(net)`, check `when`, `order`,
clock `dt`, and `active`, then check `net.schedule`. Same-slot/order ties are
resolved by object name, so assign explicit orders when sequence matters.

**Progress appears only at start/end:** callbacks are periodic in wall-clock
`report_period`, not every simulated step. Use a shorter period for a visible
long run, or inspect `net.t` in a scheduled operation for simulation-time
control.
