---
name: post-training-rlhf
description: "Guide the train-llm-from-scratch post-training alignment pipeline:
  SFT, reward modeling, DPO/ORPO/KTO, PPO, GRPO/RLVR, rollout/log-prob
  mechanics, metrics, and troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Post-Training RLHF Router

Use this sub-skill when the task is about turning a pretrained base checkpoint into aligned instruction/reasoning checkpoints with this repo's from-scratch post-training stack.

## Use this for

- Running or debugging SFT, reward-model training, DPO/ORPO/KTO, PPO, and GRPO/RLVR stages.
- Understanding masked SFT loss, Bradley-Terry reward modeling, preference objectives, PPO GAE/clipping/KL, GRPO group-relative advantages, rollout generation, log-prob recomputation, and verifier rewards.
- Planning checkpoint/data dependencies across `base_pretrained.pt -> sft.pt -> reward.pt / dpo.pt / ppo.pt / grpo.pt`.
- Interpreting stage JSONL metrics and deciding safe recovery actions.
- Building dry-run stage commands before launching expensive training.

## Route elsewhere

- Prepare or validate raw Pile/SFT/preference/RL prompt files: `../data-preparation/SKILL.md`.
- Pretrain the base Transformer or inspect model architecture: `../model-pretraining/SKILL.md`.
- Run GSM8K table evaluation, parse answers for evaluation, or chat with a checkpoint: `../evaluation-chat/SKILL.md`.
- Edit config files through forms, use the Streamlit UI, or explain config merge precedence: `../configuration-ui/SKILL.md`.

## Fast operating path

1. Identify the requested stage and verify its upstream checkpoint/data dependencies with [references/stage-workflows.md](references/stage-workflows.md).
2. Use [scripts/build_stage_command.py](scripts/build_stage_command.py) or [scripts/plan_posttraining_pipeline.py](scripts/plan_posttraining_pipeline.py) to print a dry-run command. Inspect it before running anything expensive.
3. For algorithm-specific questions, use [references/algorithm-reference.md](references/algorithm-reference.md) to map metrics and function names to the underlying loss/reward/log-prob mechanics.
4. For failures, start with [references/troubleshooting.md](references/troubleshooting.md), then route to data/model/eval/UI sub-skills when the root cause is outside post-training.
5. Inspect JSONL metrics with [scripts/inspect_metrics_jsonl.py](scripts/inspect_metrics_jsonl.py) before changing hyperparameters; prefer the smallest recovery that matches the observed metric failure.

## Safety and scope notes

- The bundled scripts are dry-run or read-only helpers. They do not download data, train, delete checkpoints, or modify configs.
- Training commands assume the user is in their own repo checkout or compatible workspace and has already prepared data/checkpoints.
- Keep log-prob math in fp32 when comparing policy/reference/old log-probs; do not "optimize" this away under bf16.
- Treat Weights & Biases as optional. JSONL metrics are the source of truth.
