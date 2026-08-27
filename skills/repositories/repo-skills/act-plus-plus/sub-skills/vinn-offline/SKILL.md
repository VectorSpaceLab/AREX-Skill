---
name: vinn-offline
description: "Routes VINN feature caching and non-interactive k-selection
  workflows for ACT++ BYOL/ResNet episode features."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# vinn-offline

Use this sub-skill when the task is about caching image features for VINN or choosing a k value from cached episode features.

## Typical triggers

- "Cache BYOL features for the simulated cube dataset"
- "Choose k for VINN"
- "How are feature files named?"
- "Why does the raw k-selection script stop in IPython?"

## What this sub-skill covers

- Feature caching from per-camera ResNet18 checkpoints.
- Feature-file naming and layout for simulated and cotrain variants.
- Offline nearest-neighbor k selection over cached features.
- CUDA requirements and dataset-index assumptions for VINN preprocessing.

## What it excludes

- ACT/CNNMLP/Diffusion training and eval -> [policy-training](../policy-training/SKILL.md).
- Simulation episode generation / replay / visualization -> [simulation-data](../simulation-data/SKILL.md).
- Real-robot VINN deployment -> root troubleshooting only.

## Read these first

- [Workflow recipes](references/workflows.md)
- [Troubleshooting](references/troubleshooting.md)
- [Data formats](../../references/data-formats.md)

## Run this helper first

Before a long cache or k-selection job, use [check_vinn_stack.py](scripts/check_vinn_stack.py) to confirm the repo checkout imports and the CUDA backend is visible.
