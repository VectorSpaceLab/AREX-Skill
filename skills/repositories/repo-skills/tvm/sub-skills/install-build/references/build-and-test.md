# Build and Test Playbook

## Choose a packaging path

| Need | Path | Evidence of readiness |
|---|---|---|
| Use a supported prebuilt CPU package | Install the `apache-tvm` distribution and its required `apache-tvm-ffi` dependency | `import tvm`, `tvm.__version__`, and `tvm.support.libinfo()` succeed |
| Change TVM code or enable a custom backend | Build from a checkout with CMake/Ninja | The intended Python tree imports and loaded libraries come from the same build |
| Develop against several checkouts | Use source-style `PYTHONPATH`; avoid editable installs | `tvm.__file__` and loaded-library paths point to the selected checkout |

The package distribution is named `apache-tvm`, while the Python import is
`tvm`. Core metadata identifies `apache-tvm-ffi`, NumPy, `ml_dtypes`, and
`typing_extensions` as required dependencies. Optional groups include
`meta-schedule`, `rpc`, `popen-pool`, `torch`, `cuda`, and `all`; select only the
group required by the workflow.

## Source build checklist

1. Initialize submodules, including `3rdparty/tvm-ffi`.
2. Create a separate `build/` directory and select a generator such as Ninja.
3. Start from `cmake/config.cmake` or pass equivalent `-D` options.
4. Set `TVM_BUILD_PYTHON_MODULE=ON` for Python workflows.
5. Select `USE_LLVM` for LLVM CPU code generation. It may be a boolean or an
   `llvm-config` command, depending on the checkout's CMake conventions.
6. Enable `USE_RPC=ON` only when RPC is needed.
7. Enable CUDA/ROCm/Vulkan/Metal only after verifying the matching toolkit,
   headers, driver, and runtime device. A visible GPU alone is not proof that
   a build can compile or execute that backend.
8. Build and then set `PYTHONPATH` to the checkout's `python` directory during
   source-style development. Point `TVM_LIBRARY_PATH` at the build library
   directory only when the build does not use a standard discoverable location.

Example CPU/LLVM/RPC configure shape:

```bash
cmake -S . -B build -G Ninja \
  -DCMAKE_BUILD_TYPE=RelWithDebInfo \
  -DTVM_BUILD_PYTHON_MODULE=ON \
  -DUSE_LLVM=ON \
  -DUSE_RPC=ON \
  -DUSE_CUDA=OFF
cmake --build build --parallel
export PYTHONPATH="$PWD/python${PYTHONPATH:+:$PYTHONPATH}"
export TVM_LIBRARY_PATH="$PWD/build/lib"
python -m pip check
python <generated-skill>/sub-skills/install-build/scripts/check_tvm_install.py \
  --repo-root "$PWD" --tvm-library-path "$PWD/build/lib"
```

Use the repository's `CMakeLists.txt` and `cmake/config.cmake` as the authority
for option spelling and accepted values when a release differs. Reconfigure
from a clean build directory after changing core toolchain or backend options.

## Validation ladder

Run the smallest check that answers the question:

1. **Import:** `python -c 'import tvm; print(tvm.__version__)'`.
2. **Build identity:** print `tvm.support.libinfo()` and inspect loaded library
   paths with `scripts/check_tvm_install.py --json`.
3. **Dependency consistency:** `python -m pip check` in the selected environment.
4. **CPU smoke:** run one small all-platform minimal test, for example
   `python -m pytest tests/python/all-platform-minimal-test/test_minimal_target_codegen_llvm.py -xvs`.
5. **Runtime-library smoke:** run
   `test_validate_runtime_library.py` when the build produced the required
   artifacts.
6. **Focused changed-area tests:** select the smallest relevant test file; do
   not run the entire suite merely to prove an import.

Native tests are final verification evidence, not a substitute for configuring
the build correctly. Keep a result as blocked when the requested backend is not
present; do not turn a required GPU check into a CPU pass.

## Installation diagnostics

Use `scripts/check_tvm_install.py --help` for options. It supports an optional
checkout root and library directory, emits text or JSON, and can check expected
backend names. It never edits files, starts RPC services, downloads models, or
runs a tuning loop.
