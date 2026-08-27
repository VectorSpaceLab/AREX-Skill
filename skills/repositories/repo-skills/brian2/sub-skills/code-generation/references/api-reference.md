# Code-generation API reference

This reference records the public Brian2 2.9.0 interfaces used by this route.
It is intentionally about operating contracts rather than ordinary model
construction.

## Preferences and devices

```python
from brian2 import get_device, prefs, set_device

prefs.codegen.target = "auto"       # auto, cython, or numpy
prefs.codegen.target = "numpy"       # explicit Python/NumPy fallback
set_device("runtime")                 # normal in-process execution
set_device("cpp_standalone")          # generated C++ project
active = get_device()
```

`prefs.codegen.target` controls runtime code objects. `"auto"` checks whether
Cython can compile and prefers it; when unavailable it selects NumPy. `"numpy"`
works without a C/C++ compiler but is normally slower. `"cython"` requires the
Cython package and a working C++ compiler. `codegen.string_expression_target`
is a separate preference for short string-expression evaluations and defaults
to NumPy; do not change it just to select the main simulation target.

Compiler selection is separate from the target choice. On Unix-like systems,
`CC`/`CXX` can select compiler executables; `prefs.codegen.cpp.compiler` is
normally left as `""` (automatic) and accepts the platform compiler family such
as `"unix"` or `"msvc"`. `prefs.codegen.cpp.include_dirs`, `library_dirs`,
`extra_compile_args`, and `extra_link_args` affect generated C++ for both
Cython and standalone. For standalone's make step, use the
`prefs.devices.cpp_standalone.make_cmd_unix` or platform-specific extra make
arguments rather than changing the generated project by hand.

`set_device(device, build_on_run=True, **kwargs)` accepts a registered device
name or a device object. `build_on_run` matters to standalone: with `True`, a
`run` triggers build/compile/run; with `False`, `run` only queues the generated
network and an explicit `device.build(...)` is required. Additional keyword
arguments supplied to `set_device` are stored as build options. `get_device()`
returns the active device. `device` imported from Brian2 is a proxy, so
`device.build()` and `device.run()` operate on that active device.

## Standalone build and run

The important `CPPStandaloneDevice` calls are:

```python
set_device("cpp_standalone", build_on_run=False, directory="project")
# construct the model and call run(...) one or more times

device.build(
    directory="project",       # None asks Brian2 for a temporary directory
    results_directory="results",
    compile=True,
    run=False,
    debug=False,
    clean=False,
    with_output=False,
)
device.run(
    results_directory="results_0",
    run_args={group.v: initial_values},
    with_output=False,
)
```

`device.build` generates the project whether or not `compile` is true. With
`compile=True`, it invokes the platform build tool; with `run=True` it then
executes the binary. Both default to `True`; `compile=False` therefore writes
only the generated project and cannot execute it. `run_args` supplied to
`build` is passed to that first execution. `device.build(run=False)` is the
usual first step before reusable runs. Do not call `device.build` manually
after selecting the default `build_on_run=True` and then allowing an automatic
build; Brian2 rejects that ambiguous sequence. If a build already ran, start a
separate standalone project and reinitialize/activate the device rather than
rebuilding the same network in place.

`directory` is the project tree. `results_directory` is relative to that tree;
an absolute result path is rejected. A build creates code-object, result, and
static-array areas. `device.run` accepts the same project and can write a
unique relative result directory for each run. Its `run_args` accepts a mapping
keyed by a `VariableView` (for example `group.v`) or a `TimedArray`, or a
lower-level list of `name=value` command-line assignments. Scalar values
broadcast where allowed; non-scalar arrays must match the variable/
`TimedArray` shape. The mapping is validated for dimensions and shape before
the native process runs. `with_output=False` captures standalone stdout in the
result area and keeps normal output quiet. Keep a reference to `get_device()`
if code crosses process or object boundaries, but multiprocessing is not an
ordinary route here.

## `run_args` contract

For repeated standalone executions, `run_args` may be a mapping whose keys are
Group `VariableView` attributes (for example `group.tau` or `group.v`) or a
`TimedArray`; values must have compatible units and shapes. A scalar broadcasts
where the variable permits it, and an array must have the expected shape. Brian
also accepts a lower-level list of command-line assignments such as
`["neurons.v=5"]`, but use the mapping form for normal code.

Only values represented in the generated model can be changed without a new
build. Put a parameter that should vary between runs in the equations, often
with `(shared, constant)` when it is one value for the whole group, then pass
it in `run_args`. An external Python constant captured by an equation is not a
reusable runtime parameter. `TimedArray` values can also be replaced with an
array of the same shape.

If one initialization depends on another value that is overridden by
`run_args`, call `device.apply_run_args()` once before the dependent
initialization is generated. It inserts the command-line application at the
appropriate point; calling it twice raises `RuntimeError`.

## Results and cleanup

Standalone monitors and final state are loaded from disk after a successful
run. Analyze them before deleting data. `device.delete()` removes generated
data and code by default; use `device.delete(code=False, directory=False)` to
keep generated code in place, or the narrower `data`, `code`, and `run_args`
switches with `directory=False` to prune parts. A directory containing
user-created files is not removed unless `force=True`. Prefer a temporary
directory in tests so cleanup is automatic.

## Inspection boundaries

`device.build`/`device.run` are native operations, not import checks. A package
import can succeed while the Cython extension or standalone compiler is broken.
Validate the target and compiler independently, then run a tiny project. The
bundled `scripts/standalone_smoke.py` is the minimal project check.
