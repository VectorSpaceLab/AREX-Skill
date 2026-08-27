# Troubleshooting and failure triage

Diagnose the first failing layer, preserve its evidence, and change one thing at
a time. A successful import does not prove that a selected code-generation or
standalone workflow is usable.

## Triage order

1. From the directory containing the bundled `scripts/` directory (or by
   passing that script's relative path), run `python scripts/check_brian2_env.py
   --json`. Record only the version, import status, required/optional module
   states, compiler **names**, target, and capability statuses; redact paths.
2. Confirm the active Python with `python -c "import sys; print(sys.version)"`
   and package consistency with `python -m pip check`.
3. Preserve the first exception and its complete traceback before clearing a
   cache or retrying. Classify it as identity/import, Python dependency,
   compiler/build, optional capability, preference/configuration, API/model, or
   workflow/device.
4. Inspect targeted preferences and unvalidated names. Do not change a target
   or cache merely to hide the symptom.
5. Retry the smallest supported path, normally a fresh interpreter with
   `prefs.codegen.target = "numpy"` and a tiny deterministic model. Native
   compilation and standalone output are separate, approved checks.

## Installation, version, and import failures

### “Cannot determine Brian version” or version is `unknown`

Brian first imports generated version metadata and can fall back to build-time
version discovery. An unknown value indicates an incomplete source-like import,
missing build metadata, or an import that is not the intended release. It does
not prove Brian2 2.9.0.

- Compare `importlib.metadata.version("Brian2")` or `python -m pip show Brian2`
  with `brian2.__version__`.
- Run from a neutral working directory to rule out package shadowing by a
  checkout or a local `brian2` directory.
- Reinstall the intended release in the active interpreter and retest in a
  fresh process. Do not add checkout directories to `PYTHONPATH` or mix an
  editable source import with a wheel.

### A required dependency cannot be imported

Brian's import-time dependency check probes NumPy, SymPy, PyParsing, and
Jinja2. Cython, setuptools, and packaging are declared runtime/build baseline
packages; Cython is exercised by the compiled Cython target and source-built
extensions rather than by that four-module import check. Check the active
interpreter and repair the declared baseline, including NumPy >=2.2.0, Cython
>=0.29.21, SymPy >=1.2, PyParsing >=3 but not 3.2.4, Jinja2 >=2.7, setuptools
>=61, and packaging. Use `python -m pip` or the matching Conda environment,
not a different `pip` executable.

If the error says that `DynamicArray` is now compiled from Cython and the
extension must be built, the package is likely being imported from an
incomplete source-like installation or a build whose generated extension does
not match the active Python. Install the released wheel/Conda package in a
clean environment, or use the project's documented development build process
in a separate environment; do not patch `sys.path`.

### Python is too old

Brian2 2.9.0 declares Python >=3.12. A resolver failure, syntax/runtime
incompatibility, or unsupported dependency on an older interpreter requires a
new environment; changing only Brian's version is not a valid 2.9.0 repair.

### Import appears to require Matplotlib

`brian2.__init__` attempts the convenient pylab import and falls back to NumPy
imports when Matplotlib is unavailable. Core Brian import and NumPy-target
execution do not require Matplotlib, but plotting and some interactive import
patterns do. Confirm the actual failing traceback before installing it.

## Cython and compiler failures

Cython-generated code needs the Cython Python package and a working C++
compiler. The checker reports executable names only; it does not compile a
probe. Distinguish:

- **Cython missing:** install the declared runtime dependency in the same
  environment as Brian, then restart Python.
- **Compiler name missing:** install/select a platform toolchain. On Unix,
  check `g++ --version` and use `CXX` only when selecting an approved compiler.
  On Windows, use the MSVC Build Tools shell with C++ tools and a Windows SDK.
- **Compiler found but build fails:** preserve the compiler command/error,
  Python/NumPy/Cython versions, and relevant include/library preference values.
  Suspect incompatible flags, missing headers/SDK, linker libraries, ABI
  mismatch, or a stale cache. Do not infer that an executable check passed the
  build gate.
- **Permission/cache error:** stop concurrent Brian jobs, verify the configured
  cache is writable, and check that the user/current-directory preference files
  did not redirect it. Clear only through the guarded API after approval; see
  [preferences and cache](preferences-and-cache.md).
- **Compiler-dependent workflow not required:** set the process target to
  `numpy` for a core smoke and record that compiled coverage remains
  unverified. Detailed target selection and generated-code repair belong to the
  [code-generation route](../../code-generation/SKILL.md).

Known platform signatures from Brian's documentation:

- On Windows, an old NumPy can report `MSVCCompiler instance has no attribute
  'compiler_cxx'`; upgrade NumPy before considering any workaround.
- A recurring “Missing compiler_cxx fix for MSVCCompiler” message is documented
  as non-fatal when no actual build failure follows.
- On macOS, Cython's `use of undeclared identifier 'isinf'` error may require
  the supported `MACOSX_DEPLOYMENT_TARGET=10.9` environment workaround.
- A missing `msvcr90d.dll` is an old Windows toolchain/NumPy issue; prefer a
  current compatible package/toolchain rather than editing installed NumPy
  files in place.

Do not route a generic package/compiler failure into standalone workflow advice
until ordinary runtime prerequisites are proven. Conversely, once the error is
about generated targets, `set_device`, build directories, or standalone
project compilation, route it to the code-generation sub-skill.

## Optional dependency failures

An absent optional package is not automatically an installation failure:

- **SciPy:** required by selected NumPy spatial/multicompartment templates;
  install it or use a workflow that does not require those operations. A core
  one-neuron NumPy smoke does not prove spatial support.
- **Matplotlib:** needed for plots and some pylab conveniences; omit it for
  headless numerical runs.
- **Pandas:** needed when requesting Pandas state formats such as
  `get_states(format="pandas")`; use the default dictionary/array format when
  Pandas is not installed.
- **IPython/Jupyter:** interactive tooling only. A notebook can import Brian
  while still handling stdout/stderr and progress reporting differently from a
  terminal.
- **brian2tools:** separate visualization/analysis package; its absence does
  not invalidate Brian2 core APIs.
- **GSL:** native development headers/libraries are required for GSL state
  updaters and related generated code. A Python import or `find_library` name
  is not proof that headers, linker paths, and the selected target work. Route
  the actual GSL target/build procedure to the
  [code-generation route](../../code-generation/SKILL.md) and keep a
  non-GSL fallback for core verification.

Do not install an optional dependency just to silence a warning. State which
capability is unavailable and whether a fallback changes numerical method,
output format, plotting, or performance.

## Preference, data, and configuration failures

### Preference syntax or precedence

A malformed `brian_preferences` or `~/.brian/user_preferences` file can fail
Brian import. Values are evaluated, so unquoted strings and misspelled sections
are common causes. The current-directory file overrides the user file.
Inspect targeted values and `prefs.prefs_unvalidated`; repair the smallest
trusted file entry, restart Python, and recheck. The old `default_preferences`
file is not a supported source.

Typical classification:

- `PreferenceError: Parsing error in preference file`: malformed section or
  missing `=`; correct the syntax.
- `PreferenceError: Value ... is invalid`: the value has the wrong type, unit,
  or validator result; use the preference's documented representation.
- `PreferenceError: Preference category ... is unregistered` or an unresolved
  preference warning: spelling error or missing device/extension import.
- Target/cache changes only in one directory: the local `brian_preferences`
  file is overriding the user file; inspect the working directory before
  changing code.

Path-bearing values such as include directories and cache locations should be
redacted in reports. Do not overwrite a user's preference file automatically.

### Input/data errors

If a small model fails after import, first reduce it to a deterministic
one-group NumPy-target case and verify dimensions, variable names, and initial
values. Unit/dimension errors, missing names, invalid equation syntax, and
shape/index mismatches are API/model issues, not installation failures. Route
equations and namespace resolution to
[modeling](../../modeling/SKILL.md) or
[units-and-equations](../../units-and-equations/SKILL.md), scheduling and
network lifecycle to
[simulation-and-recording](../../simulation-and-recording/SKILL.md), monitor
formats/export to [recording](../../recording/SKILL.md), and synapse/input
semantics to [synapses-and-inputs](../../synapses-and-inputs/SKILL.md).

## API misuse versus environment failure

Once `import brian2` succeeds, a `TypeError`, `AttributeError`, `KeyError`, or
`ValueError` from an ordinary Brian call is usually API/model misuse rather than
installation failure. Confirm the call signature and the object's lifecycle
before reinstalling. In this route, common configuration API mistakes are
assigning a whole preference category instead of a preference, using the old
`brian_prefs` name, passing an unregistered `clear_cache` target, or setting a
logging preference after initialization and expecting existing handlers to
change. Preserve the exception and effective preference values, then route
model equations, devices, code-generation targets, network scheduling, or
recording formats to their nearest owner.

If the same call fails only after selecting Cython/GSL/standalone, classify the
native prerequisite first and send the target-specific API to code-generation;
do not mask a compiler failure as a Python API correction.

## Logging diagnostics

Brian initializes a `brian2` logger on import. It writes a temporary debug log
by default at `DEBUG` level, uses `INFO` on the console, and normally deletes
successful-run logs on exit. An uncaught exception keeps the log; disabling
`logging.delete_log_on_exit` preserves it for a controlled reproduction.
Compiler stdout/stderr may be redirected to temporary files by default.

For a controlled diagnostic, before reproducing the error:

```python
from brian2 import BrianLogger, get_logger, prefs

prefs.logging.file_log = True
prefs.logging.file_log_level = "DEBUG"
prefs.logging.console_log_level = "DEBUG"
prefs.logging.delete_log_on_exit = False
prefs.logging.std_redirection = False  # show compiler output while debugging
BrianLogger.initialize()
logger = get_logger("diagnostic")
logger.debug("starting minimal reproduction")
```

Use `DIAGNOSTIC` only when Brian internals need deeper tracing:

```python
BrianLogger.log_level_diagnostic()
logger.diagnostic("include a stable, non-sensitive state summary")
```

`BrianLogger.tmp_log` and the `std_silent` destination attributes identify the
created diagnostic files in the current process. Do not paste their local paths
into a shared skill or report; copy only the relevant error lines after
redaction. If changing `std_redirection` makes a compiler error visible, keep
the first compiler diagnostic and the Python traceback together.

For library-level tests, `catch_logs()` captures Brian warnings/errors as
`(level, logger-name, message)` tuples while suppressing normal handlers. It is
useful for a tiny assertion, not a replacement for preserving the real debug
log. Logging suppressors can hide evidence, so remove temporary filters after
the reproduction.

## `brian2.test()` and workflow failures

`brian2.test()` requires pytest and is a package test harness, not a user-model
validator. Start narrow:

```python
import brian2
brian2.test(codegen_targets="numpy", test_codegen_independent=True)
```

The harness resets preferences to defaults by default, may use multiple
processes when `pytest-xdist` is installed, and restores the previous state on
completion. `test_GSL=True` is opt-in and requires native GSL; standalone,
OpenMP, documentation, and long tests are additional gates. A failing full
suite may expose optional infrastructure unrelated to a user's import or
model. Prefer a selected test or tiny reproduction and report the target,
markers, and optional flags used.

Common workflow distinctions:

- **C++ standalone output collision, build directory, `run_args`, or result
  directory failure:** do not reuse a directory concurrently; route to
  code-generation and preserve the directory/error until the owner decides
  whether cleanup is safe.
- **Jupyter progress not displayed:** C++ standalone text progress can appear
  in the terminal that launched Jupyter rather than the notebook; this is a
  documented output limitation, not necessarily a failed simulation.
- **NaN/large oscillations after a successful run:** automatic numerical
  integration can choose an unsuitable method for some parameter choices;
  route the equations/integrator decision to modeling or code-generation and
  preserve the warning and parameter values.
- **Repeated parallel Cython failures on NFS:** use an independent cache per
  process and review the locking preference as described in
  [preferences and cache](preferences-and-cache.md). Do not clear a shared
  cache while jobs are active.
- **Unexpected unused-object warnings:** `logging.warn_for_unused_objects` can
  be noisy in notebooks, but suppressing it can hide a real network ownership
  mistake. Classify the model/network issue before changing the preference.

Once the failure is workflow-specific, route it to the nearest owner rather
than expanding this installation route. Keep this route's handoff limited to
proven environment facts, effective preferences, diagnostics, and unresolved
optional/toolchain gates. Morphology and multicompartment errors belong to
[spatial-models](../../spatial-models/SKILL.md); standalone project/build
-directory errors belong to
[code-generation](../../code-generation/SKILL.md).
