---
name: training-workflows
description: "Construct, audit, and adapt VLM-R1 GRPO training launches for
  QwenVL, InternVL, LoRA, freeze-vision, DeepSpeed, and multi-node runs."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# VLM-R1 training workflows

Use this sub-skill when a user needs to build, review, or modify a VLM-R1 GRPO training launch. It covers command construction, trainer/config flags, distributed launch choices, and training-specific failure diagnosis.

## Route here for

- JSONL-driven GRPO launches with `grpo_jsonl.py` for REC, GUI or other task types.
- Qwen2-VL, Qwen2.5-VL, and InternVL command variants.
- Full fine-tuning, LoRA, `freeze_vision_modules`, and gradient checkpointing choices.
- DeepSpeed ZeRO-2, ZeRO-3, and ZeRO-3-offload command wiring.
- `torchrun` single-node and multi-node command construction.
- Training-specific CUDA, FlashAttention, DeepSpeed, W&B, data-path, and rendezvous troubleshooting.

## Route elsewhere

- JSONL schema details, answer/reward formats, bbox scoring, and reward-method selection: `../data-and-rewards/SKILL.md`.
- VLM module internals, adding a new model family, and Qwen/InternVL processor behavior: `../model-modules/SKILL.md`.
- REC/OVD evaluation or scoring saved model outputs: `../evaluation/SKILL.md`.
- Huawei Ascend inference or serving: `../ascend-inference/SKILL.md`.
- LLaMA-Factory SFT: treat as an external alternative, not a VLM-R1 GRPO launch path.

## Operating workflow

1. Identify the task family, model family, GPU topology, DeepSpeed mode, and logging policy.
2. Validate that `data_file_paths`, `image_folders`, and optional `reward_method` lists have matching colon-separated lengths.
3. Pick a baseline recipe from `references/grpo-training-workflows.md` and adapt only the required knobs.
4. Use `scripts/launch_grpo_jsonl.sh` to render or execute a checked single-node command. Default to dry-run preview before a long training job.
5. For multi-node runs, use `scripts/render_multinode_torchrun.py` to render one command per node and validate the host map before launch.
6. Check `references/configuration-reference.md` for flag semantics and trainer constraints, especially global-batch divisibility by `num_generations`.
7. If the launch fails before useful training starts, diagnose with `references/troubleshooting.md` before changing model code or data.

## Bundled files

- `references/grpo-training-workflows.md` - recipes and adaptation patterns.
- `references/configuration-reference.md` - distilled CLI/trainer/DeepSpeed/torchrun flag reference.
- `references/troubleshooting.md` - training-specific failure triage.
- `scripts/launch_grpo_jsonl.sh` - safe parameterized GRPO command renderer/launcher.
- `scripts/render_multinode_torchrun.py` - validated multi-node command renderer.

## Safety defaults

- Prefer command rendering and static validation before launching full training.
- Do not assume datasets, checkpoints, W&B credentials, or multi-node rendezvous are present.
- Do not claim full native training verification from script syntax checks alone.
- Keep user-provided paths out of reusable notes unless they are rewritten as placeholders or parameters.
