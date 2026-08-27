# Runtime Platforms and Deployment Choices

Read this when mapping a WeNet model artifact to a deployment target.

## Runtime matrix

| Target | Typical engine | Expected model artifacts | Key prerequisites |
|---|---|---|---|
| Linux/macOS/Windows C++ | libtorch | JIT `final.zip`, `units.txt`, feature/tokenizer resources, optional `global_cmvn` | CMake, compiler, compatible libtorch |
| Linux/macOS/Windows C++ | ONNX Runtime | encoder/ctc/decoder ONNX files, units/tokenizer resources, CMVN/config metadata | CMake, ONNX Runtime SDK/providers |
| Linux/macOS/Windows C++ | OpenVINO | OpenVINO-compatible exported artifacts | OpenVINO toolkit, CMake, compatible model ops |
| Android | libtorch mobile | mobile-ready JIT/runtime assets | Android Gradle toolchain, mobile libtorch/AARs |
| iOS | libtorch mobile | mobile-ready JIT/runtime assets | Xcode/CocoaPods and iOS toolchain |
| Web demo | Python/libtorch binding or app wrapper | JIT/runtime model files | Python web dependencies and model bundle |
| Raspberry Pi | ONNX Runtime | ONNX model files and resources | ARM-compatible ONNX Runtime and compiler/toolchain |
| Linux GPU service | Triton/TensorRT/ONNX Runtime GPU | ONNX/TensorRT-ready artifacts and model repository | NVIDIA GPU, driver, CUDA, TensorRT/Triton, server/client ports |
| Intel optimized | libtorch + IPEX | IPEX-compatible exported model | Intel Extension for PyTorch and compatible CPU/GPU runtime |
| Horizon BPU | BPU runtime | BPU-converted binary plus metadata | Horizon SDK/toolchain and target hardware |
| Kunlun XPU | XPU runtime | XPU-compatible model/runtime files | Kunlun SDK/toolchain and target hardware |

Use the bundled chooser for a quick machine-readable summary:

```bash
python sub-skills/runtime-deployment/scripts/choose_runtime.py \
  --platform linux --backend onnxruntime --format markdown
```

## U2 streaming and non-streaming concepts

WeNet runtime follows the U2 streaming/non-streaming design:

- Non-streaming uses full-context encoder computation and usually has best
  accuracy but highest latency.
- Streaming uses fixed chunks and caches to bound latency.
- Runtime chunk settings must match export choices such as `chunk_size` and
  `num_decoding_left_chunks`.
- Caches include attention cache and CNN cache; deployment failures often come
  from mismatched cache shapes or using non-streaming artifacts in streaming
  mode.

## Artifact handoff checklist

Before building a runtime, collect:

- exported model files for the chosen engine;
- `units.txt` and tokenizer resources;
- feature configuration and optional `global_cmvn`;
- runtime config values: sample rate, feature dim, chunk size, left chunks,
  beam/search weights, context or LM graph files when used;
- platform toolchain versions;
- hardware/backend availability.

## Deployment templates

### CPU server or command-line runtime

1. Export JIT for libtorch or ONNX for ONNX Runtime.
2. Install CMake/compiler and the matching runtime SDK.
3. Build the runtime target with only the required backend enabled.
4. Run a tiny audio smoke test before benchmarking.
5. Add LM/context graph files only after the baseline runtime works.

### GPU Triton/TensorRT service

1. Export ONNX artifacts compatible with the intended GPU runtime.
2. Verify NVIDIA driver, CUDA runtime, TensorRT/Triton versions, and GPU memory.
3. Convert/build the model repository with the selected precision and batching
   policy.
4. Start the server only after ports, model path, and GPU allocation are
   approved.
5. Use a client/performance script only against an authorized endpoint.

### Mobile or edge runtime

1. Choose mobile-compatible artifacts and model size.
2. Verify Android/iOS/Raspberry Pi toolchain and target architecture.
3. Keep resource files bundled with the app/runtime package.
4. Test short audio locally before optimizing latency or quantization.

## LM and context graph deployment

Language-model and context-biasing runtime paths require consistent word/unit
files, graph artifacts, and decoding weights. Verify baseline acoustic decoding
first, then add LM/context files and tune scores. If graph units do not match
`units.txt`, rebuild the graph rather than patching runtime flags.

## Why runtime scripts are reference-only

The source runtime tree includes C++ build systems, GPU service clients,
conversion scripts, mobile projects, and vendor toolchain hooks. They are not
bundled as runnable skill scripts because they require platform SDKs, external
model artifacts, GPUs/services, network endpoints, or large builds. This skill
bundles a safe chooser and distilled runbooks instead.
