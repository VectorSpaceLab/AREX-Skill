# Code-generation troubleshooting

Diagnose the active environment and the selected target separately. Capture the
first complete error and the target/device settings before changing them. A
NumPy recovery is useful, but it does not prove Cython or standalone support.

## Install/import failures

- **Brian2 import fails with a missing compiled support extension:** use a
  properly installed Brian2 package (or rebuild the package's own extensions)
  in the active Python >=3.12 environment. Do not infer that a source checkout
  import failure is a model or standalone failure.
- **Cython or NumPy cannot be imported:** verify the package environment's
  dependencies and interpreter selection. Do not install into a different
  interpreter than the one executing the script.
- **The package imports but `auto` chooses NumPy:** this is a native-toolchain
  signal, not an error in the model. Inspect the availability warning, then
  either prepare Cython/compiler support or set `prefs.codegen.target =
  "numpy"` explicitly to make the fallback intentional.
- **Standalone cannot start:** import/package readiness is only a preflight.
  Check the compiler and make tool in the same environment, then run the
  bundled tiny standalone smoke after the environment is prepared.

## Compiler and Cython failures

- **Compiler missing/not found:** install or expose a supported C/C++ compiler
  and build tools; on Unix, inspect `CC` and `CXX`, and on Windows prepare the
  supported Visual Studio toolchain. Re-run the Cython availability probe and
  then a tiny model. Do not claim standalone from `g++ --version` alone.
- **Cython test compile fails:** read the first compiler diagnostic, check
  Python/NumPy/Cython ABI compatibility, include/library directories, and
  compiler flags. A known-good alternative compiler can be selected through
  `CC`/`CXX` on Unix. Compare the exact model under NumPy to isolate generated
  C++/compiler failures from model errors.
- **Generated code fails after the probe succeeds:** the probe only compiles a
  trivial extension. Reduce the model, remove unsupported expressions or
  custom code, and test the same model under NumPy. Keep a native failure
  explicit if only the fallback succeeds.
- **Standalone `make` fails:** retain the compiler output, try `clean=True`
  for a stale partial project, and verify C++17/compiler support and library
  paths. Use a fresh project directory when a previous generated tree may have
  incompatible code.

## Cache and permissions

- **Cache directory cannot be created or written:** set
  `prefs.codegen.runtime.cython.cache_dir` to a writable local directory in
  the active environment. Check ownership, free space, and quota without
  deleting unrelated files. Keep `multiprocess_safe=True` for concurrent
  compilation.
- **Cache warning or unexpected disk growth:** the default warning threshold is
  `prefs.codegen.max_cache_dir_size` (1000 MB in this release). Remove stale
  generated extensions with `clear_cache("cython")` when safe, or set a
  deliberate threshold; do not confuse this cache with standalone results.
  Keep source files only while diagnosing (`delete_source_files=False`), then
  restore the space-saving default.
- **Stale or incompatible extension:** use a clean cache or change to a fresh
  writable cache after recording the compiler, Python, Cython, and NumPy
  versions. Do not run two cleaners or compilers against the same cache.

## Optional dependency failures

- **GSL headers/libraries missing:** GSL is optional. Check `prefs.GSL.directory`
  only if a GSL method is requested; it must point to a prefix containing the
  required `gsl/` headers. For standalone, also check `gsl`/`gslcblas` linking
  and shared-library discovery. Otherwise use a documented non-GSL updater and
  record that GSL was not verified.
- **GSL with NumPy target:** runtime GSL is not implemented for NumPy. Select
  Cython with a working GSL installation, use standalone with its native GSL
  libraries, or choose a non-GSL updater.
- **GSL stochastic model:** the GSL state updater rejects stochastic equations.
  Use a suitable non-GSL state updater; this is a feature boundary, not a
  missing-header problem.

## Data/configuration and API misuse

- **State/indices unavailable during standalone setup:** values that depend on
  generated execution are intentionally not readable before `run` (for
  example random/string-initialized state or indices after probabilistic
  synapses). Use string expressions for dependent initialization, concrete
  known values, or inspect after a successful run.
- **`run_args` rejects a key:** use a Group `VariableView` such as `group.v` or
  a `TimedArray`, not a plain string or arbitrary Python object. Check units,
  dtype, and exact array shape. For a scalar parameter that changes per run,
  declare it in the equations (often `(shared, constant)`) rather than closing
  over an external Python constant.
- **Dependent `run_args` value is stale:** call `device.apply_run_args()` once
  before the dependent generated assignment. A second call is invalid.
- **Build called at the wrong time:** with `build_on_run=True`, let the first
  `run` build automatically; do not call `device.build` manually in that path.
  For multiple runs, select `build_on_run=False`, queue all run statements,
  then build explicitly.
- **Absolute result directory rejected:** `results_directory` must be a
  relative path below the standalone project. Use a unique name such as
  `results_trial_03` rather than an absolute path.
- **Results collide or are overwritten:** assign distinct result directories
  for retained or concurrent runs. A shared project does not make concurrent
  writes safe; multiprocessing also requires explicit device/process handling.
- **Standalone store/restore or Python network operation fails:** these are
  unsupported or inappropriate standalone features. Use runtime mode for
  Python-controlled scheduling/snapshots, or redesign the operation as
  supported generated code.
- **Repeated looped runs do not behave as expected:** standalone generation
  represents a fixed number of `run` statements. For independent repetitions,
  build once and call `device.run` with `run_args`; for arbitrary Python loops,
  stay in runtime mode.

## Recovery checklist

1. Record device, `prefs.codegen.target`, Python/package versions, compiler,
   Cython, and optional-library choices.
2. Run a tiny runtime NumPy case. If it fails, repair model/API/units first.
3. Test Cython availability and a tiny Cython runtime case independently.
4. Prepare a fresh standalone project and run the tiny native smoke.
5. Only then retry the user's model, preserving the first native diagnostic.
6. Report functional fallback versus native/optional capability separately.
