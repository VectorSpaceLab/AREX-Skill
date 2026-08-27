---
name: quantization-integrations
description: "Choose and validate Transformers quantization methods, backend
  integrations, device placement, PEFT/Accelerate/DeepSpeed/FSDP/kernel
  interactions, and no-download config smoke checks."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Transformers Quantization Integrations

Use this sub-skill when the task is to reduce model memory, load or create quantized checkpoints, choose a quantization backend, combine quantization with PEFT/training/serving, or diagnose backend-specific optional dependency and device placement failures.

Transformers inspected version: `5.13.0.dev0`. Import package: `transformers`. A minimal environment can import base Transformers, but most quantization workflows require `torch` plus backend packages such as `accelerate`, `bitsandbytes`, `gptqmodel`, `autoawq`, `torchao`, `peft`, `deepspeed`, or hardware-specific kernels.

## Route Here

- Choose between `BitsAndBytesConfig`, `GPTQConfig`, `AwqConfig`, `TorchAoConfig`, GGUF/GGML loading, compressed-tensors, Quanto, HQQ, AQLM, EETQ, FP8, Quark, VPTQ, SpQR, SINQ, Metal, or other `quantization_config` methods.
- Decide whether a user needs on-the-fly quantization, a pre-quantized checkpoint, or a calibration/quantization job.
- Configure `AutoModelForCausalLM.from_pretrained(..., quantization_config=..., device_map=..., dtype="auto")` without downloading models during planning.
- Combine quantized models with PEFT/QLoRA, LoRA adapters, Accelerate `device_map`, CPU/disk offload, DeepSpeed, FSDP, tensor parallelism, or custom kernels.
- Check install and hardware constraints for CPU, CUDA, ROCm, MPS/Metal, Intel XPU, Gaudi/HPU, and `torch.compile`.
- Diagnose quantized checkpoint mismatch, missing optional packages, unsupported kernels, serialization limits, offload conflicts, or continuous batching incompatibilities.

## Route Elsewhere

- Inference task selection, `pipeline(...)` kwargs, and pipeline output behavior: [inference-pipelines](../inference-pipelines/SKILL.md).
- Decoding controls, `GenerationConfig`, streamers, and generation-only continuous batching concepts: [generation](../generation/SKILL.md).
- `Trainer`, `TrainingArguments`, datasets, collators, and ordinary fine-tuning loops: [training](../training/SKILL.md).
- Tokenizer, processor, chat template, image/audio/video preprocessing, and special-token choices: [tokenizers-processors](../tokenizers-processors/SKILL.md).
- `transformers` CLI commands, HTTP serving, and endpoint routing: [serving-cli](../serving-cli/SKILL.md).
- Adding new architectures, configs, model files, or processors: [model-extension](../model-extension/SKILL.md).

## Fast Decision Checklist

1. Identify the goal: memory-only loading, faster inference, CPU-only inference, QLoRA/PEFT fine-tuning, pre-quantized checkpoint loading, or creating a new quantized checkpoint.
2. Identify hardware: CPU, CUDA GPU generation, ROCm, Apple Silicon/Metal/MPS, Intel XPU, Gaudi/HPU, multi-GPU, or no backend available.
3. Prefer easy on-the-fly paths first: `bitsandbytes` for common 4/8-bit GPU workflows, `torchao` for PyTorch/compile-oriented paths, HQQ/SINQ/Quanto when their backend matches the host.
4. Prefer pre-quantized paths when calibration is expensive: AWQ and GPTQ are often loaded as existing 4-bit checkpoints; creating them requires calibration data and time.
5. Keep `dtype="auto"` and `device_map="auto"` deliberate: they are useful for large models but can conflict with tensor parallelism, offload, or unsupported backends.
6. Validate config construction locally before downloads with `scripts/quantization_config_smoke.py`.
7. Separate config validation from model execution: constructing a config does not prove kernels, GPU drivers, checkpoint metadata, or memory capacity.
8. For quantized training, update only extra parameters unless the backend explicitly supports broader training; QLoRA usually means frozen 4-bit base weights plus PEFT adapters.

## Common Starting Points

- Choose a method and backend matrix: [quantization methods](references/quantization-methods.md).
- Combine with Accelerate, PEFT, DeepSpeed, FSDP, tensor parallelism, kernels, or serving: [integration workflows](references/integration-workflows.md).
- Check optional package, hardware, compile, serialization, and device placement constraints: [compatibility](references/compatibility.md).
- Diagnose failures and expected signals: [troubleshooting](references/troubleshooting.md).

## Canonical Loading Pattern

```python
from transformers import AutoModelForCausalLM, BitsAndBytesConfig

quantization_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype="bfloat16",
)
model = AutoModelForCausalLM.from_pretrained(
    "org/model",
    quantization_config=quantization_config,
    device_map="auto",
    dtype="auto",
)
```

Use this as a shape, not a universal default. Replace `BitsAndBytesConfig` when the checkpoint already declares another method, when the host is CPU-only and GGUF is the intended format, or when the backend requires calibration, specialized kernels, or a different package.

## No-download Config Smoke Check

Run the bundled helper from this sub-skill directory or pass its path explicitly:

```bash
python scripts/quantization_config_smoke.py --method bitsandbytes-4bit --print-json
python scripts/quantization_config_smoke.py --method gptq --bits 4 --dataset c4
python scripts/quantization_config_smoke.py --method awq --bits 4 --fuse-max-seq-len 512
```

Expected success signal: `OK quantization config validated` plus a summary of the config class and options. Expected optional-dependency signal: `MISSING optional dependency` with install guidance. Expected validation failure: nonzero exit with `ERROR` and the invalid option.

## Output Expectations For Agent Answers

For quantization tasks, return the selected method, required packages, required hardware/backend, exact `quantization_config` or loading skeleton, `device_map`/offload decisions, PEFT/training/serving interaction notes, smoke-check command, expected success signals, and remaining risks such as calibration time, unsupported kernels, serialization limits, or checkpoint metadata mismatch.

## Optional Dependency Boundary

A base `transformers` import is not enough for real quantized model execution. Many config classes can be inspected or constructed without downloading a model, but model loading typically requires `torch`, `accelerate`, and the backend package. Missing dependencies commonly raise optional dependency `ImportError`s at class import, config validation, or model load time.
