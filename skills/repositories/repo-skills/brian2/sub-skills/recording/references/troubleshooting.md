# Recording troubleshooting

Start by reducing the experiment to one source, one monitor, a short duration,
and the NumPy code-generation target. Check the monitor's `t`, shape, units,
and counts before adding analysis or plotting.

## Install and import

**Symptoms:** `import brian2` fails, an extension such as a dynamic-array or
spike-queue module is missing, or monitor construction fails during import.

- Verify the interpreter and package together: `python -c "import sys, brian2;
  print(sys.executable, brian2.__version__)"`.
- Brian2 2.9.0 requires Python >=3.12 and builds Cython extensions. A partial
  source/development installation can fail before any monitor code runs;
  reinstall Brian2 into the active environment rather than debugging monitor
  arrays first.
- The core dependency set includes NumPy, Cython, SymPy, pyparsing, Jinja2,
  setuptools, and packaging. Repair a broken environment with the package
  manager used to create that environment, then rerun the import probe.
- An already-installed wheel can run a NumPy recording check without a
  compiler; a compiler is needed when Brian must build Cython/runtime
  extensions or when using C++ standalone. It is not a plotting dependency.
  Start with the NumPy target when native compilation is not available.
- Do not run a script from an unrelated directory containing a shadowing file
  named `brian2.py` or `numpy.py`; inspect `brian2.__file__` if import identity
  is uncertain.

This route can identify import failures, but environment creation belongs to
the repository environment workflow and device selection belongs to the
code-generation route.

## Optional dependencies

**Symptoms:** a monitor smoke script fails because plotting or a scientific
optional package is absent.

- Spike/state/rate/event monitor construction and `binned_rate`/
  `smooth_rate` use core Brian2 and NumPy. Matplotlib is not required to inspect
  arrays; the bundled smoke script deliberately does not import it.
- `matplotlib`, `ipython`, Jupyter, and `brian2tools` are optional visualization
  or interactive tools. Install them only for a plotting task routed outside
  this skill.
- GSL support is an optional numerical state-updater/system dependency. Its
  absence does not prevent core monitors. Switch to a supported built-in
  updater for the recording smoke, or route the GSL problem to code generation.
- Pytest is a test extra, not a runtime monitor dependency. Do not turn a
  missing test tool into a monitor-install diagnosis.

## Data and configuration errors

**Symptoms:** unit errors, unexpected empty arrays, a binning exception, or an
export that cannot be interpreted later.

- `StateMonitor` variable names must exist on the source. `EventMonitor` event
  names must exist in `source.events`. A spike monitor needs a spike-producing
  source. Inspect the model/event declaration before changing the monitor.
- `dt`/`clock` and `bin_size` are physical times. `binned_rate(bin_size)`
  requires `bin_size` to be a multiple of the monitor clock `dt`; use a
  compatible integer multiple rather than a nearly equal floating value.
- Record selection can be empty (`record=False` or `record=[]`). An empty state
  trace is not evidence that the source did not evolve. Assert `len(monitor.t)`
  and the selected row count separately.
- `get_states` returns copies. A mutation of an exported dictionary does not
  update a live monitor. For a `StateMonitor`, verify whether downstream code
  expects public `(recorded_index, time)` arrays or exported time-first
  storage. Save `record`, source/subgroup bounds, `dt`, `when`, and units policy
  with the data.
- `units=False`, `.t_`, and variable underscore attributes are raw SI-scaled
  values. Do not relabel a unitless array as milliseconds, volts, or hertz
  merely for display.
- `smooth_rate` predefined windows require a Brian time `width`; custom windows
  must be one-dimensional with odd length and must not receive `width`. A
  smoothing result has the original `dt`, not the bin width of a separate
  analysis convention.
- Trailing incomplete bins are intentionally excluded. Bins are starts, not
  centers. A late `PopulationRateMonitor` starts its binned grid at its first
  recorded time, but late `SpikeMonitor`/`EventMonitor` binning can retain
  leading zero bins from time zero. If a display needs centers, add half the
  bin width only to the display coordinate.

## API misuse

**Symptoms:** missing `i`/`t`, `KeyError` from a spike train dictionary,
`IndexError` from a state monitor, or a monitor with no events.

- `record=False` suppresses individual event indices/times by design. Use
  `count`, `num_spikes`, or `num_events`; do not call `spike_trains`,
  `event_trains`, `values`, or `all_values` unless event storage was enabled.
- A monitor attached after an earlier `run` cannot observe past spikes or
  states. Its first times begin at attachment. Create it before the run or
  intentionally treat it as a segment.
- `SpikeMonitor` and `EventMonitor` indices are local to their source. A
  subgroup monitor's `i=0` is the first neuron in the subgroup, not necessarily
  parent index zero. Save the subgroup bounds. For a non-contiguous event
  subset, use a masked custom event and save its mask; these monitors do not
  accept an arbitrary parent-index list.
- For a sparse `StateMonitor`, `monitor.v[row]` is a relative recorded row,
  whereas `monitor[parent_index].v` is absolute source indexing. A parent
  index that was not selected raises `IndexError`; do not substitute a relative
  row by guesswork.
- `StateMonitor(record=True)` may fail for a synaptic variable in standalone
  when the number of synapses is unknown before generated code executes. Use
  explicit synaptic indices in that workflow.
- An undeclared event, a source with no threshold/spike event, or a variable
  absent from the source is a model/API error. Route model-side fixes to
  modeling/synapses-and-inputs rather than hiding the error with a different
  monitor.

## Timing and shifted traces

**Symptoms:** a membrane trace appears one `dt` early/late, never reaches its
threshold, or an event-captured variable has the wrong pre/post-reset value.

1. Print or inspect `monitor.clock.dt`, `monitor.when`, and `monitor.order`.
2. Inspect the network schedule and the source's integration, threshold, reset,
   and event-handler slots.
3. Run for two or three steps with a hand-checkable state and compare the
   monitor's first/last time with the intended sample point.
4. Make `when` explicit. `StateMonitor` defaults to `start`, before the current
   step's update/threshold/reset; a later slot such as `before_resets` can
   observe the thresholded value before reset. Event monitors default to the
   event emission timing and then record directly afterward.
5. Use `order` only to disambiguate objects in the same slot. If the source or
   event handler has changed its slot, changing monitor order alone cannot fix
   the schedule.

The usual cause is schedule semantics or monitor attachment time, not a bad
plot. Do not shift `t` or the data array after the fact without documenting the
changed sampling definition.

## Workflow and standalone failures

**Symptoms:** the monitor is not in the run, arrays are unavailable during a
compiled run, snapshots fail, or result access fails after cleanup.

- In an explicit `Network`, include every monitor (`Network(source, monitor)`)
  or add it explicitly. A strong Python reference alone does not guarantee that
  a monitor in an arbitrary container is executed by a network.
- For staged recording, use `network.add/remove` or `monitor.active`; do not
  create/delete objects while relying on an implicit magic network whose
  collected object set is unclear. The run lifecycle route owns magic-network
  collection and schedule diagnostics.
- Runtime monitor removal/recreation is not a C++ standalone memory-management
  strategy. Plan bounded/generated output in the standalone program and access
  it only after the compiled run.
- In C++ standalone, Python cannot generally inspect generated dynamic results
  before the compiled executable has run. Access monitor/state values after the
  run, export them, and do not delete generated data until analysis is done.
  The standalone device does not support `Network.store`/`restore`; use an
  explicit data artifact instead.
- Standalone monitor/state output is backed by generated result files. Cleanup
  of the device data invalidates subsequent monitor access. Disk usage can be
  large even if the Python process appears small. Export or analyze before
  cleanup.
- `Network.store`/`restore` is a continuation checkpoint, not a portable data
  export. Objects and names must match, and equations are not serialized. Use
  `get_states` for analysis artifacts.
- If rate or state arrays are unexpectedly empty, first confirm that the
  monitor was active for a positive interval and that the source clock advanced.
  Then check `len(monitor.t)`, not only a plotting or aggregation result.
