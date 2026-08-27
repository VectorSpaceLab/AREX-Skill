# Source-build and native C++ troubleshooting

Use this when a cuML source build, `libcuml`/`cuml` package build, C++ example, CTest run, or native-adjacent Python test fails. Start with the non-mutating probe, then narrow by symptom.

```bash
python scripts/source_build_probe.py --format text
```

Add `--strict` for build-tool readiness and `--require-gpu --target-cuda-major 12|13` for runtime/test readiness.

## Quick triage table

| Symptom | Most likely cause | First action |
| --- | --- | --- |
| GPUs visible but `nvcc` missing | Runtime driver is present but CUDA Toolkit development tools are absent. | Install a development CUDA toolkit or the matching conda environment that includes `cuda-nvcc` and CUDA dev libraries. |
| Configure says CMake is too old | System CMake is used instead of development environment CMake. | Activate the intended environment and confirm `cmake --version` is >= 4.0. |
| Configure cannot find RAFT/RMM/cuVS/cuDF | RAPIDS dependency pins or prefix path are wrong. | Verify all RAPIDS packages share the same version family and CUDA variant; set `CMAKE_PREFIX_PATH`/install prefix to the active environment. |
| Compile fails with unsupported GPU architecture | `CMAKE_CUDA_ARCHITECTURES` does not match target CUDA/GPU support. | Use `NATIVE` for local builds or an explicit supported architecture list; use all-arch only for package-style builds. |
| Python package build pulls unexpected dependencies | Build isolation or dependency solving created a second RAPIDS stack. | Use active-prefix source builds with `--no-build-isolation --no-deps` after installing matching dependencies. |
| CTest reports no tests or missing test directory | C++ tests were not built/installed, or the wrong build/install tree is used. | Reconfigure with tests enabled, build the needed target, then list tests with `ctest -N`. |
| Python tests import stale package | Editable/source package and installed package are mixed. | Check which package is imported outside the checkout; rebuild/reinstall into one prefix and clear stale build artifacts if needed. |
| Dask/MNMG tests fail at import/startup | Optional distributed dependency group or communication stack is missing. | Install matching Dask-CUDA/Dask-cuDF/RAFT-Dask/UCX/NCCL requirements or choose single-GPU tests. |

## CUDA hardware and toolkit failures

### No GPU, hidden GPU, or unsupported compute capability

cuML runtime validation requires an NVIDIA GPU. Hardware thresholds depend on CUDA major version:

- CUDA 12.x: compute capability >= 7.0.
- CUDA 13.x: compute capability >= 7.5.

If the GPU is absent or below threshold, source compilation may still succeed, but C++ examples, CTest GPU tests, Python estimator tests, and health checks are not valid. Check `CUDA_VISIBLE_DEVICES`, container GPU passthrough, driver installation, and compute capability before treating algorithm failures as source bugs.

### `nvidia-smi` works but `nvcc` is missing

This means the runtime driver can see GPUs, but the CUDA Toolkit compiler is not available. Prebuilt cuML packages may still run, but source builds cannot compile CUDA code. Install the matching development CUDA toolkit and ensure these are on the active environment/path:

- `nvcc`
- CUDA dev libraries for cudart, cuBLAS, cuSPARSE, cuSOLVER, cuRAND, cuFFT
- CMake, Ninja, GCC/G++

If CUDA is installed outside the active prefix, set the toolkit root before configure:

```bash
export CUDA_HOME=/path/to/cuda
export CUDA_BIN_PATH="$CUDA_HOME"
```

Use environment variables only after verifying they point to the intended toolkit; a driver-only install is not enough.

### Toolkit/package CUDA variant mismatch

A CUDA 13 `cuml`/`libcuml` stack must use CUDA 13-compatible CuPy, CUDA toolkit wheels or conda packages, RAPIDS packages, and nvJitLink/runtime components. A CUDA 12 stack must use CUDA 12 variants. Mixed suffixes (`cu12` with `cu13`) usually produce import failures, link errors, missing symbols, or runtime JIT/link errors.

## Compiler, CMake, Ninja, and Python failures

- GCC must be >= 13. If the system default is older, use the compiler packages from the development environment and make sure they precede system compilers on `PATH`.
- CMake must be >= 4.0 for the source tree. Standalone examples may have lower minimums, but the main C++ build requires CMake 4.
- Ninja is the default generator. If Ninja is absent, either install it or set a deliberate alternative `CMAKE_GENERATOR` before invoking the build driver.
- Python must be >= 3.11 and <= 3.14. Do not use an older test runner to build the package.
- Cython must be >= 3.2.2. Honor any patch-level exclusions from the dependency metadata.

When tool versions look correct but CMake still sees old tools, print the active environment and command resolution, then rerun configure in a clean shell. Avoid mixing a system compiler with conda-provided CUDA/RAPIDS dependencies unless that combination is explicitly supported.

## RAPIDS dependency and package pin failures

Common signals:

- `find_package` cannot locate RMM, RAFT, cuVS, cuDF, or `cuml`.
- Python imports load a different RAPIDS version than the source tree.
- Linker errors mention missing symbols from RAFT/RMM/cuVS/libcuml.
- `pip check` or the conda solver reports incompatible RAPIDS packages.

Corrective steps:

1. Keep all RAPIDS packages in the same version family as cuML source, for example `26.10.*` with `26.10.*`.
2. Keep CUDA variants aligned (`cu12` with CUDA 12 packages, `cu13` with CUDA 13 packages).
3. Prefer one package source/channel family per prefix. Do not combine stable release packages with nightly packages unless all RAPIDS packages are pinned intentionally.
4. Set both install and prefix search paths during manual CMake configure:

```bash
cmake -S cpp -B cpp/build -G Ninja \
  -DCMAKE_INSTALL_PREFIX="$CONDA_PREFIX" \
  -DCMAKE_PREFIX_PATH="$CONDA_PREFIX" \
  -DCMAKE_CUDA_ARCHITECTURES="NATIVE"
```

5. For standalone C++ consumers, configure with a prefix that contains the installed `cuml` CMake package, using `CMAKE_PREFIX_PATH` or `cuml_ROOT`.

## CMake configure/link issues

### Runtime search path warnings

A CMake warning about unsafe runtime search paths can occur when the install prefix contains libraries that shadow implicit directories. If the warning matches that pattern and the dependency prefix is otherwise correct, it is usually safe. To silence a known benign prefix conflict, add:

```bash
-DCMAKE_IGNORE_PATH="$CONDA_PREFIX/lib"
```

### Cannot find CUDA or wrong CUDA compiler

Check:

```bash
nvcc --version
cmake --version
```

Then ensure the intended CUDA toolkit appears in `PATH`, `CUDA_HOME`, and `CUDA_BIN_PATH`. Delete/recreate the CMake build directory after changing the CUDA compiler; CMake caches compiler discovery.

### Architecture selection problems

Use `CMAKE_CUDA_ARCHITECTURES="NATIVE"` for local builds on the current GPU. Use explicit numeric architectures only when targeting known devices, for example `80;86;90`. Use broad/all-architecture build only for packaging or deployment across unknown GPUs; it increases build time substantially.

## Build time, memory, and stale state

- Limit parallel jobs with `PARALLEL_LEVEL=N` when compiling exhausts RAM or contends with other workloads.
- Use `--ccache` for repeated native builds.
- Use `--configure-only` for a cheap dependency/flag check before committing to a long compile.
- Use `--nolibcumltest` or disable selected tests/examples/benchmarks when the change does not require them.
- Use `--singlegpu` to avoid multi-GPU components when distributed dependencies are unavailable.
- Use `clean` only when stale CMake state, ABI changes, or compiler/toolkit changes make incremental builds unreliable; it removes build artifacts.

## Python package source-build failures

The Python package build should use the same active prefix as the native build. A safe source-build pattern is:

```bash
./build.sh libcuml
./build.sh cuml
```

or, manually after native installation:

```bash
python -m pip install --no-build-isolation --no-deps \
  --config-settings rapidsai.disable-cuda=true \
  python/cuml
```

If package build fails:

- Confirm `libcuml` and native RAPIDS dependencies are installed in the active prefix.
- Confirm `python -c "import sys; print(sys.version)"` reports a supported Python version.
- Confirm Cython, scikit-build-core, and rapids-build-backend requirements are installed.
- Avoid allowing pip to resolve dependencies during source-build validation; it can pull incompatible CUDA/RAPIDS variants.
- If `SKBUILD_EXTRA_CMAKE_ARGS` is used, remember that space-separated arguments are converted to semicolon-separated CMake args by the build driver.

## Native test failures

### CTest/gtests

Before running tests, list what exists:

```bash
ctest --test-dir cpp/build -N
```

If no tests are listed, tests may not have been built, the wrong build directory is selected, or `BUILD_CUML_TESTS`/`BUILD_PRIMS_TESTS` was disabled. For focused failures:

```bash
ctest --test-dir cpp/build -R 'pattern' --output-on-failure
```

A CTest failure with CUDA initialization errors is usually environment/hardware, not an algorithm regression. Check GPU visibility and compute capability. Multi-GPU tests additionally require MG build flags, MPI, compatible communication dependencies, and appropriate hardware.

### Python pytest partitions

For single-GPU tests, use focused files or ignore Dask/NCCL partitions when optional distributed dependencies are absent:

```bash
python -m pytest cuml/tests --ignore=cuml/tests/dask --ignore=cuml/tests/test_nccl.py -q
```

For Dask tests, install the optional Dask group and verify cluster startup before treating estimator failures as cuML bugs:

```bash
python -m pytest cuml/tests/dask -q
python -m pytest cuml/tests/dask --run_ucx -q
```

If tests require optional packages such as XGBoost, install the pinned optional test dependencies instead of weakening the test expectation.

## C++ example failures

- Standalone examples must link against an installed `cuml::cuml` CMake package. Configure with the same prefix that received `libcuml`.
- Set `LINKER_LANGUAGE CUDA` for examples that link CUDA runtime symbols.
- KMeans and DBSCAN examples can run tiny built-in datasets without external data. Larger sample-file paths must match the documented flattened row order and row/feature counts.
- Symbolic-regression examples require generated train/test input files before execution and treat feature matrices as column-major in that workflow.
- Example success requires GPU runtime access even if compilation succeeded on a host without visible GPUs.

## Contribution review pitfalls that often masquerade as build/test failures

### Native/CUDA pitfalls

- Missing CUDA error checks after kernel launches or memory operations.
- Host-side integer overflow in allocation sizes, spans, offsets, or launch dimensions before values are widened.
- Wrong row-major/column-major assumption across C++ and Python boundaries.
- Device memory, stream, or event leaks on error paths.
- Default-stream reuse where independent or multi-GPU operations need stream isolation.
- Public header API changes without compatibility/deprecation handling.
- Tests that only assert "runs" and do not validate numerical correctness.

### Python/Cython pitfalls next to native code

- Scikit-learn parameter/default mismatch.
- Learned trailing-underscore attributes initialized in `__init__`.
- `fit` not resetting previous learned state.
- Missing `check_is_fitted` or dimension validation in predict/transform paths.
- Incorrect conversion or output preservation for cuDF, pandas, NumPy, and device arrays.
- Tests depending on external datasets instead of synthetic or bundled data.

## Benchmark warning

Benchmarks are not source-build health checks. Use them only when the user explicitly asks for performance work or when a change is expected to affect performance. Prefer tiny examples, CTest subsets, and focused pytest files for routine validation.
