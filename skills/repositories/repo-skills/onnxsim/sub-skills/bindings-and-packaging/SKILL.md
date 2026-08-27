---
name: bindings-and-packaging
description: "Build, install, packaging, C/Rust/WASM/npm, and release-version
  workflows for ONNX Simplifier."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# bindings-and-packaging

Use this sub-skill when the task is about installing, building, linking,
packaging, releasing, or diagnosing ONNX Simplifier bindings. It covers Python
wheels/editable builds, direct CMake builds, the C ABI, Rust crates, WebAssembly,
the web demo/npm package, version synchronization, and maintainer test selection.

## Route first

- If the task asks how to call `onnxsim.simplify`, pass CLI flags, set input
  shapes, choose providers for simplification checks, or simplify an ONNX model,
  route to `../python-simplification/SKILL.md`.
- If the task asks about custom rewrite semantics, FunctionProto rule authoring,
  `ModelInfo`, MACs/FLOPs/memory metrics, graph diff, metadata, or profiling,
  route to [`../advanced-graph-control/SKILL.md`](../advanced-graph-control/SKILL.md).
- Stay here for package installation, native build options, C/Rust/WASM/npm
  binding mechanics, release/version checks, and build/test triage.

## Non-negotiable build fact

The Python wheel/editable/source build driven by `setup.py` passes
`-DONNXSIM_BUILTIN_ORT=OFF`. It builds the Python extension
`onnxsim_cpp2py_export`, ONNX/onnx-optimizer/protobuf pieces needed by that
extension, and compiles with `NO_BUILTIN_ORT`; it does **not** compile the
vendored ONNX Runtime C++ source. `onnxruntime` is only an optional Python
runtime dependency for constant folding and correctness checks. If a build is
compiling ONNX Runtime C++, it is on the standalone C++/WASM/C API/Rust native
library path where `ONNXSIM_BUILTIN_ORT=ON`, not the Python wheel path.

## Primary references

- Build and binding recipes: [`references/build-and-bindings.md`](references/build-and-bindings.md)
- WASM, ORT-web, npm, web demo, WebNN, and DLPack boundaries:
  [`references/wasm-and-web.md`](references/wasm-and-web.md)
- Failure-mode triage: [`references/troubleshooting.md`](references/troubleshooting.md)
- Safe version checker: [`scripts/check_version_sync.py`](scripts/check_version_sync.py)

## Choose the workflow

1. **Released Python package**: install the wheel when the user only needs the
   CLI/Python package.

   ```bash
   python -m pip install -U onnxsim
   python -m pip install -U "onnxsim[onnxruntime]"  # optional faster/checking runtime
   python -c "import onnxsim; print(onnxsim.__version__)"
   onnxsim --help
   onnxsim --list-default-optimizers
   ```

2. **Local Python editable/source build**: use when changing Python/C++ extension
   code or building from an sdist/checkout. Initialize submodules for a checkout,
   install build tools, and keep the build scoped to the Python extension.

   ```bash
   git submodule update --init --recursive
   python -m pip install -U pip setuptools wheel cmake ninja nanobind
   CMAKE_GENERATOR=Ninja python -m pip install -e . -v
   ```

   Optional knobs include `MAX_JOBS=<n>`, `CMAKE_ARGS="..."`, `DEBUG=1`,
   `COVERAGE=1`, `ONNX_OPT_USE_SYSTEM_PROTOBUF=1`, `ONNXSIM_RELEASE=<version>`,
   and platform-specific compiler variables. Do not add `ONNXSIM_BUILTIN_ORT=ON`
   for a normal Python wheel investigation.

3. **Standalone C++ executable or C API**: use direct CMake. The C API requires
   built-in ORT because it provides the native constant-folding executor.

   ```bash
   git submodule update --init --recursive
   cmake -S . -B build -DONNXSIM_C_API=ON -DONNXSIM_BUILTIN_ORT=ON
   cmake --build build --target onnxsim_c
   ```

   To skip a full ONNX Runtime source compile on supported native platforms, add
   `-DONNXSIM_PREBUILT_ORT=ON` and optionally set `ONNXSIM_ORT_VERSION`,
   `ONNXSIM_ORT_HOME`, or `ONNXSIM_ORT_URL`.

4. **Rust crates**: build inside `rust/` for in-tree development, choose one of
   the native-library modes for downstream consumers, and use check-only mode for
   docs or type-checking.

   ```bash
   cd rust
   ONNXSIM_NO_BUILD=1 cargo check --workspace
   ONNXSIM_PREBUILT_ORT=1 cargo build --release --workspace
   ONNXSIM_LIB_DIR=/path/to/libs cargo build --release
   ```

   `ONNXSIM_LIB_DIR` links a prebuilt `onnxsim_c`; `ONNXSIM_SOURCE_DIR` points a
   published crate at a checkout with submodules; `ONNXSIM_NO_BUILD=1` skips the
   native build and cannot produce a runnable binary.

5. **WASM/web/npm**: only run these long builds when the user explicitly needs a
   WASM module, web demo, or npm package. The npm package uses the ORT-web
   variant.

   ```bash
   ./build_wasm.sh                 # default WASM, compiles built-in ORT
   ORT_WEB=ON ./build_wasm.sh      # no ORT C++ compile; delegates to onnxruntime-web
   ./scripts/stage_npm_package.sh build-wasm-node-OFF-ortweb
   (cd npm/onnxsim && npm install && npm test && npm pack)
   ```

## Safe local checks for this sub-skill

Do not launch long native, Rust, npm, or WASM builds just to inspect a task. Start
with deterministic checks:

```bash
python scripts/check_version_sync.py --help
python scripts/check_version_sync.py --repo-root /path/to/onnxsim-checkout
```

The checker compares the root `VERSION`, Rust workspace/crate dependency
versions, and npm package version when present. It never writes files.

## Maintainer test selection

- **Version/release metadata**: run the bundled checker or the repository's
  read-only version-sync check before a release. Mutating bump scripts are
  release-only; do not run them for diagnosis unless the user asked to bump.
- **Python wheel path**: wheel CI builds Linux/macOS wheels and Windows wheels by
  cross-compile, then runs `pytest`, `onnxsim -h`, and
  `onnxsim --list-default-optimizers`. PRs intentionally use a reduced Python
  matrix; release/push runs are broader.
- **Rust path**: `ONNXSIM_NO_BUILD=1 cargo fmt/clippy/check` is fast; native
  `cargo build/test` is long; the standalone-package test validates published
  crate behavior outside a source checkout.
- **WASM/npm path**: use the ORT-web build plus `npm test && npm pack`. Hosted
  demo previews and Netron embedding are heavier than npm package validation.
- **Optional integration/regression paths**: TVM, Halide, ModelOpt, QNN,
  model-regression, YOLO, RF-DETR, VOICEVOX, X2Paddle, coverage, sanitizer, and
  big-endian jobs are targeted or scheduled. Do not treat their dependencies as
  required for the minimum build/install environment.

## Quick troubleshooting route

- Python build unexpectedly compiles ONNX Runtime: see
  [`references/troubleshooting.md`](references/troubleshooting.md#python-build-is-compiling-onnx-runtime).
- CMake/submodule/nanobind/protobuf errors: see
  [`references/troubleshooting.md`](references/troubleshooting.md#cmake-submodule-nanobind-and-protobuf-errors).
- C API or Rust link failures: see
  [`references/troubleshooting.md`](references/troubleshooting.md#c-api-and-rust-linking-failures).
- WASM, ORT-web, npm staging, or WebNN issues: see
  [`references/troubleshooting.md`](references/troubleshooting.md#wasm-ort-web-npm-and-webnn-issues).
- Optional provider dependencies and skipped heavy tests: see
  [`references/troubleshooting.md`](references/troubleshooting.md#optional-provider-and-regression-dependencies).

## Handoff checklist

- State which build path is in scope: Python package, standalone CMake, C API,
  Rust, WASM/web, npm, or release/version work.
- Preserve the Python-wheel built-in-ORT caveat exactly.
- Use concrete commands with prerequisites and expected validation outputs.
- Keep original long scripts as reference knowledge; use only the bundled safe
  checker as a runtime helper.
- When a fix needs API behavior rather than binding mechanics, route to the
  sibling sub-skill instead of duplicating semantics here.
