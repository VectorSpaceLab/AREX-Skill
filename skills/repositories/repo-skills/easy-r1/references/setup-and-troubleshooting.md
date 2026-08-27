# EasyR1 Setup and Cross-Cutting Troubleshooting

## Purpose

Read this when installing or smoke-checking EasyR1, deciding whether a runtime is ready for full training, or diagnosing failures that span multiple sub-skills.

## Runtime facts

- Distribution/import package: `verl`.
- Python requirement: Python 3.9+.
- Project focus: efficient, scalable multimodal LLM reinforcement-learning post-training based on veRL, Ray, FSDP, and vLLM SPMD rollout.
- Supported model families documented by EasyR1: Llama3/Qwen2/Qwen2.5/Qwen3 language models, Qwen2-VL/Qwen2.5-VL/Qwen3-VL vision-language models, and DeepSeek-R1 distill models.
- Supported algorithms documented by EasyR1: GRPO, DAPO, Reinforce++, ReMax, RLOO, GSPO, CISPO, and SAPO-style loss options.
- Full training runtime requirements include CUDA GPUs, PyTorch, Ray, vLLM, flash-attn, transformers, model weights, datasets, and enough GPU memory for the selected model and batch settings.

## Recommended setup direction

For real training, use the EasyR1-maintained CUDA container or reproduce its package stack. The README recommends a prebuilt image in the `hiyouga/verl` Docker repository and an Apptainer path when Docker is unavailable. This matters because `flash-attn` and vLLM wheels must match Python, PyTorch, CUDA, GPU architecture, and compiler/toolkit constraints.

For CPU-safe inspection or scripting, it is acceptable to install only the package and the dependencies needed for API/config/data/checkpoint checks. Do not mistake that for training readiness.

## Safe environment check

Use the bundled root script:

```bash
python scripts/easyr1_env_check.py --json
```

It checks selected imports and, when PyTorch is installed, CUDA visibility and a tiny allocation. It does **not** start Ray, initialize vLLM, download models, run examples, or verify flash-attn compilation.

## Common install/import failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ModuleNotFoundError: flash_attn` or flash-attn build failure | Missing wheel for the current Python/PyTorch/CUDA combination, or no `nvcc`/`CUDA_HOME` for source build | Prefer the documented EasyR1 container or install a matching PyTorch + CUDA + flash-attn wheel/toolkit. Do not use CPU import checks as proof of training readiness. |
| `ModuleNotFoundError: vllm` | vLLM runtime not installed or version incompatible with the selected PyTorch/transformers stack | Install a vLLM version compatible with EasyR1 and PyTorch, or use the EasyR1 container. vLLM is required for full rollout/training paths. |
| `RuntimeError: CUDA out of memory` | Model too large, rollout memory too high, too many samples/images, insufficient offload | Reduce `worker.rollout.gpu_memory_utilization`, lower batch sizes, enable actor offload, reduce max pixels/tokens, use LoRA, or choose a smaller model. |
| `ValueError: Image features and image tokens do not match` | VL prompt/media mismatch or prompt too long for the configured image features | Increase `data.max_prompt_length`, reduce `data.max_pixels`, verify `<image>` placeholders match `images`, and use the data/rewards sub-skill. |
| `RuntimeError: 0 active drivers ([]). There should only be one.` | Conflicting DeepSpeed/Ray/accelerator driver state; README specifically notes `deepspeed` conflict | Remove conflicting `deepspeed` from the runtime when using EasyR1's Ray/FSDP/vLLM stack unless you intentionally maintain a separate stack. |
| Ray reports insufficient resources or idle workers | Wrong `trainer.n_gpus_per_node`, `trainer.nnodes`, Ray head/worker setup, or scheduler placement issue | Check `ray status`; in multi-node jobs start the head, connect workers, and run training from the head only. |
| `USE_MODELSCOPE_HUB=1` raises import error | ModelScope hub patch requested but `modelscope` is not installed | Install `modelscope` or unset `USE_MODELSCOPE_HUB`. |
| WandB/SwanLab/MLflow errors | Logger selected without credentials or package/service setup | Use `trainer.logger=["console"]` or configure credentials/packages before enabling remote loggers. |

## Hardware planning reminders

EasyR1's README gives estimated GPU memory needs. Examples include GRPO full fine-tuning and LoRA fine-tuning across 1.5B, 3B, 7B, 32B, and 72B models. Treat those as planning estimates, not guarantees. VL models, larger images, longer responses, higher rollout `n`, tensor parallel settings, and online filtering can increase memory and runtime.

When using this skill to author commands, always record what is verified:

- Static config or command validation: CPU-safe, no training proof.
- Package/API import checks: useful for data/reward/core/checkpoint tasks, not full training proof.
- CUDA tensor allocation: proves PyTorch sees GPUs, not vLLM/flash-attn training readiness.
- Full native training example: requires explicit user approval, model/dataset access, runtime provisioning, and enough time/GPU memory.

## Where to go next

- Training config and launch issues: [../sub-skills/training-workflows/SKILL.md](../sub-skills/training-workflows/SKILL.md).
- Data row, prompt template, or reward function issues: [../sub-skills/data-and-rewards/SKILL.md](../sub-skills/data-and-rewards/SKILL.md).
- `DataProto`, dynamic batching, or algorithm tensor issues: [../sub-skills/core-apis/SKILL.md](../sub-skills/core-apis/SKILL.md).
- Actor checkpoint merge/export issues: [../sub-skills/checkpoint-export/SKILL.md](../sub-skills/checkpoint-export/SKILL.md).
