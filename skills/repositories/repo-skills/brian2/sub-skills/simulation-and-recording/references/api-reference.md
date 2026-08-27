# Simulation control API

This route targets Brian2 2.9.0 and the public import root `brian2`. The API
and behavior notes were checked against Brian's public running, computation,
and scheduling topics and the installed 2.9.0 runtime; those topics are
provenance only, not runtime dependencies.

Quantities passed to time APIs should carry
Brian units such as `ms`, `second`, or `us`; do not silently pass bare numbers
where a time quantity is required.

## Choosing the controller

### `Network`

`Network(*objs, name='network*')` owns a set of Brian objects and advances all
contained objects. It recursively accepts Brian objects and containers; mapping
keys are ignored and mapping values are added. `Network.add(...)` and
`Network.remove(...)` accept the same recursive object/container style.

Useful members:

- `net.run(duration, report=None, report_period=10*second, namespace=None,
  profile=None)` advances from `net.t` by `duration`.
- `net.t` is the current time quantity and is read-only. A newly constructed
  network starts at zero.
- `net.schedule` gets/sets the ordered schedule slots. Assign `None` to reset
  to the default preference. The default is `['start', 'groups',
  'thresholds', 'synapses', 'resets', 'end']`.
- `net.sorted_objects` exposes deterministic execution order; use
  `net.scheduling_summary()` for a printable diagnostic.
- `net.stop()` stops the active network at the current clock time. A later
  `net.run` resets the network stop flag.
- `net.store(name='default', filename=None)` and
  `net.restore(name='default', filename=None, restore_random_state=False)`
  snapshot and restore internal state.
- `net.profiling_info` is a descending list of `(code-object-name,
  time-quantity)` after a run with `profile=True`.

Objects may only be run in one network identity. Do not remove an object after
it has been simulated and then add it to a different network; toggle
`obj.active` when temporary exclusion is needed.

### Magic controller

The module-level `run`, `store`, and `restore` operate on one implicit
`MagicNetwork`; their time and snapshot membership are inferred from the
current call scope. `collect()` returns the visible, current-scope
`BrianObject` instances that magic `run` would include. It inspects direct
values in the calling namespace, not Brian objects hidden inside an arbitrary
Python list, dict, or other container. `Network(collect())` is useful **before
the first run**, followed by `net.add(hidden_objects)` for container-held
objects; it is not a way to move already-simulated objects out of a magic
network.

`start_scope()` increments the magic scope key. Objects created before it are
then excluded from later magic collection; it does not delete, reset, or rewind
those objects, and it does not change an explicit `Network` that already owns
them. `stop()` requests a stop for the currently running network through the
global stop flag.

Magic `run` has two supported patterns: all collected invalidating objects are
new (start a new simulation at zero), or all such objects belong to the
previous magic run (continue time). Non-invalidating objects such as monitors
do not determine this choice. A mix of previously run and new invalidating
objects raises `MagicError`; choose complete explicit membership before the
first run, or rebuild the model in a fresh explicit network rather than trying
to transfer objects that have already run.

### Clocks and timing

- `defaultclock` is a proxy for the active device's default `Clock`.
  `defaultclock.dt = 0.1*ms` changes the clock used by objects that did not
  receive an explicit `clock` or `dt` at construction. Set it before creating
  objects when a common step is intended.
- `Clock(dt, name='clock*')` advances on a regular integer timestep. Pass the
  same `Clock` to multiple objects to change their `dt` together later.
- `EventClock(times, name='eventclock*')` sorts a unique sequence of time
  quantities and advances only at those event times. It can be passed via an
  object's `clock=` argument; unlike a regular `Clock`, it has no regular
  `dt`. Duplicate times or dimensionless times are invalid.
- An object can receive `dt=...` or `clock=...`, but not both. Its `clock`
  cannot be replaced after construction. Its `when` is a schedule slot and
  its integer `order` breaks ties within that slot.

A clock stores time internally as integer timesteps. When changing a regular
clock's `dt` after time has advanced, Brian checks that the current time is
representable under the new step. A change such as 100.1 ms to 0.3 ms is
incompatible and raises `ValueError`; choose a compatible step, change at a
representable boundary, or use a separate clock.

### Activity and schedule

`obj.active = False` prevents its update during `run`; setting activity on a
container object propagates to contained objects. Restore it before the phase
that should run. `when` selects a slot; `order` is ascending within the same
slot, with object name as the deterministic final tie-breaker. In addition to
schedule names, `before_<slot>` and `after_<slot>` are implicit positions. A
custom schedule must be a sequence of strings, must retain every slot needed by
contained objects (normally the default `start`, `groups`, `thresholds`,
`synapses`, `resets`, `end` slots), and must not itself contain `before_` or
`after_` names.

### Callbacks and diagnostics

`NetworkOperation(function, dt=None, clock=None, when='start', order=0)` calls a
zero-argument function each update, or a one-argument function with the current
clock time. The `@network_operation` decorator creates this object. Add the
returned object to an explicit network; magic collection includes it when it is
directly visible. `dt` and `clock` are mutually exclusive. The callback must
accept no arguments or exactly one time argument; keep it lightweight and do
not rely on magic to discover Brian objects captured only by a closure.

For reproducible runtime randomness, `from brian2 import seed` followed by
`seed(integer)` resets Brian's active-device random stream (the runtime device
uses NumPy internally). `seed(None)` requests a fresh random seed. This is
separate from Python's `random` module; seed that module independently if a
callback uses it.

`report` on `run` accepts `None`, `'text'`/`'stdout'`, `'stderr'`, or a callable
`(elapsed, completed, start, duration)`. The callback is invoked at 0 and 1
completion regardless of `report_period`; periodic callbacks use wall-clock
report periods, not simulation timesteps. A report period is a time quantity,
and the callable's `start` and `duration` describe biological simulation time.

`profiling_summary(net=None, show=None)` formats results collected by
`profile=True`; without `net`, it addresses the magic network. Calling it
without a prior profile run raises `ValueError`. `scheduling_summary(net=None)`
returns a printable/HTML summary with object, owning part, clock `dt`, `when`,
`order`, and `active` values; without `net`, it first refreshes magic objects.
For an explicit network, pass `net` to both diagnostics rather than relying on
the module-level magic default.
