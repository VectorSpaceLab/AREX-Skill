---
name: lora_training_step
description: Run a deterministic reduced LoRA training step that updates only low-rank factors and records loss evidence.
---

# LoRA Reduced Training Step

Use this skill when full pretrained model training is blocked but soft-mode recovery permits a mechanism-faithful reduced experiment. It executes an actual optimizer update on LoRA factors over supervised examples. Do not call this a full GLUE, GPT-2, or pretrained-model reproduction.

## Inputs
- Synthetic or resource-derived supervised examples.
- Frozen base weight matrix and LoRA A/B matrices.
- Learning rate, alpha scale, and number of bounded update steps.

## Outputs
- `loss_before` and `loss_after`.
- `params_before` and `params_after` with changed LoRA factors and unchanged base weights.
- Merge-equivalence diagnostics for the trained adapter.

## Workflow
1. Construct examples that expose a task update missing from the frozen base model.
2. Compute predictions with `W0 x + (alpha/r) B A x`.
3. Backpropagate mean-squared error analytically into A and B only.
4. Update A and B with a bounded deterministic gradient step and keep W0 unchanged.
5. Save validator-compatible traces with before/after losses and parameters.

## Validation
Run `python scripts/reduced_training.py --output /tmp/trace.json` or the included tests. The test requires loss reduction, changed LoRA factors, unchanged base weights, and merged inference equivalence.

## Limitations
This is a reduced standard-library proxy for the LoRA mechanism, not training of RoBERTa, DeBERTa, GPT-2, or GPT-3.
