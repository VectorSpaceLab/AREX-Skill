# Brian2 Cross-Cutting Troubleshooting

Read this for failures that are not owned by one modeling, input, monitor, or
device workflow. Keep the original exception, package version, Python version,
code-generation target, and the smallest reproducing model before changing
multiple variables.

## Installation and import

- **`ModuleNotFoundError: brian2`**: verify the interpreter and distribution
  together with `python -m pip show Brian2`; install into the same isolated
  environment with `python -m pip install brian2`. Run the bundled environment
  checker from a neutral directory. Do not add the source checkout to
  `PYTHONPATH` as a substitute for installation.
- **Required dependency import failure**: Brian2 checks NumPy, SymPy, pyparsing,
  and Jinja2 during import. Repair the environment rather than masking the
  error with partial imports. Use a Python >=3.12 environment for this graph.
- **Editable/source install reports an invalid `unknown` version**: shallow
  source checkouts without tags can prevent `setuptools-scm` from resolving a
  version. Prefer a released PyPI/Conda package. For a deliberate development
  install, use a valid project version override only in the private build
  environment and do not publish that workaround as a runtime requirement.
- **A different Brian2 is imported than expected**: compare
  `importlib.metadata.version("Brian2")` with `brian2.__version__`, then inspect
  the current working directory for a shadowing `brian2.py` or `brian2/`.

## Optional packages and compiler

- **Cython target falls back to NumPy**: confirm Cython and a working C++
  compiler. Set `prefs.codegen.target = "numpy"` explicitly when a compiler is
  unavailable; this validates core runtime behavior but does not prove Cython
  performance or C++ standalone support.
- **Standalone build cannot compile**: check `g++ --version` (or the platform
  compiler), write to a fresh temporary output directory, and inspect the
  generated compiler command. Do not repeatedly reuse a partially generated
  directory. Follow the `code-generation` route for `build_on_run`, cleanup,
  `run_args`, and standalone limitations.
- **GSL method import/build fails**: GSL is optional. Install the system GSL
  runtime and development headers only if the task explicitly needs `method="gsl"`;
  otherwise select a supported non-GSL updater and state the numerical-method
  limitation.
- **Plotting/SciPy/Pandas/Jupyter errors**: these are optional integrations,
  not core Brian2 import requirements. Install only the package needed for the
  requested output and keep the simulation smoke independent of plotting.

## Preferences, cache, and logs

- **Unexpected target/compiler behavior**: inspect effective `prefs` values and
  the preference-file precedence before changing code. The user preference
  file and current-directory `brian_preferences` can override defaults; keep
  project-specific settings explicit in the script when reproducibility
  matters.
- **Cython cache is stale, too large, or not writable**: use the documented
  cache preferences and `clear_cache("cython")` only when the cache is owned by
  Brian2 and deletion is safe. Move to a writable project cache rather than
  deleting an arbitrary directory. Do not clear a cache while another process
  is compiling.
- **Need more diagnostic detail**: configure Brian's logger at the application
  boundary and retain the first traceback, target, and compiler output. Logging
  cannot repair a malformed equation or an invalid device transition.

## Cross-workflow API failures

- **`DimensionMismatchError`**: route to `units-and-equations`; annotate each
  state variable, derivative, external parameter, and assigned value. In
  equation declarations use base dimensions (`volt`, `second`, `amp`, or
  compound base units), while assignments can use scaled values such as `mV`.
- **A network does not run an object**: magic `run` only collects visible
  objects. Use an explicit `Network` and add objects held in lists/dicts or
  created across stages. If old and new objects are mixed, fix lifecycle
  ownership rather than adding another magic `run`.
- **Synaptic state or monitor data is empty**: confirm `Synapses.connect(...)`
  happened before assignment and that monitors were created before the relevant
  run. Check `when`, `dt`, selected indices, and the monitor's relative-index
  semantics.
- **Standalone script accesses state too early**: standalone executes generated
  code later, so Python-side reads of state or synaptic indices after setup may
  be invalid. Use string-based initialization, generated output, or runtime
  mode when immediate Python access is required.

## Escalation

Reduce the case to one group, one equation, one short run, and NumPy target. If
that passes, add the input, synapse, monitor, and target one at a time. Preserve
optional-backend failures as explicit limitations; never call a CPU import a
pass for a required standalone/compiler capability.
