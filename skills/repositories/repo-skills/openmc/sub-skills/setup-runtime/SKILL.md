---
name: setup-runtime
description: "Route OpenMC installation, CPU/native builds, data and environment
  checks, XML execution, parallel run configuration, bounded testing, and broad
  runtime troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# OpenMC setup and runtime

Use this route when the task is about installing OpenMC, building its executable
or shared library, configuring nuclear data, exporting or running XML inputs,
choosing OpenMP/MPI execution settings, or diagnosing a broad environment or
runtime failure. Establish the smallest required readiness gates before running
anything expensive; a Python import alone is never evidence that native
transport or library mode is ready.

## Route by the user's immediate need

- **Install or build:** read [install-and-build.md](references/install-and-build.md).
- **Run inputs, select flags, or configure parallelism:** read
  [cli-and-execution.md](references/cli-and-execution.md).
- **A command, data path, XML input, shared library, or test fails:** read
  [troubleshooting.md](references/troubleshooting.md) and run the safe diagnostic
  helper when useful: [check_openmc_environment.py](scripts/check_openmc_environment.py)
  with `python scripts/check_openmc_environment.py --help`. The no-argument
  form checks only the Python package and reports optional gates as skipped;
  add `--executable openmc`, `--library PATH`, or
  `--cross-sections PATH` to make those checks requested. A PATH executable is
  probed with only a fixed `--version` argument, never with model input or a
  shell.
- **Model objects, geometry, materials, sources, or settings semantics:** route
  to the model/geometry skill rather than duplicating its API guidance.
- **Tally/statepoint interpretation:** route to the tallies/results skill.
- **Nuclear-data formats, processing, MGXS, or depletion semantics:** route to
  the nuclear-data/depletion skill after this route has established that the
  runtime and data paths are valid.
- **C API/library internals, random ray, CMFD, weight windows, or specialized
  optional integrations:** route to the advanced-solvers skill.

## Readiness distinction

Before a requested operation, record the gate result rather than collapsing
missing prerequisites into one generic failure:

- API/XML-only work needs the Python API gate.
- Command-line transport, plotting, volume calculations, and subprocess-backed
  executor calls need both the Python API and executable gates.
- C-API/library-mode features additionally need the native-library gate.
- Transport and data-dependent depletion need a passing data gate as well.

The bundled diagnostic is a non-mutating structural probe, not a transport
smoke test. Its exit status is nonzero only when the always-on package check or
an explicitly requested executable, library, or data-index check fails.

Treat these as separate gates and report them separately:

1. **Python API gate:** `python -c "import openmc; print(openmc.__version__)"`
   succeeds and the package dependencies are usable. This supports model
   construction and XML generation, but does not prove that a native transport
   runtime exists.
2. **Executable gate:** `openmc --version` or an explicit executable path works.
   This is required for command-line transport, plotting, volume calculations,
   and Python executor calls that launch a subprocess.
3. **Native-library gate:** `import openmc.lib` loads `libopenmc` and is only
   required for C-API/library-mode features such as `Model.init_lib`, depletion
   workflows that use the C API, and selected advanced operations. A Python
   import failure caused by a missing shared library is not evidence that the
   base Python package is broken.
4. **Data gate:** a usable `cross_sections.xml` is configured and every file it
   references exists. A configured index with broken HDF5 references is still a
   failed data gate.

Do not claim a simulation is ready until the relevant gate for that operation is
positive. Keep MPI, DAGMC, libMesh, UWUW, NCrystal, and other optional features
explicitly conditional on their compiler, library, and CMake checks; MPI is not
assumed available.

## Safety and reproducibility boundaries

- Prefer a virtual/Conda environment and an out-of-source native build. Do not
  download nuclear data or mutate shell startup files on the user's behalf.
- Treat model Python and XML as executable/untrusted input. Inspect paths and
  working directories before running them, and use a dedicated output directory.
- Start with tiny API/XML checks or selected unit tests. Transport, regression,
  depletion, and full-suite runs require both the native executable and the
  data prerequisites and can be expensive.
- For comparable tests, use a strict-floating-point native build when needed and
  bound OpenMP threads (the project recommends `OMP_NUM_THREADS=2` for test
  stability). Do not imply that bitwise agreement follows from arbitrary
  compiler, thread, or MPI configurations.

## Operational handoff

When this route completes, report the package version/import result, executable
path/version or the reason that gate is unavailable, native-library binding
result, data-index parse result including missing or non-file references, build
flags, thread/process settings, XML/output location, and the next route if the
request is about model construction or results. Keep data, executable, and
shared-library findings separate. Link to the detailed references rather than
expanding their APIs in this router.
