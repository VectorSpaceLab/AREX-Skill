---
name: booster-training
description: "Use ColossalAI Booster, plugins, dataloaders, checkpointing, LoRA,
  ZeRO/Gemini, and memory-aware training loops."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Booster Training

Use this sub-skill when the task is to adapt a PyTorch training script to ColossalAI, choose a Booster plugin, build a distributed dataloader, call `booster.backward`, save/load checkpoints, enable LoRA, or diagnose ZeRO/Gemini training behavior.

## Route Here

- Choose among `TorchDDPPlugin`, `LowLevelZeroPlugin`, `GeminiPlugin`, `HybridParallelPlugin`, `TorchFSDPPlugin`, or `MoeHybridParallelPlugin`.
- Write or review a `Booster(plugin=...)` training loop.
- Use `plugin.prepare_dataloader`, `booster.boost`, `booster.backward`, `booster.execute_pipeline`, and optimizer step ordering.
- Save/load model, optimizer, and scheduler checkpoints, including sharded and safetensors variants.
- Enable LoRA or bitsandbytes-aware LoRA through Booster when the required optional dependencies are installed.
- Tune memory behavior with ZeRO stage, Gemini placement/offload, lazy initialization, mixed precision, gradient accumulation, and gradient clipping.

## Reroute

- Installing PyTorch/CUDA or launching processes: use `../installation-and-launch/SKILL.md` first.
- Tensor/pipeline/sequence topology theory and ShardFormer policies: use `../parallelism-and-sharding/SKILL.md`.
- Colossal-Inference generation or serving: use `../inference-and-serving/SKILL.md`.
- ColossalChat/Colossal-LLaMA application commands: use `../application-recipes/SKILL.md`.

## Fast Start

```python
import colossalai
colossalai.launch_from_torch(seed=42)
```

For a first CUDA smoke, use `TorchDDPPlugin`. For optimizer-state and gradient sharding, use `LowLevelZeroPlugin`. For ZeRO-3-style memory management, use `GeminiPlugin`. For tensor/pipeline/data parallel combinations, use `HybridParallelPlugin`.

## References and Helpers

- `references/booster-api.md` lists the core Booster workflow and inspected method signatures.
- `references/plugin-guide.md` maps user goals to plugin choices and constructor knobs.
- `references/gemini-zero-and-checkpointing.md` covers ZeRO/Gemini memory controls, checkpoints, LoRA, and optional async save.
- `references/troubleshooting.md` maps common training failures to checks and fixes.
- `scripts/plugin_decision_helper.py` suggests a plugin from safe command-line requirements.
- `scripts/booster_loop_template.py` prints a self-contained minimal Booster training skeleton.

## Operating Rules

- Do not call `loss.backward()` in a Booster-managed loop unless a specific plugin path explicitly permits it; use `booster.backward`.
- Do not construct GPU plugins before distributed initialization.
- Treat `enable_flash_attention`, fused normalization, FP8, Apex, TensorNVMe, and application-specific extras as optional until installed and tested.
- Validate a one-process or tiny synthetic case before long model training.
