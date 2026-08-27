---
name: post-training-rl-and-multimodal
description: "Route optional Megatron ModelOpt, RL/GRPO, VLM, and
  multimodal/MIMO workflows with explicit dependency and hardware limits."
metadata:
  disco-role: operating
disable-model-invocation: true
license: NOASSERTION
---

# post-training-rl-and-multimodal

Use this sub-skill for ModelOpt quantization/pruning/distillation/export, Megatron RL/GRPO, VLM, audio/video, and MIMO workflows. These surfaces are optional and usually need more than the minimal Megatron Core install.

## Read first

- For ModelOpt and post-training operations, read [references/post-training-workflows.md](references/post-training-workflows.md).
- For RL/GRPO concepts, rollout/inference handles, packed data, and configs, read [references/rl-workflows.md](references/rl-workflows.md).
- For VLM/multimodal/MIMO data and model-provider boundaries, read [references/multimodal-workflows.md](references/multimodal-workflows.md).
- For missing optional packages, data/checkpoint mismatch, GPU memory, and config failures, read [references/troubleshooting.md](references/troubleshooting.md).

## Route by task

| Task | Route |
|---|---|
| Quantize/prune/export a model | Confirm ModelOpt install, checkpoint/model compatibility, and target artifact before running. |
| Run GRPO/RL post-training | Confirm reward/environment configs, rollout backend, packed sequence schema, and GPU topology. |
| Train a VLM/MIMO model | Confirm media manifest/schema, encoder/model-provider, tokenizer, and heterogeneous topology. |
| Only run a standard GPT pretrain | Route to [../training-cli-and-data/SKILL.md](../training-cli-and-data/SKILL.md). |
| Missing ModelOpt/vision/audio dependency | Route to [../install-and-environment/SKILL.md](../install-and-environment/SKILL.md) for a minimal extra install; do not install all dev deps blindly. |

## Safety

- Do not start long RL training, model conversion, or server processes as a probe.
- Use `--help`, import checks, and tiny mock fixtures first.
- Treat external reward services, HF tokens, media datasets, and model checkpoints as user-provided resources; never embed credentials.
- Expect H100/Blackwell and large-memory assumptions for many current examples; document unverified hardware rather than substituting a CPU check.

## Boundaries

- Core model/topology decisions belong to [../core-models-and-parallelism/SKILL.md](../core-models-and-parallelism/SKILL.md).
- Generic environment and optional dependency installation belongs to [../install-and-environment/SKILL.md](../install-and-environment/SKILL.md).
- Checkpoint format/conversion belongs to [../checkpointing-and-conversion/SKILL.md](../checkpointing-and-conversion/SKILL.md).
