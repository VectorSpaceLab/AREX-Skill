---
name: lora_linear_adapter
description: Create and validate low-rank LoRA adapters for linear layers with merge-equivalent inference.
---

# Lora Linear Adapter

## When to use
Use this skill when a future recovery or implementation needs the exact LoRA linear-layer mechanism: frozen W, rank-r matrices A and B, alpha/r scaling, zero-output initialization via B=0, and merge/unmerge equivalence. Do not use it as evidence of full language-model quality by itself.

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
