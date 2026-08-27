---
name: model-runtimes-mobile
description: "Operate OpenMed model discovery, local/offline caches, backend
  selection, runtime/export probes, and mobile/browser parity without implicit
  model invocation."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# OpenMed model runtimes and mobile/browser routing

Use this sub-skill when a task asks how to choose, cache, inspect, export, or run OpenMed models across Python, Apple, Android, or browser runtimes. Keep the workflow local-first: never download, load, or invoke a model unless the downstream user explicitly asks for that action and the model license/data terms are acceptable.

## Route map

- **Model discovery and selection**: use `openmed.core.model_registry`, the top-level `openmed.list_models(...)`, and manifest metadata summarized in `references/model-runtime-workflows.md`.
- **Offline/Hugging Face cache planning**: use `openmed.core.hf_hub` helpers and `OPENMED_OFFLINE`/`OpenMedConfig(local_only=True)` guidance in `references/model-runtime-workflows.md`.
- **Python pipeline loading**: use `openmed.core.models.ModelLoader`, `OpenMedConfig(backend=...)`, and cache-release methods from `references/model-runtime-workflows.md`.
- **Backend capability checks**: run the bundled `scripts/backend_capability_probe.py` and interpret the matrix in `references/backend-compatibility.md`.
- **Runtime/export choices**: choose among Hugging Face/Torch, MLX/MLX-LM, ONNX Runtime, OpenVINO, CoreML, Android ONNX Runtime Mobile, Swift OpenMedKit, or browser WebGPU/WASM using `references/backend-compatibility.md`.
- **Failure diagnosis**: use `references/troubleshooting.md` for offline cache misses, missing extras, unsupported hardware, tokenizer/span drift, quantized recall deltas, artifact layout problems, and platform toolchain issues.

## Boundaries

This sub-skill covers runtime and artifact operations only. Route clinical task design and high-level NER/grounding behavior to `clinical-extraction-grounding`; route PHI/PII policy semantics, masking, date shifting, and surrogate handling to `deidentification-privacy`; route REST/MCP/service deployment contracts to `interoperability-serving`.

Use synthetic text only in examples and probes. Do not log raw clinical text, token strings from real notes, secrets, Hub tokens, local cache contents containing sensitive filenames, or model outputs from real PHI.

## Minimal safe first step

From this sub-skill directory, probe capabilities without downloads or model loads:

```bash
python scripts/backend_capability_probe.py --json
```

The probe reports import availability, optional extras, and hardware/toolchain signals. Treat unavailable optional backends as planning constraints, not as package failures, unless the user's requested target requires that backend.
