---
name: model-loading-and-export
description: "Use for LlamaFactory model/tokenizer/processor loading, model
  patches, LoRA adapter loading/merge/export, export-time GPTQ quantization,
  on-the-fly quantization backends, value-head export, checkpoint utilities, and
  hub/cache/revision/trust settings."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Model Loading and Export

Use this sub-skill when an agent needs to load, patch, merge, quantize, export, or diagnose LlamaFactory v0 model artifacts for source behavior `0.9.6.dev0`.

## Route Here For

- `model_name_or_path`, `adapter_name_or_path`, tokenizer/processor loading, `trust_remote_code`, `cache_dir`, `model_revision`, and hub tokens.
- LoRA/OFT adapter load, resume, merge, export, `create_new_adapter`, `pissa_init`, `pissa_convert`, value-head/RM checkpoints, and `additional_target` interactions.
- `llamafactory-cli export CONFIG.yaml` or `lmf export CONFIG.yaml`, including adapter merge, full-model export, Ollama `Modelfile`, tokenizer/processor saving, and hub push settings.
- Quantization choices for PTQ models, QLoRA/on-the-fly training or inference, and export-time GPTQ quantization.
- Model patches and utilities such as vocab resize, RoPE/attention/kv-cache/kernel switches, MoD, Unsloth, Liger, KTransformers, and checkpoint conversion/init planning.

## Boundaries

- Route training launch mechanics, dataset sampling, optimizers, distributed training, CLI overrides, and experiment tracking to `training-and-configs`.
- Route dataset registration, prompt templates, multimodal data schemas, and tokenizer-template fixes to `data-and-templates` unless the failure is directly in model/tokenizer/processor loading.
- Route chat/API/Web UI/vLLM/SGLang serving behavior to `inference-and-serving` unless the issue is model loading, adapter, or quantization setup.
- Treat source checkpoint conversion and initialization utilities as reference-only plans unless the user explicitly authorizes large CPU/GPU and disk operations.

## Start With

1. Identify the operation: load, train-time adapter setup, export/merge, export quantization, or checkpoint utility.
2. Read `references/model-loading.md` for loader arguments, tokenizer/processor behavior, patches, adapters, and value-head concerns.
3. Read `references/export-and-quantization.md` before editing export YAML or choosing a quantization backend.
4. Read `references/checkpoint-utilities.md` before recommending PiSSA/LoftQ/LLaMA-Pro/DCP/other checkpoint conversions.
5. Read `references/troubleshooting.md` when errors mention tokenizer/processor loading, remote code, hub access, quantized vocab resize, adapter merge, optional dependencies, or hub mirrors.

## Bundled Helper

- `scripts/check_export_config.py` statically checks YAML/JSON export configs for common LlamaFactory pitfalls without importing LlamaFactory, Transformers, PyTorch, or downloading models.

## Safety

- Never run model downloads, adapter merges, export quantization, checkpoint conversion, or hub pushes without explicit user approval and a concrete output path.
- Do not put secrets in config files; prefer environment variables for hub tokens and mirror controls.
- Warn that quantized model merge/export operations are constrained: adapters must be merged before export quantization, and adapters cannot be merged into an already quantized model.
