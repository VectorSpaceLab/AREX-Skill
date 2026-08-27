---
name: easy-r1
description: "Use EasyR1 for multimodal LLM RL post-training, dataset/reward
  preparation, core API debugging, and checkpoint export workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# EasyR1

Use this repo skill when a task names **EasyR1**, the `verl` package from EasyR1, or a multimodal LLM RL/post-training workflow that looks like EasyR1: GRPO/DAPO/Reinforce++/ReMax/RLOO/GSPO/CISPO/SAPO training, Ray + FSDP + vLLM rollout, Qwen/Qwen-VL post-training, EasyR1 reward functions, EasyR1 checkpoint merging, or `DataProto` debugging.

This skill is self-contained operating guidance distilled from the EasyR1 repository. It does not require reopening the repository checkout. Full training still requires an EasyR1-compatible CUDA runtime with Ray, vLLM, flash-attn, model weights, datasets, and enough GPU memory.

## First checks

- Read [references/repo-provenance.md](references/repo-provenance.md) before deciding whether this skill is current for a checkout or whether to refresh it.
- Read [references/setup-and-troubleshooting.md](references/setup-and-troubleshooting.md) for install/runtime choices, Docker/container guidance, CUDA/vLLM/flash-attn limits, and common cross-cutting failures.
- Run [scripts/easyr1_env_check.py](scripts/easyr1_env_check.py) when you need a safe local environment/import/backend check. It does not start Ray, download models, or run training.

## Route by task

### Training workflows

Load [sub-skills/training-workflows/SKILL.md](sub-skills/training-workflows/SKILL.md) when the task is to configure, lint, explain, or launch `python -m verl.trainer.main` jobs. It covers EasyR1 config hierarchy, OmegaConf CLI overrides, algorithms and loss types, Ray/FSDP/vLLM runtime assumptions, LoRA, logging, validation, checkpoint save/resume, multi-node setup, and training troubleshooting.

Typical triggers:

- "Run EasyR1 GRPO/DAPO/GSPO/CISPO/SAPO on my dataset."
- "Build or validate an EasyR1 config."
- "Convert an example shell launch to a safer command."
- "Explain `worker.rollout.tensor_parallel_size`, `algorithm.online_filtering`, LoRA, or GPU memory settings."

### Data and rewards

Load [sub-skills/data-and-rewards/SKILL.md](sub-skills/data-and-rewards/SKILL.md) when the task is about dataset rows, prompt templates, image/video columns, reward functions, `worker.reward.reward_function`, batch/sequential reward modes, DAPO overlong penalties, R1-V/math/Android GUI reward patterns, or validating reward outputs.

Typical triggers:

- "Prepare a custom text/VL dataset for EasyR1."
- "Write an EasyR1 reward function with `overall`, `accuracy`, or `accuracy_normalized`."
- "Debug image-token mismatch, overlong prompts, or missing reward keys."

### Core APIs

Load [sub-skills/core-apis/SKILL.md](sub-skills/core-apis/SKILL.md) when the task involves EasyR1 support APIs rather than a full job launch: `DataProto`, tensor/non-tensor batches, padding/unpadding, dynamic sequence-length batching, `compute_policy_loss`, advantage/KL helpers, logger/tracker helpers, or native CPU API smoke checks.

Typical triggers:

- "Debug a `DataProto.union` or chunk/split error."
- "Use EasyR1 core algorithm functions directly."
- "Explain dynamic batching restore order or GRPO grouped rollout assertions."

### Checkpoint export

Load [sub-skills/checkpoint-export/SKILL.md](sub-skills/checkpoint-export/SKILL.md) when the task is to inspect EasyR1 actor checkpoint directories or convert actor shards to Hugging Face format. It covers `model_world_size_<N>_rank_<R>.pt` shard patterns, the `huggingface/` metadata directory, generation config preservation, LoRA merge requirements, upload caveats, and safe preflight inspection.

Typical triggers:

- "Merge an EasyR1 actor checkpoint to Hugging Face format."
- "Preflight a checkpoint before running the model merger."
- "Explain missing rank shards, unsupported DTensor placement, or LoRA base-model errors."

## Minimal install/import shape

For users setting up EasyR1 itself, prefer the project-documented CUDA container or an equivalent Python 3.9+ environment with compatible PyTorch, Ray, vLLM, flash-attn, transformers, and model/dataset access. A minimal import check is:

```bash
python - <<'PY'
import verl
from verl.protocol import DataProto
from verl.trainer.core_algos import compute_kl
print("verl", getattr(verl, "__version__", "unknown"))
print("DataProto", DataProto.__name__)
print("compute_kl", compute_kl.__name__)
PY
```

If `flash_attn`, `vllm`, CUDA, or Ray imports fail, use the setup/troubleshooting reference before treating EasyR1 training as ready. CPU-safe API checks do not prove the full training runtime.

## Boundaries

Do not use this skill as a generic TRL/OpenRLHF/LlamaFactory manual. Use it when EasyR1-specific config keys, scripts, dataset/reward contracts, `verl` APIs, or checkpoint layout matter. For ordinary supervised fine-tuning or inference workflows that EasyR1 explicitly does not provide, route to a more suitable LLM fine-tuning or serving skill.
