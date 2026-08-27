# Backend compatibility and capability planning

Use this matrix to decide whether a target runtime is usable, which optional dependency group to install, and which validation evidence is still required. Availability is environment-specific; probe it before planning exports or inference.

## Import and hardware probe

From this sub-skill directory:

```bash
python scripts/backend_capability_probe.py --json
python scripts/backend_capability_probe.py --require hf --require onnx-runtime
python scripts/backend_capability_probe.py --model pii_detection --json
```

The probe performs import and hardware checks only. It does not download, load, tokenize, or invoke any model.

## Optional backend keys

The OpenMed capability registry recognizes these runtime-related backend keys:

| Key | Typical install extra | Enables | Probe interpretation |
| --- | --- | --- | --- |
| `hf` | `openmed[hf]` | Hugging Face Transformers token-classification loading and cache prefetch helpers | Missing `transformers` or `huggingface_hub` means remote/local HF model loading is not ready. |
| `mlx` | `openmed[mlx]` | Apple MLX token-classification and MLX-LM artifacts | Requires Apple Silicon/macOS for useful acceleration; import availability alone is not enough. |
| `coreml` | `openmed[coreml]` | CoreML export for Apple app packages | Conversion usually requires macOS tooling for full validation; Linux may inspect but not validate ANE behavior. |
| `onnx` | `openmed[onnx]` | ONNX export, optimization, validation, and Python ONNX Runtime | Conversion pulls Torch/Transformers/ONNX tooling and is heavier than inference-only. |
| `onnx-runtime` | `openmed[onnx-runtime]` | Lightweight ONNX Runtime loading of existing artifacts | Use when an ONNX export already exists and no conversion is needed. |
| `openvino` | `openmed[openvino]` | OpenVINO IR export/inference and NNCF INT8 quantization | Needs OpenVINO runtime devices; CPU is common, GPU/NPU depend on host drivers. |
| `gliner` | `openmed[gliner]` | GLiNER zero-shot entity recognition | Not a standard Android token-classification export path; route carefully. |

Additional toolchains outside Python include Xcode/Swift Package Manager for OpenMedKit Apple apps, Android Gradle/JDK/ONNX Runtime Mobile for Android, and Node/npm plus browser WebGPU/WASM requirements for browser deployment.

## Runtime decision matrix

| Target | Primary modules/surfaces | Best for | Required evidence before use | Common blockers |
| --- | --- | --- | --- | --- |
| Python CPU with HF/Torch | `openmed.core.models.ModelLoader`, `openmed.torch`, `OpenMedConfig(backend="hf", device="cpu")` | Broad model compatibility and simple local/server execution | `hf` available, model cached or remote download approved, license accepted, tokenizer max length known | Missing `transformers`/`torch`, slow cold start, cache miss in offline mode |
| Python CUDA | `openmed.torch.resolve_torch_device`, `OpenMedConfig(device="cuda")` | Higher throughput on NVIDIA GPUs | Torch CUDA build matches driver, selected GPU visible, memory budget fits, quantization evidence if used | CPU-only Torch wheel, CUDA unavailable, out-of-memory, unsupported attention backend |
| Python MPS | `openmed.torch.resolve_torch_device`, `OpenMedConfig(device="mps")` | Apple GPU through Torch when MLX is not selected | macOS/Apple Silicon, Torch MPS available, parity with CPU checked | MPS unsupported op, fallback to CPU, memory pressure |
| Python MLX token classification | `openmed.mlx.create_mlx_pipeline`, `OpenMedConfig(backend="mlx")` | Apple Silicon acceleration with OpenMed MLX artifacts | macOS/Apple Silicon, `mlx` importable, `openmed-mlx.json`, tokenizer assets, label sidecar, supported family | Non-Apple host, unsupported architecture, missing tokenizer, unvalidated quantization |
| MLX-LM generation | `openmed.mlx.OpenMedMLXLanguageModel`, `generate_text`, paged KV cache helpers | Local Apple Silicon text generation artifacts | `mlx-lm` available, target and draft tokenizer alignment when speculative decoding is used, permissive draft license | Not a token-classification pipeline, unsupported model alias, excessive KV cache memory |
| Python ONNX Runtime | `openmed.onnx.load_onnx_model`, `OpenMedConfig(backend="onnx")` | Torch-free local CPU inference with exported token-classification artifacts | `onnxruntime`, `tokenizers`, `numpy`, labels, tokenizer assets, provider selection, variant present | Missing `model_int8.onnx` for int8-only profile, provider fallback, missing `id2label` |
| OpenVINO | `openmed.onnx.OpenVinoTokenClassificationSession`, `resolve_openvino_device` | Intel CPU/GPU/NPU edge targets | OpenVINO runtime devices listed, ONNX-to-IR verification, quantization recall evidence for INT8 | No NPU/GPU plugin, unsupported ops, missing NNCF, recall gate rejection |
| CoreML package | `openmed.coreml.convert`, bundle validators | Bundled iOS/macOS/watchOS/visionOS artifacts | Supported model family, `.mlpackage`/`.mlmodelc`, `id2label`, compute units, parity report | Unsupported architecture, ANE residency below threshold, simulator not representative for MLX |
| Android ONNX Runtime Mobile | ONNX Android profile, Android OpenMedKit model catalog/cache/runtime | On-device Android token classification | `onnx-android`/`onnx-int8`/`ort-android` artifact metadata, tokenizer assets, catalog hash, exact span parity | Missing ORT conversion tooling, no compatible ABI, tokenizer drift, cache not ready |
| Swift OpenMedKit MLX | Swift `OpenMed(backend: .mlx(...))`, `OpenMedModelStore` | Apple Silicon macOS and real iPhone/iPad devices | MLX artifact layout, app-local cache, platform supports MLX, tokenizer assets | iOS Simulator, unsupported family, network during inference, model too large |
| Swift OpenMedKit CoreML | Swift `OpenMed(backend: .coreML(...))`, `PlatformModel` | Bundled CoreML and constrained Apple platforms | `mlmodelc`/`mlpackage`, `id2label`, tokenizer reference/assets, Nano INT8 checks for watchOS/visionOS | Non-Nano artifact on constrained platform, over memory budget, missing labels |
| Browser Transformers.js | `transformersjs` bundle | Local browser token-classification through Transformers.js | Bundle contract, local/static asset path, tokenizer assets, `config.json` labels | Remote URL rejected for PHI workflows, missing `model_quantized.onnx`, WebGPU unavailable |
| Browser ONNX Runtime Web | OpenMed browser loader plus `onnxruntime-web` | Local WebGPU/WASM execution with exported ONNX graph | Local model path, local wasm assets, WebGPU or cross-origin-isolated WASM capability | Missing COOP/COEP headers for threaded WASM, CDN asset URL, provider fallback |

## Artifact format support summary

| Family or architecture class | MLX | CoreML | ONNX/default | ONNX Android | Browser bundle | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| BERT / DistilBERT / Electra / RoBERTa / XLM-RoBERTa | Supported | Supported | Supported | Supported | Supported | Standard token-classification path. |
| DeBERTa-v2 / DeBERTa-v3-compatible token classification | Supported where converter allows it | Supported for DeBERTa-v2 family | Supported if upstream export works | Supported if parity passes | Supported if ONNX contract passes | Verify tokenizer behavior carefully. |
| OpenAI Privacy Filter family | Supported through specific MLX runtimes | Not a CoreML allowlist target | Not a standard ONNX path | Not a standard Android path | Not a standard browser path | Keep on supported Python/MLX paths until a certified export exists. |
| GLiNER-family span/class/relation models | Supported through MLX custom family paths | Not supported | Not standard token-classification export | Not supported by standard Android session | Not supported by standard browser bundle | Requires prompt labels/word masks/span decoding; do not force into BIO token-classification. |
| ModernBERT / Longformer / Qwen-like families | Generally not in first-class mobile converter allowlists | Not supported unless converter adds family | Conditional on upstream exporter and validators | Conditional and often unsupported | Conditional | Treat as research/export work, not a guaranteed runtime path. |
| Text-generation MLX-LM artifacts | MLX-LM path | Not a token-classification CoreML path | Not the same as token-classification ONNX | Not the same as Android token classification | Not covered by token-classification browser bundle | Validate prompt/cache behavior separately; avoid clinical-decision automation. |

## Hardware and provider checks

- **CPU**: inspect architecture and SIMD flags when using INT8 fast paths; scalar fallback is valid but slower.
- **CUDA**: require a CUDA-capable Torch build and a visible GPU. `nvidia-smi` visibility does not prove that the Python wheel can use CUDA.
- **MPS**: only on Apple platforms with compatible Torch. Apply MPS tuning explicitly when used.
- **MLX**: useful only on Apple Silicon/macOS or supported Apple devices through Swift. Non-Apple hosts should route to HF/Torch or ONNX.
- **ANE/CoreML**: compute-unit selection and ANE residency must be measured on Apple tooling; a conversion file alone is not proof of Neural Engine execution.
- **ONNX Runtime providers**: list providers and compare against requested providers. A session silently falling back to CPU can invalidate latency claims.
- **OpenVINO devices**: list devices through the runtime. CPU availability is common; GPU/NPU require drivers/plugins.
- **Android**: confirm min SDK, ABI, ORT Mobile operator config, Gradle/JDK, tokenizer AAR, and app-local cache behavior.
- **Browser**: confirm WebGPU capability or WASM mode. Threaded WASM requires cross-origin isolation headers; no remote assets for PHI workflows.

## Platform parity evidence

Minimum parity record for every mobile/browser artifact:

```json
{
  "synthetic": true,
  "model_id": "OpenMed/example-token-classifier",
  "artifact_format": "onnx-android",
  "token_ids": "exact",
  "char_offsets": "exact",
  "span_labels": "exact",
  "span_boundaries": {"mode": "exact", "tolerance_chars": 0},
  "quantization": {"precision": "int8", "certified": true},
  "runtime": {"platform": "android", "provider": "CPUExecutionProvider"}
}
```

If any tokenizer or span field drifts, treat the artifact as not portable until the drift is explained and accepted. Do not compensate by shifting spans after the fact; fix tokenizer assets, decoder logic, or aggregation settings.
