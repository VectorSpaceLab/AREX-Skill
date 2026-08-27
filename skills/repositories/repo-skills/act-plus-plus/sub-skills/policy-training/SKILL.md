---
name: policy-training
description: "Routes ACT, CNNMLP, Diffusion Policy, and latent-model training or
  evaluation workflows for ACT++ checkpoints and datasets."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# policy-training

Use this sub-skill when the task is about training or evaluating ACT++, CNNMLP, Diffusion Policy, or the VQ latent model that follows ACT training.

## Typical triggers

- "Train ACT on sim_transfer_cube_scripted"
- "Evaluate the best checkpoint"
- "Why does policy.py fail to import?"
- "What does --temporal_agg do?"
- "How do I run the latent model training pass?"

## What this sub-skill covers

- Step-based training and evaluation through the `imitate_episodes` workflow.
- ACT, CNNMLP, and Diffusion policy wrappers.
- The DETR-derived backbone / transformer / latent model internals that drive those wrappers.
- Dataset loading, normalization, and evaluation statistics.
- VQ latent model training from a previously trained ACT checkpoint.

## What it excludes

- Simulated data generation, replay, and rendering -> [simulation-data](../simulation-data/SKILL.md).
- VINN feature cache and k-selection -> [vinn-offline](../vinn-offline/SKILL.md).
- Real robot deployment or ROS/servo control -> root troubleshooting only.
- Experimental actuator-network training with hard-coded paths -> reference-only note only.

## Read these first

- [Workflow recipes](references/workflows.md)
- [Model overview](references/model-overview.md)
- [Troubleshooting](references/troubleshooting.md)
- [API reference](../../references/api-reference.md)
- [Data formats](../../references/data-formats.md)

## Run this helper first

Before trying to train, use [check_policy_stack.py](scripts/check_policy_stack.py) to confirm the repo checkout imports, the CUDA backend is visible, and the policy wrapper surface is present.
