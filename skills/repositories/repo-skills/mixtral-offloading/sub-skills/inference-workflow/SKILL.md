---
name: inference-workflow
description: "Adapt mixtral-offloading's notebook evidence into safe local
  offloaded Mixtral inference workflows."
metadata:
  disco-role: operating
disable-model-invocation: true
license: MIT
---

# Inference Workflow

Use this sub-skill when the task is to run, script, adapt, or troubleshoot the
Mixtral offloading demo workflow: building an offloaded `MixtralForCausalLM`
from quantized safetensors, choosing offload sizes, and generating chat text.

## Read this when

- The user asks to turn the demo notebook into a Python script.
- The task mentions `OffloadConfig`, `QuantConfig`, `build_model`,
  `offload_per_layer`, or a quantized Mixtral state directory.
- The user needs to balance GPU VRAM, system RAM, and generation speed.
- A local run fails before or during model construction or generation.

## Route map

1. Read [references/workflow.md](references/workflow.md) for the full
   notebook-to-script recipe, validation gates, and generation-loop outline.
2. Read [references/configuration.md](references/configuration.md) when the task
   is about offload sizing, HQQ quantization settings, or memory trade-offs.
3. Use [scripts/create_offload_config.py](scripts/create_offload_config.py) to
   compute `main_size`, `offload_size`, and `buffer_size` from layer/expert
   counts without importing the repository.
4. Use [scripts/render_generation_skeleton.py](scripts/render_generation_skeleton.py)
   to render a safe starter script that shows where to call `build_model`
   without downloading weights or executing the model.
5. Read [references/troubleshooting.md](references/troubleshooting.md) for
   state-path, CUDA, memory, HQQ config, tokenizer, and generation-cache errors.

## What this sub-skill owns

- Runtime prerequisites specific to offloaded inference after the repository
  dependencies are installed.
- State directory checks for `model.safetensors.index.json` and safetensors
  weight-map keys used by `build_model`.
- The notebook's model setup pattern: tokenizer, quant configs, `OffloadConfig`,
  `build_model`, streamer, sampling parameters, and cached generation.
- Memory and speed trade-offs for `offload_per_layer`.

## What to route elsewhere

- Use the root [../../references/installation-and-runtime.md](../../references/installation-and-runtime.md)
  for source-only installation, `PYTHONPATH`, and package import checks.
- Use [../quantization-kernels/SKILL.md](../quantization-kernels/SKILL.md) for
  HQQ layer internals, packing functions, and Triton kernel errors.
- Use [../expert-cache/SKILL.md](../expert-cache/SKILL.md) for LRU expert-cache,
  storage, and SparseMoeWrapper internals.

## Minimal decision flow

1. Confirm the user has a CUDA-capable PyTorch runtime for actual inference.
   CPU-only checks can validate imports and config math, but not the advertised
   offloaded generation path.
2. Confirm the quantized state path is local and contains a Hugging Face
   safetensors index. Do not start a large network download unless the user
   explicitly asks.
3. Compute `offload_per_layer` and derived cache sizes from the model config.
4. Build the quantization configs exactly before calling `build_model`.
5. Keep generation code explicit about `attention_mask` and `past_key_values`
   if continuing multi-turn chat.

## Verification expectations

Safe checks are `--help` on the bundled scripts and dry-run config rendering.
Full Mixtral generation requires large external model artifacts and a CUDA GPU;
classify it as an approved native run only when the user accepts downloads,
memory use, and runtime cost.
