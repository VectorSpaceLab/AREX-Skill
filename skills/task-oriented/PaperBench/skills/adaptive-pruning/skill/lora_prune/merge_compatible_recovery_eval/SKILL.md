---
name: merge_compatible_recovery_eval
description: Evaluate LoRAPrune recovery metrics while verifying structured-mask LoRA merge compatibility and mechanism checks.
---

# Merge-Compatible Recovery Evaluation

Use this skill at the end of a LoRAPrune recovery run to show that the pruned LoRA model can be represented as merged masked weights. Do not accept a proxy recovery on metric value alone; it must include merge and structured-mask mechanism checks.

## Inputs

- Frozen base weights `W0`.
- Trained LoRA matrices `B` and `A`.
- Structured group mask.
- Evaluation inputs and labels.
- Optional baseline metric at the same sparsity.

## Outputs

- Merged and masked weights.
- Numeric evaluation loss or equivalent metric.
- Relative improvement versus a baseline when provided.
- Mechanism checks: structured mask applied, merge equivalence checked, maximum merge difference, and no dense unstructured mask.

## Workflow

1. Compute `W = W0 + B @ A`.
2. Apply the structured mask to complete output/input groups, not individual random elements.
3. Compare merged inference against explicit LoRA inference with the same structured mask.
4. Compute the evaluation metric on held-out examples.
5. Emit mechanism checks and fail downstream validation if merge equivalence or structured pruning is absent.

## Validation

Run:

```bash
python /share/project/yuyang/workspace/Paper2Skills/Distiller/skills/module-to-skill/scripts/validate_skill_tree.py <this_skill_dir> --run-tests
```

The tests verify merge formula correctness, structured-mask evidence, and explicit-vs-merged equivalence.

## Limitations

The script implements a small matrix proxy. For transformer recovery, the same evidence must be recorded per pruned projection/head/channel and the final adapter should not require dense unstructured residual computation.
