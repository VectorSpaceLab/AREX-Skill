# Build and Test Workflows

## When to Read

Read this before proposing CMake commands, selecting native tests, diagnosing wrapper build failures, or deciding whether a check is safe to run in an agent session.

## CMake Build Concepts

OpenMM is a CMake project that builds shared/static libraries, optional platforms, optional plugins, C++ tests, examples, and Python wrappers. A typical maintainer build is an out-of-source build with options selected up front.

Common configuration shape:

```bash
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release -DOPENMM_BUILD_SHARED_LIB=ON -DOPENMM_BUILD_STATIC_LIB=OFF
cmake --build build --parallel
```

Important options and defaults surfaced by the top-level build files:

| Option | Purpose | Notes |
| --- | --- | --- |
| `OPENMM_BUILD_SHARED_LIB` | Build shared OpenMM libraries | Default on. Most plugin and wrapper workflows assume shared libraries. |
| `OPENMM_BUILD_STATIC_LIB` | Build static OpenMM libraries | Default off. Static builds require extra compile definitions and can expose ABI/link assumptions. |
| `OPENMM_BUILD_CPU_LIB` | Build optimized CPU platform | Default on when supported. CPU tests can be disabled separately. |
| `OPENMM_BUILD_AMOEBA_PLUGIN` | Build Amoeba plugin | Default on. Python wrappers depend on plugin build options for plugin APIs. |
| `OPENMM_BUILD_RPMD_PLUGIN` | Build RPMD plugin | Default on. RPMD has platform-specific plugin implementations. |
| `OPENMM_BUILD_DRUDE_PLUGIN` | Build Drude plugin | Default on. Drude includes serialization and wrapper pieces. |
| `OPENMM_BUILD_PME_PLUGIN` | Build CPU PME plugin | Default on. Some CPU-test behavior depends on whether the PME plugin is present. |
| `OPENMM_BUILD_PYTHON_WRAPPERS` | Build Python wrappers | Default on. Requires plugin prerequisites and generated/staged files. |
| `OPENMM_BUILD_EXAMPLES` | Build example executables | Default on. Examples are not the first validation target for internal changes. |
| `BUILD_TESTING` | Enable CTest registration | Standard CMake/CTest option. Platform tests have additional per-platform switches. |

Backend-specific platform directories define additional test switches such as `OPENMM_BUILD_CPU_TESTS`, `OPENMM_BUILD_CUDA_TESTS`, `OPENMM_BUILD_OPENCL_TESTS`, `OPENMM_BUILD_HIP_TESTS`, and double-precision variants for GPU backends.

## Focused Native Test Selection

Native C++ tests are registered with CTest from subsystem `CMakeLists.txt` files. They require configured and built test executables. Treat them as build-required candidates, not safe default checks.

Selection patterns:

```bash
ctest --test-dir build -R TestSerializeHarmonicBondForce --output-on-failure
ctest --test-dir build -R TestReferenceCustom --output-on-failure
ctest --test-dir build -R TestCpuNonbondedForce --output-on-failure
ctest --test-dir build -R TestCudaNonbondedForceSingle --output-on-failure
```

Guidance:

- Serialization changes: run the matching `TestSerialize*` executable and any plugin serialization tests for plugin-owned classes.
- Reference implementation changes: run matching `TestReference*` tests before optimized platform tests.
- CPU implementation changes: run matching `TestCpu*` tests and relevant core tests.
- CUDA/OpenCL/HIP common changes: run single precision first, then mixed/double variants when hardware and build options support them.
- Plugin changes: run plugin API tests, plugin serialization tests, and platform-specific plugin tests for each implemented platform.

The repository includes `devtools/run-ctest.py` as a maintainer helper for CTest workflows, but it is reference-only for this generated skill because it is tied to a checkout and build tree. Prefer documenting command patterns rather than bundling a script that would falsely imply portability.

## Python Test Candidates

Python tests live under the Python wrapper test tree and use `pytest` configuration. They are useful for public Python API, app-layer, serialization, and installed-package behavior, but they also depend on a built or installed package and selected platform availability.

Typical shapes:

```bash
python -m pytest wrappers/python/tests -q
python -m pytest wrappers/python/tests -q -k serialization
python -m pytest wrappers/python/tests -q -k "not cuda and not opencl"
```

Use Python tests after wrapper or public API changes, not as the only validation for C++ kernel correctness. If a prebuilt installed package is being used only for API inspection, do not assume it validates local source changes.

## Python Wrapper Build Notes

The Python build uses Cython and NumPy and links extensions against OpenMM libraries. The wrapper build expects environment variables that point to installed or staged OpenMM artifacts:

```bash
export OPENMM_INCLUDE_PATH=/path/to/openmm/include
export OPENMM_LIB_PATH=/path/to/openmm/lib
python -m pip install .
```

Do not embed machine-specific values in generated instructions. For troubleshooting, ask the user to substitute their actual install or build-tree paths.

Wrapper-specific facts:

- Missing `OPENMM_INCLUDE_PATH` produces a direct setup error asking for the OpenMM include directory.
- Missing `OPENMM_LIB_PATH` produces a direct setup error asking for the OpenMM library directory.
- Debug library builds can use debug library names on non-Windows platforms when the build environment requests them; Windows debug-library use is explicitly unsupported by the wrapper build logic.
- Python package extras may declare platform packages for CUDA or HIP backends, but wrapper development still requires compiled core libraries and headers.

## Wrapper Generation

Wrapper generation through `wrappers/generateWrappers.py` and plugin-specific generator helpers is a maintainer workflow, not a portable runtime helper. The generation pipeline depends on source metadata, Doxygen/XML outputs, generated staging directories, and plugin-specific generator scripts. Keep it reference-only unless the user has an active checkout with the generator dependencies installed and asks to run it.

When a C++ public API change is not reflected in Python:

1. Confirm the C++ header and method are in the wrapper generation inputs.
2. Regenerate wrappers in the maintainer build workflow.
3. Rebuild the Python package against the matching headers/libs.
4. Run focused Python import/signature tests and any related wrapper tests.
5. Avoid manually editing generated wrapper outputs as a long-term fix.

## Safe vs Build-Required Checks

Safe static checks that do not require a full build:

- Inspect CMake options and test registration names.
- Confirm expected source/header/proxy/test files exist in the planned change set.
- Check generated skill references for self-contained commands and no local path leaks.

Build-required checks:

- `cmake --build`.
- `ctest` native tests.
- Python wrapper rebuilds.
- CUDA/OpenCL/HIP platform tests.
- Plugin load tests against newly built libraries.

Mark build-required native candidates as skipped unless the user confirms a suitable build tree and hardware/runtime availability.
