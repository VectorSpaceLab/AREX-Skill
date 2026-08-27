# Native and optional builds

Use this reference to classify what can be checked in the current runtime. It
never downloads dependencies or treats a configured option as a verified
capability.

## Base CPU build contract

The native build is a C++17 CMake project. HDF5 is required; OpenMP is enabled
by default in the documented option set, and CMake requires an OpenMP compiler
when it is on. libpng is optional for plotting. The build produces both the
`openmc` executable and a shared `libopenmc` library on non-Windows platforms;
the build copies the shared library into the Python binding package location
for `openmc.lib` to load.

A caller who intentionally has a source tree can use an explicit disposable
build directory:

```bash
cmake -S <source-dir> -B <build-dir> \
  -DCMAKE_BUILD_TYPE=RelWithDebInfo \
  -DOPENMC_USE_OPENMP=ON \
  -DOPENMC_BUILD_TESTS=ON
cmake --build <build-dir> --parallel
ctest --test-dir <build-dir> --output-on-failure
```

Use `OPENMC_ENABLE_STRICT_FP=ON` when reproducible floating-point regression
references are the verification target. Do not run a broad CTest or transport
regression suite merely to prove that a library exists. First confirm the
configuration, build artifacts, and data prerequisites; then select a bounded
native test.

The following CMake options are the relevant gates:

| Option | Meaning | Evidence required before claiming support |
|---|---|---|
| `OPENMC_USE_OPENMP` | shared-memory parallelism | successful compiler/dependency detection and build |
| `OPENMC_BUILD_TESTS` | C++ unit-test targets | configured ON, successful test target build |
| `OPENMC_ENABLE_STRICT_FP` | strict floating-point compile definition | loaded library or cache reports ON |
| `OPENMC_USE_MPI` | MPI support | MPI package/compiler detection, successful build, and an MPI launch check |
| `OPENMC_USE_DAGMC` | DAGMC/MOAB CAD geometry | DAGMC found, version at least 3.2.0, successful link, and `feature_enabled('dagmc')` true |
| `OPENMC_USE_LIBMESH` | libMesh unstructured mesh tallies | libMesh package found and successful link, then a feature query/native check |
| `OPENMC_USE_UWUW` | UWUW material support | DAGMC is ON and the discovered DAGMC build has UWUW |

`OPENMC_USE_UWUW=ON` without DAGMC is an invalid configuration. Parallel HDF5
also requires MPI to be enabled; a parallel-HDF5 detection with MPI disabled
is a configuration error rather than an automatic fallback.

Random ray, CMFD, photon routines, and weight-window code are part of the
regular native source set; they do not have independent `feature_enabled`
strings. Their availability still requires a successful compatible native
build, and their data/model restrictions must be checked at execution time.
There is no evidence for a CUDA-specific OpenMC package or GPU backend in this
contract.

## Inspecting a build without mutation

Run the bundled diagnostic from any working directory. Start with help or a
no-argument smoke; pass explicit paths when more than one build may exist:

```bash
python <advanced-solvers-skill-dir>/scripts/check_native_features.py --help
python <advanced-solvers-skill-dir>/scripts/check_native_features.py
python <advanced-solvers-skill-dir>/scripts/check_native_features.py \
  --build-dir <build-dir> \
  --library <path-to-libopenmc.so> \
  --executable <path-to-openmc>
```

The helper only performs these safe operations:

- probes `import openmc` without importing `openmc.lib`;
- checks existence, readability, and executable status of supplied or
  build-directory-discovered artifacts without running them;
- parses `CMakeCache.txt` for the OpenMC feature options;
- after a shared library actually loads and exposes
  `openmc_get_feature_enabled`, queries the supported names `dagmc`, `libmesh`,
  `strict_fp`, and `uwuw`.

It does not invoke CMake, a compiler, the executable, a simulation, a package
manager, or a network client. A missing/unloadable shared library is reported
separately from a failed base Python import, and feature flags are omitted from
the report until the library query is usable. A cache value is configuration
evidence; a successful C API query is runtime evidence. Conflicting values are
reported rather than reconciled by inference.

The native helper intentionally does not call `openmc.lib`: importing that
package itself attempts to load the package-local shared library and is
therefore the wrong probe when the library may be absent or when an explicit
library path is being inspected.

## Safe test selection

Use a staged gate:

1. **Base Python/API gate:** `import openmc`, representative class/signature
   inspection, and data-free XML construction. This does not prove
   `openmc.lib`.
2. **Native artifact gate:** executable/shared-library checks and, if a build
   is available, a CMake target build. The absence of `libopenmc` is expected
   before a native build.
3. **C API gate:** only after the shared library loads, query the four supported
   feature names, then use a tiny model and the documented lifecycle. Keep
   `openmc.lib.init()`/`finalize()` paired even on errors; use
   `run_in_memory()` for automatic cleanup.
4. **C++/CTest gate:** select small geometry, tally, mesh, ray, or photon unit
   tests from a successfully configured test build. These test native semantics
   and do not substitute for cross-section-dependent transport validation.
5. **Solver gate:** random-ray and CMFD cases require their native entry points,
   valid XML/model inputs, and often multigroup or cross-section data.
   Weight-window generation and full transport remain conditional on data and
   can be expensive.
6. **Optional integration gate:** run a DAGMC, libMesh, MPI, or NCrystal case
   only when the corresponding dependency and library feature are positively
   identified. Otherwise record the integration as unverified.

Do not use full C API, random-ray, weight-window, or CMFD regression cases as
an import gate: their complete behavior requires a built shared library and,
for transport, compatible data/model fixtures. Likewise, absence of
`OPENMC_CROSS_SECTIONS` blocks transport claims but does not block base
Python/XML or pure native API checks.

## Native library and executable distinctions

- A working Python distribution can have `openmc` importable while the native
  executable is absent. This blocks command-line transport, not Python model
  authoring.
- The base Python import can succeed while the package-local shared library is
  absent or stale. This blocks `openmc.lib` until the library is built and made
  available to the binding; do not classify that as a base package failure.
- The executable can be present while the shared library is absent, unreadable,
  or unloadable because a dependent library is missing. The diagnostic checks
  these as separate artifacts and never infers one from the other.
- A shared library can load while an optional feature is false. Use
  `openmc.lib.feature_enabled()` or the helper's library query rather than
  relying on filenames or CMake intent.
- A library can load with optional feature true while its external geometry or
  data file is absent. That is an input/runtime failure, not evidence that the
  feature query is wrong.

## Optional integration boundaries

- MPI is detected by CMake's MPI package. If it is not detected, do not suggest
  an MPI build command will succeed. Even when MPI is built, random ray warns
  that it performs work on rank 0 instead of providing efficient decomposition.
- DAGMC requires an external DAGMC installation and a supported version. A
  Python `DAGMCUniverse` object can serialize its filename without proving that
  the native reader is enabled.
- libMesh requires the external libMesh package; its presence is separate from
  the regular mesh classes.
- NCrystal is a runtime-loaded external library for NCrystal materials and a
  Python dependency for `Material.from_ncrystal`. It is not one of the four
  C-API build feature names.
- Photon transport requires compatible photon data and is rejected in
  multigroup mode by native settings validation. Charged-particle handling is
  local-deposition/secondary-photon physics, not an optional charged-particle
  geometry backend.

## Verification record language

Use precise statuses:

- `verified`: the specified artifact/API/feature check ran and passed;
- `configured`: a cache or build option requests a feature, but runtime proof
  has not run;
- `available`: an executable or library was found, without a solver/data test;
- `unverified`: optional dependency, data, or test prerequisite was absent;
- `blocked`: a required base import or CPU build/API check failed.

Never turn `configured`, `available`, or `unverified` into `verified` by
inference.
