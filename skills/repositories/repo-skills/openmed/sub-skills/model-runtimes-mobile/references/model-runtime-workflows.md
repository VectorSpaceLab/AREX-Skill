# Model runtime workflows

This reference is for selecting OpenMed model artifacts, planning local caches, and preparing runtime/export work across Python, Apple, Android, and browser targets. It is intentionally runtime-only: do not design clinical extraction behavior, PHI de-identification policy, or service deployment here.

## Operating invariants

- **Local-first by default**: discovery from the committed model manifest is safe and offline; downloads are explicit preparation steps.
- **No implicit inference**: inspect registries, imports, cache state, and artifact manifests before invoking any model.
- **Synthetic examples only**: use placeholder notes such as `SYNTH_PATIENT_001 has SYNTH_CONDITION_A`; never test runtime plumbing with real PHI.
- **Model terms matter**: inspect `license`, gated/restricted access requirements, and data-use terms before prefetching, exporting, or shipping an artifact.
- **Parity is a release gate**: tokenizer IDs, character offsets, span labels, and span boundaries must match the Python reference for mobile/browser token-classification artifacts.

## 1. Discover candidate models without downloads

Primary modules:

- `openmed.core.model_registry`
- top-level `openmed.list_models(...)`
- canonical manifest rows exposed through `models.jsonl` and `ModelInfo`

Use the registry before touching Hugging Face or a local cache:

```python
from openmed import list_models
from openmed.core.model_registry import (
    get_all_models,
    get_model_info,
    get_model_suggestions,
    get_models_by_category,
    list_model_categories,
)

print(list_model_categories())
print(list_models(include_registry=True, include_remote=False)[:10])

info = get_model_info("pii_detection")
if info is not None:
    print({
        "model_id": info.model_id,
        "category": info.category,
        "task": info.task,
        "formats": info.formats,
        "languages": info.languages,
        "tier": info.tier,
        "license": info.license,
        "download_mb": info.download_mb,
        "peak_ram_mb": info.peak_ram_mb,
        "recommended_confidence": info.recommended_confidence,
    })

for key, model, reason in get_model_suggestions("oncology token-classification"):
    print(key, model.model_id, reason)
```

Selection rules:

1. Match the task family first (`token-classification`, privacy/PII, biomedical NER, or text generation).
2. Filter by target runtime format: `pytorch`, `mlx-fp`, `mlx-8bit`, `mlx-4bit`, `onnx`, `onnx-android`, `onnx-int8`, `ort-android`, `webgpu`, `transformersjs`, or `coreml` when the artifact manifest records it.
3. Check `languages`, tokenizer script coverage, `tier`, `param_count`, `download_mb`, `disk_mb`, `peak_ram_mb`, `latency_ms`, and `recommended_tier` against the deployment budget.
4. Verify `license` and any gated-model requirement before planning a download.
5. Prefer the smallest model that meets recall/parity requirements; do not choose a quantized artifact just because it is smaller unless its recall-delta report is accepted.

The CLI model-size path is also safe for offline planning because it uses manifest estimates unless a remote lookup is explicitly requested:

```bash
OPENMED_OFFLINE=1 openmed models size pii_detection --format json
openmed models size --budget-mb 512 --format json
```

## 2. Plan Hugging Face and local caches

Primary modules:

- `openmed.core.hf_hub.resolve_repo_id`
- `openmed.core.hf_hub.prefetch_model`
- `openmed.core.hf_hub.list_cached_models`
- `openmed.core.hf_hub.clear_cached_model`
- `openmed.core.offline` through `OPENMED_OFFLINE` or `OpenMedConfig(local_only=True)`

Connected preparation step, only after the user approves the model and terms:

```python
from openmed.core.hf_hub import prefetch_model, resolve_repo_id

repo_id = resolve_repo_id("pii_detection")
print(repo_id)

snapshot_dir = prefetch_model(
    "pii_detection",
    revision="main",
    allow_patterns=[
        "config.json",
        "tokenizer.json",
        "tokenizer_config.json",
        "special_tokens_map.json",
        "*.safetensors",
        "*.onnx",
        "openmed-*.json",
        "id2label.json",
    ],
    max_bandwidth=None,
)
print(snapshot_dir)
```

Offline execution step:

```bash
export OPENMED_OFFLINE=1
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
python - <<'PY'
from openmed.core.hf_hub import list_cached_models
print([model.repo_id for model in list_cached_models()])
PY
```

Cache planning checklist:

- Pin a model revision or immutable artifact version when reproducibility matters.
- Keep `HF_HOME`, `HF_HUB_CACHE`, and OpenMed `cache_dir` stable between prefetch and execution.
- Treat an offline cache miss as a planning failure, not as a reason to disable offline mode during PHI processing.
- Store PHI-free evidence only: repo id, revision, content hashes, byte counts, artifact formats, and validation outcomes.
- Do not serialize access tokens, raw note text, decoded spans from real text, or user-specific cache paths into shareable reports.

## 3. Load Python models through `ModelLoader`

Primary modules:

- `openmed.core.models.ModelLoader`
- `openmed.core.config.OpenMedConfig`
- `openmed.core.backends` through the `backend` field

`ModelLoader` centralizes cache reuse, tokenizer reuse, backend selection, Hub auth, local-only behavior, max-length checks, and model unloading.

```python
from openmed import ModelLoader, OpenMedConfig

config = OpenMedConfig(
    backend="hf",          # None=auto, or one of "hf", "mlx", "onnx"
    device="cpu",         # "cuda", "cuda:1", "mps", or "cpu" when supported
    cache_dir="./openmed-model-cache",
    local_only=True,
)
loader = ModelLoader(config=config)

max_len = loader.get_max_sequence_length("pii_detection")
print(max_len)

pipeline = loader.create_pipeline(
    "pii_detection",
    task="token-classification",
    aggregation_strategy="simple",
    use_fast_tokenizer=True,
    local_files_only=True,
)

# Invoke only when the user explicitly requested inference and the input is safe.
entities = pipeline("SYNTH_PATIENT_001 visited SYNTH_CLINIC_A.")

loader.unload_model("pii_detection")
loader.unload_all_models()
```

Backend auto-selection for Python token classification:

1. On Apple Silicon with `mlx` installed, `backend=None` can select MLX.
2. Hugging Face/Torch is the default general backend when available.
3. ONNX Runtime can be selected with `backend="onnx"` for CPU-only exported artifacts.

For a vendored local artifact directory, pass the directory path instead of a Hub id. Existing filesystem paths are treated as local model references; for Hugging Face/Torch loading, OpenMed uses cache-only behavior for local paths.

## 4. Use runtime-specific paths

### Hugging Face / Torch

Use when you need the broadest architecture support, CUDA, MPS, attention-backend control, or HF pipeline compatibility.

```python
from openmed import ModelLoader, OpenMedConfig
from openmed.torch import resolve_torch_device

print(resolve_torch_device("auto"))
loader = ModelLoader(OpenMedConfig(backend="hf", device="cuda"))
```

Torch quantization helpers live under `openmed.torch` and are optional. Apply AWQ/GPTQ/4-bit options only when their required packages and calibration evidence are present.

### MLX and MLX-LM

Use `openmed[mlx]` on Apple Silicon for Python MLX token-classification and MLX-LM text-generation artifacts. MLX token-classification artifacts should be self-contained with:

```text
openmed-mlx.json
config.json
id2label.json
tokenizer assets
weights.safetensors  # preferred
weights.npz          # fallback when needed
```

Python examples:

```python
from openmed import ModelLoader, OpenMedConfig
from openmed.mlx import OpenMedMLXLanguageModel, tokenizers_are_aligned

loader = ModelLoader(OpenMedConfig(backend="mlx", local_only=True))

runner = OpenMedMLXLanguageModel("OpenMed/laneformer-2b-it-q4-mlx")
# Generation is model invocation; do it only when explicitly requested.
```

For speculative decoding, require tokenizer alignment between target and draft models before accepting speedups. Reject a draft model if its license is not permissive or if the tokenizer fingerprint differs.

### ONNX Runtime and WebGPU export

Use `openmed[onnx]` for conversion and `openmed[onnx-runtime]` for lightweight Python ONNX inference.

```bash
python -m openmed.onnx.convert \
  --model OpenMed/OpenMed-PII-SuperClinical-Small-44M-v1 \
  --output dist/synthetic-onnx \
  --include-transformersjs
```

Expected default export shape:

```text
dist/synthetic-onnx/
  config.json
  id2label.json
  tokenizer.json
  tokenizer_config.json
  model.unoptimized.onnx
  model.onnx
  model.webgpu.onnx
  openmed-onnx.json
  transformersjs/
    config.json
    tokenizer.json
    tokenizer_config.json
    quantize_config.json
    transformersjs-contract.json
    onnx/
      model.onnx
      model_quantized.onnx
```

Load a local ONNX artifact without Torch:

```python
from openmed.onnx import load_onnx_model

model = load_onnx_model("dist/synthetic-onnx", variant="fp32")
# Invoke only on synthetic or approved input.
```

### OpenVINO

Use OpenVINO IR for Intel CPU/GPU/NPU edge targets when `openmed[openvino]` is installed.

```python
from openmed.onnx import OpenVinoTokenClassificationSession, resolve_openvino_device

selection = resolve_openvino_device("NPU")
print(selection)
session = OpenVinoTokenClassificationSession(
    "dist/synthetic-openvino/openvino/model.xml",
    device="NPU",
)
```

Device selection is deterministic. If the requested device is not available, it falls back through CPU/GPU/NPU according to the runtime selector and records that fallback.

### CoreML

Use `openmed[coreml]` to package Hugging Face token-classification checkpoints for Apple apps.

```bash
python -m openmed.coreml.convert \
  --model OpenMed/OpenMed-PII-SuperClinical-Small-44M-v1 \
  --output dist/OpenMedPIISmall.mlpackage \
  --precision float16 \
  --compute-units cpuAndNeuralEngine \
  --quantize int8
```

Supported source families are BERT, DistilBERT, Electra, RoBERTa, XLM-RoBERTa, and DeBERTa-v2. Unsupported architectures should fail before tracing.

### Android

Use Android ONNX Runtime Mobile when the target is an Android app-local model directory. An Android export should include:

```text
model.onnx
model_fp16.onnx
model_int8.onnx
model.ort                         # when ORT mobile conversion tooling is available
model.required_operators_and_types.config
config.json
id2label.json
openmed-onnx.json
tokenizer assets
```

Android apps should load compatible entries from the bundled model catalog, download during an explicit setup step, verify checksums before exposing a model as ready, and perform inference from the app-local cache. Runtime inference must not require network permission.

### Swift / OpenMedKit

Use Swift OpenMedKit for macOS, iOS, iPadOS, watchOS, and visionOS. Choose MLX for Apple Silicon Macs or real iPhone/iPad devices; choose CoreML for bundled packages, simulators, watchOS, visionOS, or older OS fallbacks.

Apple platform constraints:

| Platform | Runtime path | Practical constraint |
| --- | --- | --- |
| macOS 14+ Apple Silicon | MLX or CoreML | Base-tier models can fit if memory allows. |
| iOS/iPadOS 17+ physical device | MLX or CoreML | Prefer Tiny-tier artifacts and bounded sequence lengths. |
| iOS Simulator | CoreML | Do not use Swift MLX as the simulator validation target. |
| watchOS 10+ | CoreML Nano INT8 | Fail closed for non-Nano, non-INT8, or over-budget artifacts. |
| visionOS 1+ | CoreML Nano INT8 | Same constrained-platform checks as watchOS. |

### Browser

Use Transformers.js bundles or ONNX Runtime Web only with local/static model assets. Browser loaders should reject remote model URLs for PHI-processing workflows; use WebGPU when available, threaded WASM only when cross-origin isolation headers enable `SharedArrayBuffer`, and single-threaded WASM otherwise.

## 5. Quantization and certification caveats

- **MLX INT4**: require `recall_delta.json`; accept only when `certified: true` and the max per-label recall loss is within the configured limit.
- **MLX INT8/fp**: still require artifact manifest validation and tokenizer/span parity against the parent.
- **ONNX dynamic INT8**: verify fp32 parent vs `model_int8.onnx` on synthetic calibration/parity cases; an over-budget recall delta must block release even if the artifact exists.
- **OpenVINO INT8**: require calibration data plus per-family recall evidence; reject if required labels lose too much recall.
- **CoreML INT8/palettized variants**: require sidecar labels and parity report comparing spans with the source model.
- **Torch AWQ/GPTQ/bitsandbytes**: require explicit calibration text, device compatibility, and task-specific recall certification. A load-time quantization config is not a clinical validation.

For privacy runtimes, direct-identifier recall and critical leakage matter more than aggregate F1. Quantized and mobile variants need synthetic safety sweeps that target names, IDs, dates, phone-like tokens, multilingual scripts, and edge-case boundaries.

## 6. Platform parity checklist

Before treating a model as portable across Python, Android, Swift, or browser:

1. Use the same tokenizer assets (`tokenizer.json`, tokenizer config, special tokens, vocabulary/merges as applicable).
2. Compare token IDs exactly on synthetic cases.
3. Compare character offsets exactly unless a documented platform tolerance was approved for that platform.
4. Compare span labels and span boundaries after decoding.
5. Verify tie-breaking, aggregation strategy, confidence threshold, max sequence length, truncation behavior, and special-token masking.
6. Confirm no runtime logs raw input text, token strings, or decoded PHI-like spans.
7. Record artifact format, revision, content hash, quantization, precision, platform, and toolchain versions in PHI-free evidence.
