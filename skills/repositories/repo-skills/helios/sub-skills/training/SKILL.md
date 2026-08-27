---
name: training
description: "Route Helios Stage 1, Stage 2, Stage 3 training and config workflows."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# Training

Use this sub-skill when the user needs to configure, validate, launch, resume,
or debug Helios training.

## Typical triggers

- "train Helios"
- "fine-tune the model"
- "run Stage 1/2/3"
- "validate this YAML config"
- "use DeepSpeed or DDP"
- "resume from checkpoint"
- "merge a LoRA checkpoint"

## What this sub-skill covers

- Stage 1 architectural adaptation workflows.
- Stage 2 pyramid/token-compression workflows.
- Stage 3 distilled, ODE, GAN, and self-forcing variants.
- YAML config groups and common invariants.
- DDP versus DeepSpeed launch decisions.
- Checkpoint and LoRA handling at the workflow level.

## What it does not own

- Raw video metadata validation belongs in `data-preparation`.
- Running the final generation/demo path belongs in `inference`.
- The metric benchmark suite is outside this generated runtime graph.

## Read next

- `references/workflows.md` for stage selection and launch order.
- `references/configuration.md` for config groups and invariant checks.
- `references/troubleshooting.md` for training-specific failures.
- `scripts/validate_train_config.py` for a safe preflight check.
- `scripts/compare_configs.py` for comparing two YAML configs.

## Working rule

Do not begin an expensive training run until the config, data layout, backend,
and checkpoint paths have all been validated.
