---
name: visual_pgd_prompt_optimizer
description: Optimize continuous visual prompt vectors with projected gradient descent and auditable constraint diagnostics.
---

# Visual PGD Prompt Optimizer

Use this skill when reconstructing the visual adversarial example mechanism from the paper: a frozen model receives a trainable visual input, the visual input is optimized against target text/corpus loss, and optional `L_inf` projection keeps the adversarial prompt near a benign image. This skill is safe for tiny surrogate losses and does not require real VLM weights.

## Inputs

- `initial`: numeric vector representing the benign visual prompt.
- `target`: numeric vector or target direction for a differentiable surrogate objective.
- PGD parameters: `steps`, `step_size`, optional `epsilon`, and optional bounds.
- A caller-provided loss/gradient function, or the built-in quadratic surrogate.

## Outputs

- `params_before` and `params_after` for validation-compatible traces.
- `loss_before`, `loss_after`, and full `losses` trajectory.
- Constraint diagnostics including maximum `L_inf` distance from the initial vector.

## Workflow

1. Keep model/surrogate parameters fixed; update only the visual vector.
2. Compute gradients of the configured loss with respect to the visual vector.
3. Take signed or direct gradient-descent steps.
4. Project the vector into the `L_inf` ball when `epsilon` is provided.
5. Record loss and parameter changes so recovery can prove that optimization actually ran.

## Validation

Run:

```bash
python scripts/pgd_optimizer.py --self-test
```

The tests verify loss decrease, parameter changes, and projection under an `L_inf` constraint.

## Limitations

The built-in objective is a deterministic proxy for recovery. Full paper reproduction requires a VLM likelihood loss and model-specific image preprocessing.
