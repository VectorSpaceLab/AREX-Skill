---
name: gptq-quantization
description: "Configure, save, load, and troubleshoot Optimum GPT-QModel
  quantization workflows with explicit backend requirements."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Optimum GPTQ Quantization

Use this sub-skill when a task asks for Optimum's GPT-QModel integration: configuring `GPTQQuantizer`, running or planning GPTQ quantization for text causal language models, saving quantized checkpoints, loading saved quantized weights, selecting GPT-QModel kernels, or diagnosing GPTQ dependency and serialization failures.

Do not use this sub-skill for ONNX Runtime, OpenVINO, Intel Neural Compressor, or exporter CLI quantization; route those to the exporter/CLI workflow. Do not use it for general dummy-input or `NormalizedConfig` utilities; route those to the utility/config workflow.

## Safe entry sequence

1. Before any model download, quantization run, or checkpoint load, run the bundled availability probe:
   - [`scripts/gptq_availability_probe.py`](scripts/gptq_availability_probe.py)
2. If the probe reports missing `gptqmodel>=7.0.0`, missing `accelerate`, or no usable accelerator, treat full GPTQ quantization/loading as an optional backend gap unless the user explicitly approves installing dependencies and using GPU time.
3. Confirm the model is a text `CausalLM`-style model and will be loaded as `torch.float16` before quantization.
4. For custom architectures, identify the Transformer block path and maximum sequence length before quantization; do not rely on automatic discovery if the probe or helper functions cannot infer them.

## Reference map

- [`references/gptq-workflows.md`](references/gptq-workflows.md): task-oriented quantize, save, load, custom-model, dataset, and backend workflows.
- [`references/api-reference.md`](references/api-reference.md): constructor fields, method signatures, helper functions, serialization keys, and dataset helpers.
- [`references/troubleshooting.md`](references/troubleshooting.md): dependency, CUDA, dtype, custom-model, offload, save/load, and backend-selection failures.

## Operating boundaries

- The bundled script is a lightweight availability/config probe only; it performs no downloads, no quantization, no training, and no checkpoint writes.
- Full native GPTQ validation needs `gptqmodel>=7.0.0`, `accelerate`, a compatible Transformers stack, CUDA or another GPT-QModel-supported accelerator, model/tokenizer access, and an explicit time/memory budget.
- A CPU-only import or config probe is not proof that quantization kernels or serialized quantized inference will work.
