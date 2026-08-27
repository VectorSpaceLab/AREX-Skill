# C++ standalone workflows

C++ standalone turns the Brian2 setup into a generated project, compiles it,
and runs a native executable. It is useful when Python-loop overhead dominates
or a fixed network should be run repeatedly. It is not a drop-in replacement
for arbitrary Python control flow.

## One final run

Select the device before constructing the model:

```python
from brian2 import *
set_device("cpp_standalone", directory="standalone_project")
# construct model, monitors, and one final run(10*ms)
run(10 * ms)  # automatic build and native execution
```

For one run, the default `build_on_run=True` is convenient. Pass build options
such as `directory=None`, `debug=True`, or `with_output=False` through
`set_device` when appropriate. `directory=None` asks Brian2 to create a
temporary project, which is useful for disposable checks. The automatic path
is equivalent to generating, compiling, and running once; do not call
`device.build` manually in this mode. If build options or first-run arguments
need explicit control, use `build_on_run=False` and call
`device.build(..., run_args=...)` yourself.

## Multiple `run` statements

A Python script with several `run` statements must disable automatic building:

```python
set_device("cpp_standalone", build_on_run=False, directory="project")
# construct a model
run(2 * ms)
# make other model setup that is representable in generated code
run(3 * ms)
device.build(run=True, with_output=False)
```

This emits a fixed sequence of network runs and compiles once. Do not call
`device.build()` after an automatic build or after the project has already run.
If a model truly needs a new generated network, create a fresh device/project
and reinitialize it rather than trying to rebuild an executed project.

## Build once, reuse the binary

For independent full simulations with the same generated model:

```python
set_device("cpp_standalone", build_on_run=False, directory="project")
G = NeuronGroup(4, "dv/dt = -v/tau : 1\n tau : second (shared, constant)")
G.tau = 10 * ms
mon = StateMonitor(G, "v", record=True)
run(1 * ms)                    # queue the model; no build yet
device.build(run=False)        # generate and compile once
for tau_value in (5 * ms, 10 * ms):
    device.run(
        run_args={G.tau: tau_value},
        results_directory=f"results_{tau_value/ms:g}",
        with_output=False,
    )
```

`device.run` reuses the compiled executable. It reruns the full simulation,
including generated initialization and random state handling, but does not
accept arbitrary model edits. Use `run_args` for equation variables or a
`TimedArray` with matching shape/units. For a random trial sweep with no
parameter change, call `device.run()` repeatedly and still use distinct result
locations when retaining each output.

A dependent initialization needs care. In the generated code, a normal
assignment such as `G.tau = 5*ms; G.other = "tau*2"` is emitted in order. If
`run_args` should override `tau` before `other` is computed, call
`device.apply_run_args()` once before defining the dependent assignment. The
method inserts the command-line application and cannot be called twice.

## Results directories and collisions

`device.build(..., results_directory="results")` and
`device.run(results_directory="results_i")` require a relative path. Brian2
places it below the project directory. Never use the same results directory
for concurrent processes or for runs whose outputs must be preserved: monitor
and final-state files will collide. Multiprocessing also has global active-device
and pickling concerns; use it only as an explicitly designed, separately
validated workflow. For ordinary sequential sweeps, unique directories are
sufficient.

Read monitor/state values after a successful native run. Delete data only after
analysis:

```python
device.delete(data=True, code=False, directory=False)
```

That narrowed call deletes data in the device's current `results_dir`; if
several result directories were retained, remove the older directories
separately or discard the whole disposable project. `device.delete()` without
narrowed options removes generated data and code for the active project, while
a project directory containing unrelated files is protected unless
`force=True`. Use a temporary directory for tests and let its owner clean up.

## Standalone limitations

Plan around these boundaries before selecting the device:

- Python-based `NetworkOperation` work and arbitrary Python callbacks do not
  become native C++ operations.
- The generated code supports a fixed number of `Network.run` statements. A
  Python loop that repeatedly sets up a network and calls `run()` is not a
  general standalone parameter sweep. Generate one fixed sequence or use the
  build-once/`device.run` pattern.
- Some array-based syntax, including examples such as `S.w[0, :] = ...`, is
  not supported. Prefer Brian string-based expressions when they can be
  evaluated in generated code.
- During setup, values that depend on generated execution are not available:
  state arrays initialized with random/string expressions, and indices after a
  probabilistic/conditional synapse connection, may raise `NotImplementedError`
  when accessed. Use string initializations, concrete known values, or inspect
  after `run`.
- Standalone does not support the runtime `Network.store`/`restore` mechanism.
- Standalone object names need to be globally unique in the generated project.
- Compiler and native-library support are required even if the same model runs
  with NumPy at runtime.

A successful NumPy run demonstrates the model path only. A successful package
import demonstrates neither Cython compilation nor standalone build/run.

## Recovery pattern

When a runtime script fails to compile under Cython or standalone, first run its
smallest equivalent with `prefs.codegen.target = "numpy"` and the runtime device.
If that works, retain the result as a functional fallback while checking the
native failure separately. State clearly that NumPy does not validate generated
C++ syntax, standalone restrictions, compiler availability, or GSL linkage.
