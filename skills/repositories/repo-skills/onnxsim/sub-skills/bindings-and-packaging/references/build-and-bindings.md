# Build and bindings reference

This reference distills the install/build/package facts needed by future agents.
It is self-contained: do not reopen the source repository just to recover option
names, commands, or binding contracts.

## Package identity

- Python distribution and import package: `onnxsim`.
- Console script: `onnxsim`.
- Supported Python: `>=3.10`.
- Required Python runtime dependencies: `onnx`, `rich`.
- Optional extras:
  - `onnxsim[onnxruntime]` installs `onnxruntime >= 1.6.0`. It is preferred for
    constant folding and correctness checking, but the package can fall back to
    ONNX's reference evaluator when absent.
  - `onnxsim[symbolic]` installs `sympy` for symbolic MACs/FLOPs formulas.
- The Python build backend is setuptools with a custom CMake build step.
- Version source:
  - If a git tag is available, `setup.py` derives the version from
    `git describe --tags --abbrev=0`, removing a leading `v`.
  - `ONNXSIM_RELEASE=<version>` overrides git-derived version during release
    builds.
  - Without tags, the root `VERSION` file is the fallback. The WASM build also
    bakes this file into the module's version panel/report.

## Python wheel/editable/source build

### Critical caveat: no vendored ONNX Runtime C++ build

`setup.py` always configures the Python extension with:

```text
-DONNXSIM_PYTHON=ON
-DONNXSIM_BUILTIN_ORT=OFF
-DONNX_BUILD_PYTHON=ON
-DONNX_INSTALL=OFF
-DONNX_USE_LITE_PROTO=OFF
```

Therefore `pip install .`, `pip install -e .`, and wheel builds do **not** build
or link the vendored ONNX Runtime C++ source. The extension compiles with
`NO_BUILTIN_ORT`, which excludes `Ort::` C++ paths from the Python extension.
At runtime, constant folding/checking calls the pip-installed `onnxruntime` when
available and otherwise uses ONNX's reference evaluator.

If a command is compiling ONNX Runtime C++, it is not the normal Python wheel
path. It is likely a direct CMake build, a C API build, a Rust native-library
build, or the default WASM build.

### Common commands

Install the released package:

```bash
python -m pip install -U onnxsim
python -m pip install -U "onnxsim[onnxruntime]"  # optional runtime dependency
python -c "import onnxsim; print(onnxsim.__version__)"
onnxsim --help
onnxsim --list-default-optimizers
```

Build an editable checkout for development:

```bash
git submodule update --init --recursive
python -m pip install -U pip setuptools wheel cmake ninja nanobind
CMAKE_GENERATOR=Ninja python -m pip install -e . -v
python -c "import onnxsim, onnxsim.onnxsim_cpp2py_export as m; print(m.__file__)"
onnxsim --help
```

Build from an sdist or checkout without editable mode:

```bash
python -m pip install -U pip setuptools wheel cmake ninja nanobind
python -m pip install . -v
```

Recommended local validation after a Python build:

```bash
python -c "import onnxsim; print('onnxsim', onnxsim.__version__)"
python -c "import onnxsim.onnxsim_cpp2py_export as m; print(sorted(x for x in dir(m) if not x.startswith('_'))[:8])"
onnxsim --help
onnxsim --list-default-optimizers
```

### Python build knobs

- `MAX_JOBS=<n>` or `python setup.py build -j<n>` controls build parallelism.
- `CMAKE_ARGS="..."` appends extra CMake arguments; `setup.py` removes this
  variable after consuming it to avoid leaking it into downstream scripts.
- `CMAKE_GENERATOR=Ninja` is the usual fast generator.
- `DEBUG=1` switches to a debug build; `COVERAGE=1` also enables
  `-DONNXSIM_COVERAGE=ON` and turns optimization off for coverage.
- `USE_MSVC_STATIC_RUNTIME=1` affects Windows MSVC runtime selection.
- `ONNX_ML=0`, `ONNX_VERIFY_PROTO3=1`, `ONNX_NAMESPACE=<name>`,
  `ONNX_BUILD_TESTS=1`, and `ONNX_OPT_USE_SYSTEM_PROTOBUF=1` are forwarded into
  the ONNX/onnx-optimizer build where applicable.
- On macOS, `ARCHFLAGS="-arch arm64 -arch x86_64"` is respected for cross/universal
  builds; the deployment target is `13.3` to match ONNX's C++ requirements.
- Python 3.12+ regular wheels use a `cp312` stable ABI when possible. Free-
  threaded Python builds are not stable-ABI builds but mark the nanobind module
  as GIL-not-used.

## Direct CMake options

Top-level CMake defaults target standalone native/WASM development, not Python
wheels. Important options:

| Option | Default | Meaning |
| --- | ---: | --- |
| `ONNXSIM_PYTHON` | `OFF` | Build the Python extension target with nanobind. `setup.py` sets this `ON`. |
| `ONNXSIM_BUILTIN_ORT` | `ON` | Build/link ONNX Runtime into onnxsim for standalone native/WASM/C API/Rust paths. `setup.py` sets this `OFF`. |
| `ONNXSIM_PREBUILT_ORT` | `OFF` | With built-in ORT enabled, link an official prebuilt ONNX Runtime release instead of compiling ORT from source. Not supported for Emscripten. |
| `ONNXSIM_WASM_NODE` | `OFF` | Emscripten Node/NODERAWFS-oriented build switch. |
| `ONNXSIM_C_API` | `OFF` | Build the shared C ABI library `onnxsim_c`; requires `ONNXSIM_BUILTIN_ORT=ON`. |
| `ONNXSIM_COVERAGE` | `OFF` | Instrument onnxsim C++ targets with gcov/llvm-cov coverage flags; GCC/Clang only. |
| `ONNXSIM_TESTS` | `OFF` | Build dependency-light C++ unit tests such as `sym_expr_test`, `model_metrics_test`, `sym_value_eval_test`, `sym_shape_infer_test`, and `dlpack_dtype_test`. |
| `ONNXSIM_WASM_ORT_WEB` | `OFF` | Emscripten-only ORT-web variant: no ONNX Runtime is linked; folding delegates to onnxruntime-web. Forces `ONNXSIM_BUILTIN_ORT=OFF`. |

Option constraints:

- `ONNXSIM_PREBUILT_ORT=ON` requires `ONNXSIM_BUILTIN_ORT=ON`.
- `ONNXSIM_PREBUILT_ORT=ON` is not supported for Emscripten.
- `ONNXSIM_WASM_ORT_WEB=ON` applies only to Emscripten/WebAssembly.
- Emscripten without built-in ORT is only valid in the ORT-web variant.
- `ONNXSIM_C_API=ON` requires built-in ORT.
- `ONNXSIM_PYTHON` and Emscripten are not a meaningful combination.

## Prebuilt ONNX Runtime native path

For standalone native CMake/C API/Rust builds where built-in ORT is needed but a
full ORT source build is too expensive, enable prebuilt ORT:

```bash
cmake -S . -B build \
  -DONNXSIM_BUILTIN_ORT=ON \
  -DONNXSIM_PREBUILT_ORT=ON \
  -DONNXSIM_C_API=ON
cmake --build build --target onnxsim_c
```

Inputs:

- `ONNXSIM_ORT_VERSION` defaults to `1.28.0`.
- `ONNXSIM_ORT_HOME` points to an already-extracted ONNX Runtime release
  containing `include/` and `lib/`; when set, no download is attempted.
- `ONNXSIM_ORT_URL` overrides the auto-detected archive URL.

The prebuilt path creates an imported `onnxruntime` target and exposes
`ONNXRUNTIME_INCLUDE_DIR` plus the library directory. It locates release tarball
layouts directly instead of using ONNX Runtime's CMake package files.

## Standalone executable and C++ tests

Build the standalone executable:

```bash
git submodule update --init --recursive
cmake -S . -B build -DONNXSIM_BUILTIN_ORT=ON
cmake --build build --target onnxsim
```

Build dependency-light C++ tests:

```bash
cmake -S . -B build-tests -DONNXSIM_TESTS=ON -DONNXSIM_BUILTIN_ORT=OFF
cmake --build build-tests
ctest --test-dir build-tests --output-on-failure
```

The `ONNXSIM_TESTS` targets are designed to cover pure units without requiring a
full ONNX Runtime configuration, and are useful on cross/big-endian builds.

## C API

Build the shared C ABI library:

```bash
git submodule update --init --recursive
cmake -S . -B build-capi -DONNXSIM_C_API=ON -DONNXSIM_BUILTIN_ORT=ON
cmake --build build-capi --target onnxsim_c
```

Optional faster native dependency path:

```bash
cmake -S . -B build-capi \
  -DONNXSIM_C_API=ON \
  -DONNXSIM_BUILTIN_ORT=ON \
  -DONNXSIM_PREBUILT_ORT=ON \
  -DONNXSIM_ORT_VERSION=1.28.0
cmake --build build-capi --target onnxsim_c
```

The C ABI exchanges models as serialized ONNX `ModelProto` bytes and exports:

- `OnnxsimStatus` with `ONNXSIM_OK` and `ONNXSIM_ERROR`.
- `OnnxsimRewriteFn` and `OnnxsimRewriteFreeFn` for custom graph rewriter
  callbacks. A rewriter returns `>0` for changed, `0` for no change, and `<0`
  for failure.
- `OnnxsimExecuteFn` and `OnnxsimExecuteFreeFn` for custom constant-folding
  executors at the DLPack boundary.
- `onnxsim_simplify`, `onnxsim_simplify_with_executor`,
  `onnxsim_simplify_with_rules`, and `onnxsim_simplify_path`.
- `onnxsim_list_optimizers`, `onnxsim_model_info_diff`, and
  `onnxsim_graph_diff`.
- `onnxsim_free_buffer` and `onnxsim_free_string`; callers must free returned
  model buffers and strings with these functions.

C API parameter semantics:

- `skip_optimizers_is_null != 0` means skip **all** optimizer passes.
- `skip_optimizers_is_null == 0` means run all passes except the supplied names;
  an empty list runs all passes.
- `constant_folding` and `shape_inference` are integer booleans.
- `tensor_size_threshold` is a byte limit for folded tensors kept as
  initializers.
- `target_opset_version > 0` converts the default ONNX-domain opset before
  simplifying; `<= 0` leaves it unchanged.
- On success, output model bytes are newly allocated and owned by the caller.
- On failure, `out_error` is a newly allocated NUL-terminated message.

Custom executor contract:

- Inputs are borrowed `DLManagedTensor*` for the duration of the callback; do not
  free or retain them.
- Outputs are owned `DLManagedTensor*`; onnxsim releases each tensor via the
  tensor's DLPack deleter and then calls the optional array-container free
  callback.
- Tensors must be CPU, contiguous, little-endian, and one of the supported
  numeric/bool dtypes.
- `model_data` is a serialized sub-model; inputs and outputs are positional in
  graph input/output order.

FunctionProto rule semantics are shared with Python and Rust. For rule-authoring
details, route to the advanced graph-control sub-skill.

## Rust bindings

Crate layout:

| Crate | Role |
| --- | --- |
| `onnxsim` | Safe Rust API. Use this from application code. |
| `onnxsim-sys` | Raw FFI declarations and `build.rs` for linking/building `onnxsim_c`. |

Public safe API includes `simplify`, `simplify_with`, `simplify_path`,
`simplify_path_with`, `simplify_with_rewriter`, `simplify_path_with_rewriter`,
`simplify_with_executor`, `list_optimizers`, `model_info_diff`, and `graph_diff`.
`Options::new()` supports `constant_folding(bool)`, `shape_inference(bool)`,
`tensor_size_threshold(bytes)`, `target_opset_version(i32)`,
`without_optimizers()`, `skip_optimizers(...)`, `skip_optimizer(...)`, and
`function_rewrite_rule(pattern_bytes, replacement_bytes)`.

Use examples:

```rust
let model = std::fs::read("model.onnx")?;
let simplified = onnxsim::simplify(&model)?;
std::fs::write("model.opt.onnx", &simplified)?;

let opts = onnxsim::Options::new()
    .shape_inference(false)
    .skip_optimizer("eliminate_nop_transpose")
    .tensor_size_threshold(512 * 1024 * 1024);
let simplified = onnxsim::simplify_with(&model, &opts)?;

for pass in onnxsim::list_optimizers() {
    println!("{pass}");
}
```

Native-library build modes in `onnxsim-sys`:

| Mode | Environment | Use when |
| --- | --- | --- |
| Skip native build | `ONNXSIM_NO_BUILD=1` or docs.rs | `cargo check`, docs, clippy/type-check only; not runnable. |
| Prebuilt library | `ONNXSIM_LIB_DIR=/dir[:/dir2...]` | You already built `onnxsim_c` and dependencies. |
| Source build | default in the repository, or `ONNXSIM_SOURCE_DIR=/checkout` | Need a runnable crate and want CMake to build `onnxsim_c`. |

Additional source-build variables:

- `ONNXSIM_SKIP_ORT_DOWNLOAD=1`: fail if ONNX Runtime source is not already
  present instead of downloading it.
- `ONNXSIM_PREBUILT_ORT=1`: link a prebuilt ONNX Runtime release instead of
  compiling ORT from source.
- `ONNXSIM_ORT_VERSION`, `ONNXSIM_ORT_HOME`, `ONNXSIM_ORT_URL`: forwarded to the
  prebuilt ORT CMake path.

Typical Rust commands:

```bash
cd rust
ONNXSIM_NO_BUILD=1 cargo check --workspace
ONNXSIM_NO_BUILD=1 cargo clippy --workspace --all-targets -- -D warnings
ONNXSIM_PREBUILT_ORT=1 cargo build --release --workspace
ONNXSIM_PREBUILT_ORT=1 cargo test --release --workspace
cargo test --release -- --ignored list_optimizers_is_non_empty
```

If consuming the published crate without the source tree, choose
`ONNXSIM_LIB_DIR`, `ONNXSIM_SOURCE_DIR`, or `ONNXSIM_NO_BUILD`. A build with no
mode selected should fail early with a message naming those choices.

Package/release notes:

- The published crates may require `cargo publish --no-verify` because normal
  Cargo verification unpacks the crate away from the C++ source tree.
- Publish `onnxsim-sys` first, wait for the index to see it, then publish
  `onnxsim`.
- Release CI bumps binding versions to the release tag before publishing.

## Version and release scripts

Use the bundled safe checker for read-only verification from any checkout:

```bash
python ../scripts/check_version_sync.py --repo-root /path/to/onnxsim-checkout
```

It checks the root `VERSION`, Rust workspace version, Rust `onnxsim` dependency
on `onnxsim-sys`, and npm package version when present.

Repository release scripts are intentionally not bundled as runtime helpers:

- `check_version_sync.sh`: original read-only shell checker. Adapted here as the
  safe Python checker.
- `bump_binding_versions.sh`: mutates npm, Rust, and `VERSION`; release-only.
- `build_npm_package.sh`: long ORT-web WASM build plus staging; reference-only.
- `stage_npm_package.sh`: stages built WASM artifacts into the npm package;
  reference-only because it copies build outputs.
- `test_rust_package_standalone.sh`: long package validation; reference-only for
  maintainer planning.

## Maintainer test selection matrix

| Change area | Fast local check | CI/long check when needed |
| --- | --- | --- |
| Version metadata | bundled `check_version_sync.py --repo-root .` | release version-sync bump/check jobs |
| Python packaging | import compiled extension, `onnxsim --help`, `--list-default-optimizers` | wheel matrix, sdist install/test, ABI3 audit |
| CMake/C API | configure/build targeted `onnxsim_c` only | sanitizer, coverage, platform wheels |
| Rust | `ONNXSIM_NO_BUILD=1 cargo check/clippy` | native build/test, standalone package test, coverage |
| WASM/npm | inspect commands, ensure version/package metadata | `ORT_WEB=ON` build, stage, `npm test && npm pack` |
| Web demo | npm/unit tests | hosted Pages/Cloudflare preview and convertmodel inference tests |
| Optional providers/regressions | document as optional | TVM, Halide, QNN, ModelOpt, model-regression, YOLO, RF-DETR, VOICEVOX, X2Paddle |
| Portability/diagnostics | targeted C++ tests | big-endian/qemu, sanitizer, combined coverage |
