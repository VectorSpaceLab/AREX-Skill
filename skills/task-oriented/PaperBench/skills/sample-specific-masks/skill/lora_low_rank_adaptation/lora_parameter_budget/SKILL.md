---
name: lora_parameter_budget
description: Compute LoRA trainable parameter budgets and reduction ratios for adapted Transformer projections.
---

# LoRA Parameter Budget

Use this skill to estimate how many task-specific parameters LoRA trains compared with full fine-tuning.

## Inputs
Projection dimensions or `d_model`, rank `r`, adapted matrix count, layer count, and optional full-parameter baseline.

## Outputs
Trainable LoRA count, dense-update count for the same matrices, and reduction ratios.

## Workflow
For square Transformer projections use the paper formula `2 * L_hat * d_model * r`, where `L_hat` counts adapted matrices. Compare against full dense updates `L_hat * d_model * d_model`.

## Validation
Run included tests for formula correctness and rank monotonicity.

## Limitations
This is an accounting skill; it does not measure wall-clock training throughput.
