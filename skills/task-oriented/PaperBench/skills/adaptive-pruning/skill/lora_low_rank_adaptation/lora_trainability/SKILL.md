---
name: lora_trainability
description: Freeze pretrained parameters and expose only LoRA task parameters for training or checkpointing.
---

# Lora Trainability

## When to use
Use this skill when adapting a model with LoRA and you must audit which parameters are trainable or stored. It defines a name-based contract compatible with LoRA papers: parameters containing lora_ are trainable; optional bias policies must be stated.

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
