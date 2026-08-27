---
name: openrlhf
description: "Use OpenRLHF for Ray/vLLM/DeepSpeed RLHF workflows, including
  dataset preparation, SFT/RM/DPO training, PPO-family RL and agent training,
  runtime operations, reward serving, LoRA merging, and troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# OpenRLHF

Use this repo skill when a user asks about OpenRLHF, a Ray + vLLM + DeepSpeed RLHF framework for supervised fine-tuning, reward modeling, preference optimization, PPO-family reinforcement learning, custom rewards, multi-turn agents, and distributed training operations.

OpenRLHF workflows are usually GPU/distributed and can trigger model downloads, Ray clusters, long training runs, or service processes. Prefer planning, validating, and generating commands first; run expensive operations only after confirming the user wants execution and the environment is ready.

## Fast Routing

- **Dataset schemas and validation**: use `sub-skills/data-preparation/` for SFT records, reward-model chosen/rejected pairs, DPO preferences, PPO prompt datasets, chat templates, mixed dataset probabilities, VLM image placeholders, and the bundled dataset validator.
- **SFT, reward-model, and DPO/IPO/cDPO training**: use `sub-skills/supervised-preference-training/` for `train_sft`, `train_rm`, `train_dpo`, LoRA/packing/DeepSpeed/checkpoint/logging flags, and safe command skeleton generation.
- **PPO, REINFORCE++, GRPO/RLOO, Ray/vLLM, custom rewards, and agents**: use `sub-skills/rl-agent-training/` for `train_ppo_ray`, hybrid engine placement, async rollout, single-turn reward functions, multi-turn agents, VLM agents, and OpenAI-compatible agent executors.
- **Installation, diagnostics, serving, LoRA merge, and utilities**: use `sub-skills/operations-and-utilities/` for dependency/runtime checks, CUDA/flash-attn/Ray/NCCL issues, reward-model serving, LoRA adapter merging, DeepSpeed checkpoint conversion, and Docker/system caveats.

## Start Safely

1. Identify the user’s target workflow: data preparation, supervised/preference training, RL/agent training, or runtime utility operations.
2. Check whether the request requires execution or only a plan, command, script, config review, or troubleshooting answer.
3. If execution is requested, classify safety first: local schema validation is usually safe; full training, Ray/vLLM startup, reward serving, Docker/NVIDIA setup, model downloads, and checkpoint conversion are expensive or stateful.
4. Route to the nearest sub-skill and read its linked references before giving detailed commands.
5. For cross-cutting failures, read `references/troubleshooting.md` and then the workflow-specific troubleshooting file in the owning sub-skill.

## Minimal Package Facts

- Distribution name: `openrlhf`.
- Import module: `openrlhf`.
- Version represented by this skill: `0.10.4`.
- Python requirement from packaging metadata: Python 3.10 or newer.
- Core dependency stack: PyTorch, Transformers, DeepSpeed, Ray, vLLM-related optional extras, flash-attn, datasets, PEFT/LoRA tooling, logging integrations, and CUDA-capable GPU infrastructure for realistic training.

A top-level `import openrlhf` only proves package metadata/import visibility. It does not prove CUDA, flash-attn, DeepSpeed, Ray, vLLM, model download, or distributed training readiness. Use the operations sub-skill for runtime checks.

## Common Workflows

- **Prepare SFT data**: route to `data-preparation`, validate keys and chat-template assumptions, then use `supervised-preference-training` to generate a `train_sft` command.
- **Train a reward model**: route to `data-preparation` for chosen/rejected pairs, use `supervised-preference-training` for `train_rm`, and use `operations-and-utilities` if the reward model will be served over HTTP.
- **Run DPO/IPO/cDPO**: route to `supervised-preference-training`; verify prompt/chosen/rejected fields through `data-preparation` first.
- **Run PPO or REINFORCE++ with Ray/vLLM**: route to `rl-agent-training`; use `operations-and-utilities` for Ray cluster, NCCL, CUDA, and vLLM runtime readiness.
- **Add custom reward or multi-turn agent logic**: route to `rl-agent-training` and generate a bundled template before adapting user logic.
- **Diagnose install or runtime failures**: route to `operations-and-utilities`; check optional dependency and GPU/backend status before changing training flags.

## References

- `references/repo-provenance.md`: source commit, package version, evidence paths, dirty-state notes, and refresh baseline.
- `references/troubleshooting.md`: cross-cutting install/import/backend/routing issues shared by all sub-skills.

## Boundaries

This skill is a self-contained guide distilled from repository source, docs, examples, scripts, and tests. Do not depend on the original checkout at runtime. If a user needs a reusable helper, use the bundled scripts under this skill or adapt their contents into the user’s project.

Do not run original OpenRLHF training examples or system scripts as smoke tests by default. Treat them as evidence for command shape unless the user explicitly asks to run them and the environment, GPUs, data, models, credentials, and time budget are suitable.
