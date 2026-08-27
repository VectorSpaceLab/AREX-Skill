# WASM, ORT-web, npm, and web demo reference

This reference covers the WebAssembly build variants, the ORT-web constant
folding boundary, npm packaging, and web-demo validation. Use it for build and
package mechanics only; model simplification semantics belong to the sibling
Python/API sub-skill, and rewrite/metrics semantics belong to the advanced
sub-skill.

## Build variants

### Default WebAssembly build

```bash
./build_wasm.sh
```

Properties:

- Requires `emcmake` from an active Emscripten SDK environment.
- Uses a host `protoc` found on `PATH`; if none is found, it builds one through
  ONNX's helper scripts.
- Downloads ONNX Runtime source version `1.28.0` into `third_party/` if missing.
- Configures CMake for Emscripten and builds the `onnxsim_bin` target.
- Keeps `ONNXSIM_BUILTIN_ORT=ON`, so ONNX Runtime is compiled into the WASM
  module.
- Default output directory is `build-wasm-node-OFF/`; passing a first argument
  changes the `ONNXSIM_WASM_NODE`/NODERAWFS-oriented suffix.
- Outputs `onnxsim.js` and `onnxsim.wasm`.

### ORT-web WebAssembly build

```bash
ORT_WEB=ON ./build_wasm.sh
```

Properties:

- Configures `-DONNXSIM_WASM_ORT_WEB=ON`.
- CMake forces `ONNXSIM_BUILTIN_ORT=OFF` and compiles with `NO_BUILTIN_ORT`.
- Does not download, compile, or link ONNX Runtime C++.
- Links ONNX/onnx-optimizer directly because ORT no longer provides ONNX
  transitively.
- Builds `scripts/convertmodel/js_model_executor.cpp` and defines
  `ONNXSIM_WASM_ORT_WEB` for the executable.
- Adds Asyncify link flags because the synchronous C++ simplification stack must
  await asynchronous onnxruntime-web promises.
- Output directory is `build-wasm-node-OFF-ortweb/`.
- This is the variant staged into the npm package and used by the hosted demo.

### Emscripten CMake constraints

- `ONNXSIM_PREBUILT_ORT=ON` is unsupported for Emscripten.
- Emscripten without built-in ORT is only valid when `ONNXSIM_WASM_ORT_WEB=ON`.
- `ONNXSIM_WASM_ORT_WEB=ON` is Emscripten-only.
- `ONNXSIM_PYTHON=ON` is not a valid Emscripten build path.
- The linker enables memory growth and raises the wasm32 memory cap to 4 GiB;
  larger models still require a different architecture such as wasm64.

## Host protoc and protobuf

The ORT-web path removes ONNX Runtime's wasm protobuf runtime, so CMake sets
`ONNX_BUILD_CUSTOM_PROTOBUF=ON` and lets ONNX build its bundled protobuf for the
wasm target. `build_wasm.sh` passes `ONNX_CUSTOM_PROTOC_EXECUTABLE=$(which
protoc)` for code generation.

The host `protoc` must match ONNX's pinned protobuf version. In this snapshot,
ONNX's SBOM pins protobuf `31.1`, and CI installs protoc `31.1`. If the version
is wrong, symptoms include generated protobuf headers that fail to compile,
errors about older `protoc`, or missing/unknown protobuf namespace macros.

Local rule: put a matching `protoc` on `PATH` before `ORT_WEB=ON ./build_wasm.sh`.
Do not rely on a distro `protobuf-compiler` if it is older than the bundled ONNX
protobuf.

## ORT-web constant folding boundary

Default WASM uses a C++ `CppModelExecutor` backed by statically linked ONNX
Runtime. ORT-web WASM replaces that with `JsModelExecutor`:

```text
Simplify / RunOps in C++
  -> JsModelExecutor::Run(sub-model, positional DLPack-like inputs)
  -> Module.onnxsimOrtWebRun(modelBytes, inputsData, inputsMeta)
  -> onnxruntime-web InferenceSession.create(...).run(...)
  -> batched bytes/meta returned to C++
```

Boundary facts:

- Constant-fold sub-models are serialized ONNX `ModelProto` bytes.
- Tensor feeds and fetches are positional, not named. Input `i` maps to graph
  input `i`; outputs are returned in graph output order.
- Inputs are batched into one raw byte blob plus one metadata array per fold
  group. Metadata is a flat sequence of `[dtype, ndim, dims...]` entries.
- Outputs return as `{ data: Uint8Array, meta: Float64Array }` in the same
  layout.
- Supported ORT-web bridge dtypes match the implemented executor set: FLOAT,
  DOUBLE, INT64, UINT64, INT32, UINT8, INT8, UINT16, INT16, and BOOL.
- Asyncify makes the exported simplification call promise-like in the ORT-web
  variant. Web workers or callers must `await` it when `onnxsim_needs_ort_web()`
  reports true.
- Because onnxsim-wasm and onnxruntime-web are separate WASM modules with
  separate linear memories, true zero-copy tensor exchange is not possible. The
  design removes protobuf tensor serialization overhead, but data still crosses
  heap boundaries.
- WebGPU/WebNN outputs must be brought back to CPU for onnxsim to consume them.

## DLPack executor boundary

The native C API and Rust bindings expose a DLPack-based executor seam for
constant folding. It is useful when embedding onnxsim in another compiler or
runtime stack.

Important contract points:

- Tensors are CPU, contiguous, and little-endian at the boundary.
- Inputs are borrowed for the duration of the callback.
- Outputs are owned by the caller receiving them and released through each
  tensor's DLPack deleter.
- The model still crosses as serialized `ModelProto`; only runtime tensors use
  DLPack.
- Dtype support includes standard float, integer, unsigned integer, bfloat16,
  float16, and bool types supported by the bridge. STRING, complex, float8,
  int4/uint4/float4, and undefined tensor types are rejected.
- On big-endian hosts, conversions must byte-swap between ONNX raw little-endian
  tensor data and host-order DLPack buffers. The project has dedicated C++ and
  Python big-endian checks for this class of issue.

## npm package

The npm package is named `onnxsim` and is a Node.js-friendly wrapper around the
ORT-web WASM build.

Snapshot package facts:

- Package type: ESM (`"type": "module"`).
- Entry: `index.mjs`; types: `index.d.ts`.
- Runtime files: `index.mjs`, `index.d.ts`, `ort_executor.mjs`, `onnxsim.cjs`,
  `onnxsim.wasm`, and README.
- `onnxsim.cjs` is the Emscripten modularized CommonJS output renamed from
  `onnxsim.js`; this avoids ESM parsing of `module.exports` while preserving
  `__dirname` lookup for the sibling `.wasm` file.
- Runtime dependency: `onnxruntime-web` `^1.27.0`.
- Node engine: `>=18`.
- Public API covered by npm tests includes `simplify()` and `versions()`.

Build and stage locally only when a user asks for npm/WASM output:

```bash
ORT_WEB=ON ./build_wasm.sh
./scripts/stage_npm_package.sh build-wasm-node-OFF-ortweb
(cd npm/onnxsim && npm install && npm test && npm pack)
```

`npm pack` is the safe package smoke check. Avoid using unconditional
`npm publish --dry-run` for routine validation because it contacts the registry
and can fail simply because the package version already exists.

### Release staging

On a `v*` release, CI bumps binding versions, stages the ORT-web module into the
npm package, runs `npm test && npm pack`, and then uses npm staged publishing.
Staged publishing uploads to a review queue; it is not live until a maintainer
approves it with npm 2FA. The workflow's trusted-publisher setting must allow
stage publishing for this to work.

Maintainer actions after a staged release:

```bash
npm stage list --package onnxsim
npm stage view <stage-id>
npm stage approve <stage-id>   # or reject with npm stage reject <stage-id>
```

## Web demo and convertmodel tests

The hosted convertmodel demo uses the ORT-web variant. Production deploys happen
from push events on selected branches; preview deploys are opt-in through a
maintainer `/preview` comment; pull requests touching WASM/npm paths run the
cheaper build-plus-npm-validation path and skip Netron/deployment.

The demo validation stack includes Node tests for inference, comparison, backend
selection, WebNN, version reporting, traces, shapes, model loading, CDN behavior,
and related UI helpers. Treat these as web-demo/package validation, not as a
requirement for ordinary Python package installation.

## WebNN boundary

WebNN is an experimental inference-panel execution-provider option in the web
demo. It does not change model conversion or simplification.

Operational facts:

- WebNN is exposed through `navigator.ml` in supported Chromium-based browsers,
  often behind a browser flag and with strongest coverage on Windows.
- onnxruntime-web's WebNN provider is experimental and lives in its "all" bundle,
  so the panel loads that bundle on demand when WebNN is selected.
- Provider selection appends `wasm` as fallback for WebNN and WebGPU choices.
- The UI probes `gpu`, `npu`, and `cpu` WebNN device types, surfaces a status
  line, and logs detailed failures/ORT diagnostics for debugging.
- If WebNN fails or an operator is unsupported, fallback to WASM is expected;
  document which provider actually ran.

## Validation checklist

- For default WASM, expect ONNX Runtime source compile/download unless cached.
- For ORT-web WASM, confirm no ONNX Runtime C++ source is compiled and output is
  under an `ortweb` build directory.
- For npm, confirm `onnxsim.cjs`, `onnxsim.wasm`, and `ort_executor.mjs` are
  staged before `npm test` or `npm pack`.
- For browser/worker integration, await simplification when the module reports
  it needs ORT-web.
- For WebNN, always include fallback behavior and actual provider diagnostics.
