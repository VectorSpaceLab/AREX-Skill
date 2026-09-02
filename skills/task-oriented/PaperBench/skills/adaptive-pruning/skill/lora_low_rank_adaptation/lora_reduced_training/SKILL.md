---
name: lora_reduced_training
description: Run a bounded LoRA-only optimization loop and log mechanism-faithful training evidence.
---

# Lora Reduced Training

## When to use
Use this skill when full model training is blocked but a reduced, mechanism-faithful LoRA optimizer step is needed. It consumes tiny supervised examples, updates only A/B, records before-after parameters, and verifies frozen base weights.

## Inputs
- Base matrix or named parameters relevant to the module.
- LoRA rank `r`, scaling `alpha`, and small task examples when training or evaluation is needed.

## Outputs
- Deterministic JSON-serializable mechanism checks.
- Updated LoRA parameters or validation metrics, depending on the module.

## Workflow
1. Keep pretrained/base weights immutable unless explicitly performing a merge copy for inference.
2. Represent the adaptation as `delta_W = (alpha / r) * B @ A`.
3. Verify that only LoRA matrices are treated as task-specific trainable parameters.
4. For recovery, log rank, loss before and after, parameter changes, and merge equivalence.

## Validation
Run `python -m pytest tests` or validate the skill tree with the Distiller module-to-skill validator. The included tests use only the Python standard library.

## Limitations
This skill provides the reusable mechanism; full paper benchmark scores still require real pretrained models, datasets, and training infrastructure.
