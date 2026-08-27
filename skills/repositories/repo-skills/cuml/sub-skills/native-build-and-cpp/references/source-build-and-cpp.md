# cuML source build and C++/CUDA operating guide

This reference is for agents working from a cuML source checkout or from an environment containing a source-built `libcuml`. It condenses the source-build, public C++ API, and native-test decisions needed for safe local development. It is not a general installed-wheel usage guide.

## 1. Decide whether source build is necessary

Prefer prebuilt packages when the user only needs Python estimator workflows. Choose a source build when any of these are true:

- A C++/CUDA implementation, public header, Cython binding, packaging recipe, or build flag changed.
- The task requires validating `libcuml.so`, C++ examples, or CTest/gtests.
- A Python package source build must be checked against a locally built `libcuml`.
- ABI, linker, CUDA architecture, or RAPIDS dependency resolution is the failure under investigation.

Build the smallest component that covers the change:

| Need | Smallest target | Notes |
| --- | --- | --- |
| C++/CUDA library or public C++ header change | `libcuml` | Builds and installs the C++ shared library plus selected native targets. |
| Python package wrapper or Cython binding change | `libcuml` then `cuml` | `cuml` expects matching C++/RAPIDS libraries in the active install prefix. |
| Primitive test change | `prims` | Covers ml-prims test target only. |
| Multi-GPU C++ test change | `cpp-mgtests` | Requires MPI and RAPIDS distributed dependencies; skip when not installed. |
| C++ benchmark investigation | `bench` or `prims-bench` | High-cost; never use as a default smoke test. |
| Clean rebuild | `clean` then selected target | Deletes build artifacts; use only when stale CMake/build state is suspected. |

## 2. Hardware and software prerequisites

### CUDA device requirements

- CUDA 12.x runtime/test execution requires NVIDIA GPU compute capability **7.0 or higher**.
- CUDA 13.x runtime/test execution requires NVIDIA GPU compute capability **7.5 or higher**.
- A GPU is not required merely to configure or compile source, but GPU execution is required for cuML functionality, C++ examples, CTest GPU tests, and Python estimator tests.

### Required build tools

- CUDA Toolkit **>= 12.2**, including development libraries for cudart, cuBLAS, cuSPARSE, cuSOLVER, cuRAND, and cuFFT.
- GCC **>= 13** for supported Linux source builds. Generated development environments may select a newer GCC in the same supported family.
- CMake **>= 4.0**.
- Ninja, unless overriding the generator deliberately.
- Python **>= 3.11 and <= 3.14**.
- Cython **>= 3.2.2**. If dependency metadata excludes a specific Cython patch release, honor that exclusion.

Run the bundled probe before building:

```bash
python scripts/source_build_probe.py --format text
```

Use `--strict` to make missing required build tools a nonzero result, and `--require-gpu --target-cuda-major 13` when validating a CUDA 13 runtime/test job.

## 3. RAPIDS dependency pin matching

All RAPIDS libraries in a build/test environment must match the cuML version family and CUDA variant. For a `26.10` source tree, the matching family is `26.10.*` for packages such as:

- C++ libraries: `librmm`, `libraft`, `libcuvs`, and related native dependencies.
- Python/runtime packages: `rmm`, `pylibraft`, `cudf`, `libcuml`, `cuml`, `cupy` for the chosen CUDA major, CUDA Python bindings, and CUDA toolkit runtime components.
- Optional distributed packages: `rapids-dask-dependency`, `dask-cudf`, `raft-dask`, and `dask-cuda` with the same RAPIDS and CUDA variant.

Do not mix CUDA 12 and CUDA 13 package suffixes, and do not mix stable and nightly channels/wheels in one prefix unless every RAPIDS package is intentionally pinned to a compatible family. Validate package consistency with the package manager (`pip check` for pip environments, or the conda solver/explicit package list for conda environments) before blaming CMake or cuML source.

## 4. Conda development environment pattern

A complete development environment should include the CUDA toolkit, compilers, CMake, Ninja, RAPIDS native libraries, Python build/runtime dependencies, and test extras. The generated `all_cuda-<cuda>_arch-<arch>.yaml` environments encode those pins. A typical source-build environment looks like:

```bash
conda create -n cuml_dev python=3.14
conda env update -n cuml_dev --file conda/environments/all_cuda-133_arch-$(uname -m).yaml
conda activate cuml_dev
```

Use the CUDA 12 environment file only when the target package/toolkit stack is CUDA 12. Use the CUDA 13 environment file when building CUDA 13 variants. If disk, solver time, or dependencies are constrained, install only the needed component groups, but keep the RAPIDS version and CUDA variant aligned.

## 5. `build.sh` source-build taxonomy

The source checkout provides a build driver that installs to `$INSTALL_PREFIX` when set, otherwise `$CONDA_PREFIX` when active, otherwise a build-local install prefix. Ninja is the default generator unless `CMAKE_GENERATOR` is set.

Common commands:

```bash
./build.sh --help                         # show supported targets and flags
./build.sh                                # default: build/install libcuml, cuml, and prims
./build.sh libcuml                        # build/install the C++/CUDA library
./build.sh cuml                           # build/install the Python package only
./build.sh prims                          # build ml-prims tests
./build.sh cpp-mgtests                    # build multi-GPU C++ tests; requires MPI/distributed deps
./build.sh clean                          # remove existing build/configuration artifacts
```

Useful flags and environment variables:

| Control | Effect | When to use |
| --- | --- | --- |
| `--configure-only` | Run CMake configure without compiling. | Fast dependency/flag validation. |
| `--ccache` | Enable compiler cache. | Repeated local builds or branch switching. |
| `--singlegpu` | Build without multi-GPU components; Python install also receives `--singlegpu`. | Single-GPU development or missing distributed dependencies. |
| `--allgpuarch` | Build for all RAPIDS-supported GPU architectures instead of native arch only. | Packaging or deploy-to-many-GPU scenarios; slower. |
| `--nolibcumltest` | Disable libcuml C++ tests during build. | Faster compile when C++ tests are not needed. |
| `-n` / `--no-install` | Build but do not install. | Inspect local build artifacts without changing prefix. |
| `-g` / `--debug` | RelWithDebInfo build. | Native debugging/profiling. |
| `-v` / `--verbose` | Verbose build/CMake output. | Diagnose compiler/linker errors. |
| `--nvtx` | Enable NVTX markers. | Profiling instrumentation. |
| `PARALLEL_LEVEL=N` | Limit build parallelism. | Avoid RAM pressure or reduce system contention. |
| `CUML_EXTRA_CMAKE_ARGS="..."` | Append/override CMake flags. | Narrow algorithms, set architecture, disable examples/tests, add paths. |
| `CUML_EXTRA_PYTHON_ARGS="..."` | Extra arguments to Python package installation. | Rare source-package customization. |

Examples:

```bash
PARALLEL_LEVEL=8 ./build.sh libcuml --ccache --nolibcumltest
./build.sh libcuml --configure-only --singlegpu
CUML_EXTRA_CMAKE_ARGS='-DCMAKE_CUDA_ARCHITECTURES=80 -DBUILD_CUML_BENCH=OFF' ./build.sh libcuml
./build.sh libcuml cuml prims
```

## 6. Manual CMake outline

Use manual CMake when you need exact control or must reproduce a build-driver failure. From the source checkout root:

```bash
cmake -S cpp -B cpp/build -G Ninja \
  -DCMAKE_INSTALL_PREFIX="$CONDA_PREFIX" \
  -DCMAKE_PREFIX_PATH="$CONDA_PREFIX" \
  -DCMAKE_CUDA_ARCHITECTURES="NATIVE" \
  -DCMAKE_BUILD_TYPE=Release \
  -DBUILD_CUML_CPP_LIBRARY=ON \
  -DBUILD_CUML_TESTS=ON \
  -DBUILD_CUML_MG_TESTS=OFF \
  -DBUILD_PRIMS_TESTS=ON \
  -DBUILD_CUML_EXAMPLES=ON \
  -DBUILD_CUML_BENCH=OFF

cmake --build cpp/build -j"${PARALLEL_LEVEL:-$(nproc)}" --target install
```

If CUDA is installed but not on `PATH`, set the CUDA toolkit root before configure:

```bash
export CUDA_BIN_PATH="$CUDA_HOME"
```

For faster or reproducible architecture-specific builds, replace `NATIVE` with a semicolon-separated list such as `70`, `75`, `80`, `86`, or `90`. For package-style broad compatibility, use the source build driver `--allgpuarch` rather than guessing architecture lists.

Important CMake options:

| Option | Default | Use |
| --- | --- | --- |
| `BUILD_CUML_CPP_LIBRARY` | `ON` | Disable only when embedding a limited consumer build. Disabling also disables tests/examples/benchmarks. |
| `BUILD_CUML_TESTS` | `ON` | Build single-GPU C++ tests. |
| `BUILD_CUML_MG_TESTS` | `OFF` | Build multi-GPU C++ tests; requires MPI and distributed dependencies. |
| `SINGLEGPU` | `OFF` | Disable multi-GPU sources/comms and force MG tests off. |
| `BUILD_PRIMS_TESTS` | `ON` | Build primitive tests. |
| `BUILD_CUML_EXAMPLES` | `ON` | Build public C++ usage examples. |
| `BUILD_CUML_BENCH` | `ON` | Build benchmarks; explicitly set `OFF` unless benchmarking is requested. |
| `DETECT_CONDA_ENV` | `ON` | Let CMake use the active conda prefix for dependencies and install prefix. |
| `DISABLE_OPENMP` | `OFF` | Turn off OpenMP if the host toolchain/runtime requires it. |
| `NVTX` | `OFF` | Enable NVTX instrumentation for profiling. |
| `USE_CCACHE` | `OFF` | Use compiler cache. |
| `CMAKE_CUDA_ARCHITECTURES` | unset by manual configure | Use `NATIVE`, explicit numbers, or package-style all-architecture build. |

Build the Python package after a compatible `libcuml` is installed in the active prefix:

```bash
python -m pip install --no-build-isolation --no-deps \
  --config-settings rapidsai.disable-cuda=true \
  python/cuml
```

The `--no-build-isolation --no-deps` pattern deliberately uses the active RAPIDS/CUDA prefix; do not let pip solve a second incompatible RAPIDS stack during a source-build validation.

## 7. Public C++ API and example patterns

The public C++ surface is under the `cuml/` include namespace and is built around CUDA device memory, RAFT handles/streams, and explicit output buffers. Common public families include clustering, decomposition, linear models, manifold learning, neighbors, SVM, tree/forest, metrics, datasets, explainers, time-series, and symbolic-regression/genetic APIs.

C++ applications typically:

1. Select and initialize a CUDA device.
2. Create a CUDA stream and `raft::handle_t` for stream/allocator context.
3. Allocate device inputs/outputs with CUDA or RMM.
4. Fill algorithm parameter structs from `cuml/...` headers.
5. Call a stateless `ML::...` or `cuml::...` public function with pointers, sizes, parameters, and the RAFT handle.
6. Synchronize/copy results only where needed.
7. Free resources or rely on RAII wrappers.

Standalone C++ example builds use this CMake shape:

```cmake
cmake_minimum_required(VERSION 3.26.4 FATAL_ERROR)
project(my_cuml_example LANGUAGES CXX CUDA)
set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
find_package(cuml REQUIRED)
add_executable(my_cuml_example my_cuml_example.cpp)
target_link_libraries(my_cuml_example PRIVATE cuml::cuml)
set_target_properties(my_cuml_example PROPERTIES LINKER_LANGUAGE "CUDA")
```

Configure the standalone project with a prefix that can find the installed `cuml` package, for example by setting `CMAKE_PREFIX_PATH`, `cuml_ROOT`, or using the same conda/install prefix that received `libcuml`.

### Example families

- **KMeans**: includes clustering headers, sets `ML::kmeans::KMeansParams`, uses a RAFT handle, calls `ML::kmeans::fit` and `ML::kmeans::predict`, and can run a tiny built-in dataset when no input file is supplied. Nontrivial input is row-major text with `-num_rows`, `-num_cols`, `-input`, `-k`, and `-max_iterations` controls.
- **DBSCAN**: includes `cuml/cluster/dbscan.hpp`, runs a default 25-sample by 3-feature dataset when no input is supplied, and reports a cluster histogram/noise count. External input is flattened text plus `-num_samples`, `-num_features`, `-min_pts`, `-eps`, and optional batch-memory controls.
- **Symbolic regression**: uses genetic/symbolic-regression headers, consumes generated train/test feature and label text files, supports mutation/population/generation/stopping controls, and demonstrates RMM device containers plus CUDA event timing. Inputs are treated as column-major in the example workflow.

Treat these examples as API demonstrations and optional native verification candidates. Do not turn them into routine health checks unless the environment has a source build, CUDA runtime, and the user asked for C++ validation.

## 8. Native test command selection

Choose tests by change surface and backend availability. Start with collection/listing commands before broad execution.

### C++/CUDA tests

```bash
ctest --test-dir cpp/build -N
ctest --test-dir cpp/build --output-on-failure
ctest --test-dir cpp/build -R 'kmeans|dbscan|neighbors' --output-on-failure
```

Use CTest only after C++ tests have been built or installed. Multi-GPU tests require the MG build option plus MPI/distributed dependencies and compatible hardware. If tests are installed in a package prefix rather than a checkout build tree, run `ctest` from the installed gtests directory for that prefix.

### Python tests for source changes

From the Python source directory:

```bash
python -m pytest cuml/tests --collect-only
python -m pytest cuml/tests --ignore=cuml/tests/dask --ignore=cuml/tests/test_nccl.py -q
python -m pytest cuml/cuml_accel_tests -q
python -m pytest -p cudf.pandas cuml/tests --ignore=cuml/tests/dask --quick_run -q
```

Use Dask tests only when Dask-CUDA, Dask-cuDF, RAFT-Dask, UCX/UCXX/NCCL requirements, and GPU topology are ready:

```bash
python -m pytest cuml/tests/dask -q
python -m pytest cuml/tests/dask --run_ucx -q
```

Test-selection heuristics:

- Public C++ header/API change: build `libcuml`, list CTest tests, run matching CTest regex, then a small Python wrapper test if bindings are affected.
- Python estimator binding change: build/install `libcuml` and `cuml`, run matching `cuml/tests/test_*.py`, plus scikit-learn compatibility checks when estimator behavior changed.
- `cuml.accel` change: run accelerator CLI/help and focused accelerator pytest files; route detailed accelerator behavior to the accel sub-skill.
- Distributed/MNMG change: verify dependency group first, then Dask pytest subset and MG C++ tests if relevant.
- Packaging/build change: run the source-build probe, configure-only build, minimal build target, `pip check` or equivalent package-manager consistency check, then a focused import/health check.

## 9. Contributor review rules to apply

### C++/CUDA changes

Only flag real CRITICAL/HIGH issues. Prioritize:

- Unchecked CUDA kernel launches, memory copies, synchronization, or CUDA library calls. Use RAFT error macros in cuML implementation code where appropriate.
- Race conditions, invalid memory access, host/device confusion, missing synchronization, or wrong stream lifecycle.
- GPU/device memory leaks; prefer RMM/RAFT/RAII containers such as `rmm::device_uvector` and a `raft::handle_t` stream context.
- Integer overflow/underflow in host-side allocation sizes, launch dimensions, spans, or pointer offsets. Use checked arithmetic helpers and explicit checked narrowing for CUDA launch dimensions.
- Data-layout mismatches, especially row-major versus column-major assumptions crossing C++/Python boundaries.
- Numerical instability that can produce wrong ML results.
- Public API breakage in exported headers; public functions should remain stateless and document POD/handle/pointer contracts.
- Tests must validate numerical correctness on synthetic or bundled data; do not depend on external datasets.

Ignore formatting and personal style preferences that do not affect correctness, API stability, or maintainability.

### Python/Cython changes adjacent to native code

Prioritize:

- Scikit-learn compatibility: names, defaults, required fitted attributes, and estimator behavior.
- No fitted attributes with trailing underscores initialized in `__init__`; learned state belongs after `fit`.
- Correct conversion/preservation of cuDF, pandas, NumPy, and device-array inputs, including memory order.
- `fit` state reset and `predict`/`transform` fitted-state checks.
- Tests comparing numerical results, edge cases, different input types, and standalone test functions.
- Public API/docs/compatibility lists updated when a new estimator or accelerator-supported estimator is added.
