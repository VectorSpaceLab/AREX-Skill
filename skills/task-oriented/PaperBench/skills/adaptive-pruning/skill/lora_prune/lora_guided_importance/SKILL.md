---
name: lora_guided_importance
description: Compute LoRAPrune's LoRA-gradient-only Taylor importance estimate for structured pruning without frozen base-weight gradients.
---

# LoRA-Guided Importance

Use this skill when implementing or checking LoRAPrune-style pruning criteria for a LoRA-adapted linear module. Do not use it for ordinary magnitude pruning or for methods that explicitly require gradients of the frozen pretrained weights.

## Inputs

- `W0`: frozen base matrix shaped `(d, k)`.
- `B`: LoRA matrix shaped `(d, r)`.
- `A`: LoRA matrix shaped `(r, k)`.
- `grad_B` and `grad_A`: gradients from the current calibration batch.

The contract deliberately has no `grad_W0` input.

## Outputs

- Elementwise nonnegative importance matrix shaped like `W0`.
- Diagnostics with `uses_base_gradients: false` and shape/rank metadata.

## Workflow

1. Validate all matrix dimensions and reject accidental broadcasting.
2. Compute `BA = B @ A`.
3. Approximate `dL/d(BA)` as `grad_B @ A + B @ grad_A - grad_B @ grad_A`.
4. Return `((approx_grad) * (W0 + BA)) ** 2` elementwise.
5. Pass the importance matrix to a structured grouping skill; do not threshold individual weights here.

## Validation

Run:

```bash
python /share/project/yuyang/workspace/Paper2Skills/Distiller/skills/module-to-skill/scripts/validate_skill_tree.py <this_skill_dir> --run-tests
```

The included tests verify the exact formula, zero-gradient behavior, and shape mismatch handling.

## Limitations

This skill implements the criterion, not the whole pruning loop. It assumes a dense matrix representation in small examples; large model implementations should call the same formula on tensor backends while preserving the no-base-gradient invariant.
