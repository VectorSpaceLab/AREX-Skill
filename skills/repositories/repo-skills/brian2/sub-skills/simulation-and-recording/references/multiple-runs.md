# Multiple runs, trials, and snapshots

These trial and snapshot rules were checked against Brian2 2.9.0's running
and computation topics, network/magic implementation behavior, and focused
store/restore, random-state, and clock cases. The source topics are provenance
only; the state format remains version-sensitive.

## Continue versus restart

`Network.run` always advances from the network's current `t`; it never rewinds
by assigning to a clock. Two calls on the same explicit network therefore form
one continued simulation. A fresh `Network` starts at zero. With magic calls,
Brian infers whether all invalidating objects are new or all belong to the
previous magic run. Do not rely on that heuristic in staged experiments.

`start_scope()` starts a new magic collection scope. It excludes objects from
before the call from later module-level `run`, `collect`, `store`, and `restore`
operations; it does not remove objects from an explicit `Network` and does not
restore state.

## In-memory snapshots

Use named snapshots for trial boundaries:

```python
net.store("initialized")
for trial in range(3):
    net.restore("initialized")
    run_training_phase(net)
    net.store("after_learning")
    for test_input in test_inputs:
        net.restore("after_learning")
        apply_test_input(test_input)
        net.run(test_duration)
```

`store` captures internal state of all objects in the network, all their clocks,
network time, and the active device's random-generator state. Names are
independent slots; storing another snapshot with the same name replaces it.
Monitors already in the network are part of the snapshot state, so repeated
runs can restore monitor internals as well as model state. A monitor created
*after* a snapshot is not part of that stored state and is not a safe way to
change snapshot membership; construct it before the snapshot and toggle
`active`, or use a deliberately explicit network with a stable object set.
Brian's built-in monitors are non-invalidating for magic-network continuation,
so a late monitor alone does not cause the mixed old/new `MagicError`; it can
still be absent from an earlier snapshot or make trial membership ambiguous.

Restoration does not reconstruct Python objects, equations, thresholds, or
names. Recreate the same object graph with identical object names before
loading a disk snapshot. It restores dynamic state such as membrane values,
synaptic weights/connections/delays, clocks, pending delayed spikes, and
network time. It is not a cross-version or cross-platform serialization format;
use state export APIs for portable analysis/documentation data.

## Randomness and reproducibility

Call `from brian2 import seed` and then `seed(integer)` before stochastic
initialization or the trial block when a repeatable runtime random stream is
required. `seed(None)` requests a fresh seed. `restore()` defaults to
`restore_random_state=False`: it restores model state but intentionally allows
new random draws, so stochastic repeated trials need not match. Use
`restore(restore_random_state=True)` when the trial must replay the exact
runtime random stream from the snapshot. Brian restores its runtime/NumPy
random state, not Python's `random` module state; seed or snapshot that module
separately if it is used.

For comparisons, distinguish these goals:

- **Independent trials:** restore model state without random state, then let the
  runtime draw a fresh stream.
- **Exact replay:** restore with `restore_random_state=True` and keep the same
  object graph and code path.
- **Same initialization, parameter sweep:** seed once before initialization,
  snapshot the initialized network, restore the snapshot for each parameter
  value, and change only the intended state/parameter.

## Late monitors and train/test loops

A built-in monitor added after training is non-invalidating, so it does not by
itself trigger a mixed-old/new `MagicError`; it still cannot appear in an
earlier snapshot and may make trial membership or result ownership unclear.
Prefer constructing all monitors before the first run, setting
`monitor.active = False` during training, then enabling it for test. If a late
object is actually a new invalidating input, synapse, or group, mixed magic
membership can raise `MagicError`; construct the complete explicit network
before its first run. If objects have already run in magic, do not try to move
them into a new network—recreate the model or continue with the existing magic
membership.

A robust train/test pattern is:

1. Create model, synapses, all monitors, and any control operations.
2. Build one explicit `Network` and store `"initialized"`.
3. For each train trial, restore `"initialized"`, enable plasticity, run
   training, store `"after_learning"`, and disable plasticity.
4. For each test, restore `"after_learning"`, set the test input, activate the
   test monitor, run the test duration, copy results out, then deactivate it.
5. Use distinct result arrays/copies outside the network; do not assume a
   monitor's mutable buffers are a trial archive.

If the test monitor must preserve every trial, allocate a result structure in
Python and copy monitor values before the next restore. If a monitor should
record only a phase, `active` controls updates but snapshot semantics still
require that its object exists in the network when the snapshot is taken.

## Disk snapshots

`net.store("name", filename="state.pkl")` can hold several named states in one
file. Later, construct an object graph with the same names and call
`net.restore("name", filename="state.pkl")`. Treat the file as a local,
version-sensitive artifact. Avoid untrusted pickle files; never load one from
an untrusted source.
