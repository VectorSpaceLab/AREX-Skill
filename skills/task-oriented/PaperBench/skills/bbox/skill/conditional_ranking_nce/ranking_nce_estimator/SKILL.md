---
name: ranking_nce_estimator
description: Optimize finite ranking NCE objectives and recover conditional distributions when partition functions vary by input.
---

# Ranking NCE Estimator

Use this skill when a recovery needs the ranking objective from conditional NCE. It computes the paper's candidate-set objective and can optimize a small finite protocol without relying on an original implementation repository.

Do not use this skill for binary data-vs-noise NCE; use `binary_nce_estimator` for that objective.

## Inputs

- A `ConditionalNCEProtocol` from `conditional_nce_protocol`.
- A score function or the built-in Section 4.3 two-parameter score.
- Candidate events from exact enumeration or sampled data.
- Bounded optimizer settings.

## Outputs

- Ranking objective value.
- Estimated conditionals after score normalization over labels.
- Optimizer trace with parameters, loss values, and ratio diagnostics.
- Candidate posterior normalization checks.

## Workflow

1. Compute adjusted scores `bar_s=s-log p_N`.
2. For each event, form a `(K+1)`-way softmax over the positive candidate and all negative candidates.
3. Accumulate the expected log probability of the positive candidate.
4. Normalize scores over the complete label set to produce `p_hat(y|x)`.
5. In reduced recovery, optimize the Section 4.3 population objective and verify the `x1` ratio approaches `1/3`.

## Validation

Run:

```bash
python /share/project/yuyang/workspace/Paper2Skills/Distiller/skills/module-to-skill/scripts/validate_skill_tree.py . --run-tests
```

The tests check objective finiteness, softmax normalization, and recovery of the Section 4.3 ratio.

## Limitations

The included optimizer is designed for deterministic small-support recovery. Large neural language-model training should use a real ML stack and treat this skill as a semantic reference for the objective.
