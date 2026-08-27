# Bindings and packaging troubleshooting

Use this reference to map build/package symptoms to the correct workflow and
smallest safe fix. Do not install heavyweight provider stacks or run long build
scripts unless the user explicitly asks for that path.

## Python build is compiling ONNX Runtime

Symptom:

- A user expected `pip install .`, `pip install -e .`, or a wheel build, but logs
  show a long ONNX Runtime C++ compile under `third_party/onnxruntime-*`.

Interpretation:

- This should not happen on the `setup.py` Python wheel/editable path because it
  passes `-DONNXSIM_BUILTIN_ORT=OFF` and compiles with `NO_BUILTIN_ORT`.
- The user is probably running direct CMake, a C API build, a Rust native-library
  source build, or the default WASM build.

Fix:

1. For Python package work, use:

   ```bash
   python -m pip install -U pip setuptools wheel cmake ninja nanobind
   CMAKE_GENERATOR=Ninja python -m pip install -e . -v
   ```

2. Confirm the configure line includes `-DONNXSIM_PYTHON=ON` and
   `-DONNXSIM_BUILTIN_ORT=OFF`.
3. Install optional Python runtime support separately if needed:

   ```bash
   python -m pip install "onnxsim[onnxruntime]"
   ```

4. Do not try to fix a Python wheel by compiling vendored ORT C++.

## CMake, submodule, nanobind, and protobuf errors

### Missing submodules or nested submodules

Symptoms include missing `third_party/onnx`, missing `third_party/onnx-optimizer`,
missing optimizer targets, or CMake errors while adding ONNX/onnx-optimizer.

Fix for a source checkout:

```bash
git submodule update --init --recursive
```

The top-level checkout has submodules for ONNX and onnx-optimizer. Recursive
initialization is safest because onnx-optimizer may carry its own nested inputs,
even when the top-level build prefers the repository's top-level ONNX target.

### Missing nanobind

Symptoms include CMake failing at `nanobind_add_module` or ONNX's CMake logic
reporting that `nanobind` cannot be found, especially in offline or fully
disconnected builds.

Fixes:

```bash
python -m pip install nanobind
python -m nanobind --cmake_dir
```

If the build is offline, pass the resulting CMake directory through
`nanobind_DIR` or `CMAKE_PREFIX_PATH`, or pre-provide nanobind through the build
environment. If online and not fully disconnected, ONNX may fetch nanobind via
CMake FetchContent.

### Protobuf and ONNX CMake mismatches

Symptoms:

- Generated protobuf headers fail to compile.
- Messages mention `PROTOBUF_NAMESPACE_OPEN` or generated code from an older
  `protoc`.
- CMake cannot find or uses an incompatible system protobuf.

Fixes:

- For ordinary Python/CMake native builds, prefer the bundled/custom protobuf
  path unless the user explicitly needs `ONNX_OPT_USE_SYSTEM_PROTOBUF=1` and has
  a compatible system protobuf.
- For ORT-web WASM, install a host `protoc` matching ONNX's pinned protobuf. In
  this snapshot that is protoc `31.1` for protobuf `31.1`.
- If using system protobuf, keep C++ library, headers, and `protoc` versions in
  sync.

### macOS and C++ standard errors

ONNX uses C++ features that require macOS deployment target `13.3` with current
libc++. Ensure the build environment does not force an older deployment target.
For universal builds, set `ARCHFLAGS` and let `setup.py` forward architectures to
CMake.

## C API and Rust linking failures

### `ONNXSIM_C_API requires ONNXSIM_BUILTIN_ORT=ON`

Cause: The C ABI target `onnxsim_c` needs the native constant-folding executor.

Fix:

```bash
cmake -S . -B build-capi -DONNXSIM_C_API=ON -DONNXSIM_BUILTIN_ORT=ON
cmake --build build-capi --target onnxsim_c
```

To reduce build time, add `-DONNXSIM_PREBUILT_ORT=ON` on supported native
platforms.

### Prebuilt ORT errors

Symptoms and fixes:

| Symptom | Fix |
| --- | --- |
| `ONNXSIM_PREBUILT_ORT requires ONNXSIM_BUILTIN_ORT=ON` | Enable built-in ORT for the standalone/C API/Rust build. |
| `ONNXSIM_PREBUILT_ORT is not supported for Emscripten` | Use default WASM with source ORT or ORT-web WASM with no ORT. |
| Header `onnxruntime_cxx_api.h` not found | Point `ONNXSIM_ORT_HOME` at an extracted release containing `include/`. |
| Library not found under `lib/` or `lib64/` | Use a complete release archive or set `ONNXSIM_ORT_URL`/`ONNXSIM_ORT_HOME` to the correct asset. |
| Runtime loader cannot find ONNX Runtime shared library | Add the ORT/onnxsim library directories to the platform loader path or package/copy them with the binary. |

### Rust build mode confusion

Symptoms:

- Published crate tries to build from source but no C++ checkout exists.
- `cargo check` starts a native build.
- Runnable binary fails to link `onnxsim_c`.

Choose exactly one mode:

```bash
ONNXSIM_NO_BUILD=1 cargo check                 # type-check/docs only
ONNXSIM_LIB_DIR=/path/to/libs cargo build      # link an existing onnxsim_c
ONNXSIM_SOURCE_DIR=/path/to/checkout cargo build  # build from a checkout
ONNXSIM_PREBUILT_ORT=1 cargo build             # source mode, skip ORT compile
```

Notes:

- `ONNXSIM_NO_BUILD=1` cannot produce a runnable binary.
- `ONNXSIM_LIB_DIR` is path-list syntax: colon-separated on Unix-like systems and
  semicolon-separated by platform path rules where applicable.
- If the native library was built separately, include every directory holding
  `onnxsim_c` and its transitive shared libraries.
- `ONNXSIM_SKIP_ORT_DOWNLOAD=1` makes source mode fail if the ORT source tree is
  absent; unset it to allow download, or use `ONNXSIM_PREBUILT_ORT=1`.

### C API memory/FFI crashes

Check these first:

- Free successful `out_data` only with `onnxsim_free_buffer`.
- Free error strings and optimizer lists only with `onnxsim_free_string`.
- Do not retain borrowed DLPack input pointers after executor callback return.
- Return owned output `DLManagedTensor*` with valid deleters.
- Return one tensor per sub-model graph output, in positional order.
- Keep tensors CPU, contiguous, and supported numeric/bool dtypes.

## WASM, ORT-web, npm, and WebNN issues

### Missing `emcmake` or Emscripten tools

`build_wasm.sh` starts by checking `emcmake`. Activate an Emscripten SDK before
running WASM builds. These builds are long; do not use them as a first-line
package inspection check.

### ORT-web build still compiles ONNX Runtime

Expected ORT-web command:

```bash
ORT_WEB=ON ./build_wasm.sh
```

The build directory should end in `-ortweb`, CMake should set
`ONNXSIM_WASM_ORT_WEB=ON`, and ONNX Runtime C++ should not be downloaded or
compiled. If ORT source is compiling, the environment variable was not set or a
different build path is being used.

### Protobuf/protoc failure in ORT-web WASM

Cause: ORT-web removes the ONNX Runtime wasm protobuf provider. ONNX builds its
own bundled protobuf for the wasm target, while host `protoc` generates code.
The host generator must match the bundled protobuf version.

Fix:

1. Install a matching `protoc` on `PATH` before running the build. In this
   snapshot, use protoc `31.1`.
2. Avoid older distro `protobuf-compiler` packages for this build.
3. Clean or reconfigure the WASM build directory after changing `protoc`.

### Asyncify or Promise-related failures

In ORT-web mode, C++ simplification synchronously calls an asynchronous
onnxruntime-web session through Asyncify. The exported simplification function
becomes promise-like when `onnxsim_needs_ort_web()` is true.

Fix for JS callers/workers: await the simplification call after registering
`Module.onnxsimOrtWebRun`.

### npm staging or package files missing

Symptoms:

- `onnxsim.wasm is missing -- run scripts/build_npm_package.sh first`.
- `onnxsim.cjs` or `ort_executor.mjs` missing from npm package.
- Node treats generated `onnxsim.js` as ESM and fails on `module.exports`.

Fix:

```bash
ORT_WEB=ON ./build_wasm.sh
./scripts/stage_npm_package.sh build-wasm-node-OFF-ortweb
(cd npm/onnxsim && npm install && npm test && npm pack)
```

The staging step renames Emscripten's CommonJS `onnxsim.js` to `onnxsim.cjs` and
copies `onnxsim.wasm` plus `ort_executor.mjs` into the package.

### npm publish smoke fails because version already exists

Use `npm pack` for routine packaging validation. `npm publish --dry-run` can
contact the registry and fail if the current package version is already live,
which is normal between releases.

### WebNN unavailable or falls back to WASM

WebNN is experimental and browser/platform-dependent. The web demo intentionally
adds WASM fallback after WebNN/WebGPU provider choices. Report the actual
provider used and surface onnxruntime-web diagnostics; do not treat WebNN
fallback as a package build failure.

## Version-sync failures

Run the bundled safe checker:

```bash
python ../scripts/check_version_sync.py --repo-root /path/to/onnxsim-checkout
```

Mismatches can involve:

- root `VERSION`, used as Python fallback and baked into WASM;
- Rust workspace version in `rust/Cargo.toml`;
- Rust `onnxsim` dependency on `onnxsim-sys` in `rust/onnxsim/Cargo.toml`;
- npm `npm/onnxsim/package.json` version when present.

Do not run mutating bump scripts unless the task is a release/version bump. For
release work, update all binding manifests together and rerun the checker.

## Optional provider and regression dependencies

The minimum package/build skill does not require these optional stacks:

- `onnxruntime-gpu` / CUDA providers;
- Qualcomm `onnxruntime-qnn`;
- NVIDIA ModelOpt;
- TVM or Halide;
- Torch/torchvision/timm/ultralytics/rfdetr/VOICEVOX/X2Paddle regression stacks;
- browser, WebGPU, WebNN, Netron, Cloudflare, or Pages deployment credentials.

When a test involving one of these stacks fails, classify it as an optional
integration/regression path unless the user explicitly selected that backend.
Use the CPU/base Python package path as the default substitute for package
installation and build diagnosis.

## Long-script policy

The original repository contains useful long or mutating scripts for release,
WASM/npm, and Rust package validation. This sub-skill does not bundle or
recommend them as generic runtime helpers. Use them only when the user asks for
that exact workflow, and prefer the distilled commands and safe checker here for
triage.
