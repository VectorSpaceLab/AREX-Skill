---
name: nce_recovery_evaluation
description: Evaluate conditional NCE recovery with ratio errors, KL metrics, and explicit mechanism checks for proxy runs.
---

# NCE Recovery Evaluation

Use this skill after ranking and binary NCE recovery outputs are available. It compares the declared module-plan target against the recovery result and emits the mechanism checks needed for a soft-mode proxy recovery.

Do not use this skill to hide target drift. It should fail or report non-acceptance if the recovery target metadata differs from the module plan.

## Inputs

- The `fast_recovery_target` from `module_plan.json`.
- A ranking NCE output JSON.
- A binary NCE diagnostic JSON.
- A training trace or optimizer-update record.
- Source-boundary status from the recovery harness.

## Outputs

- `ranking_ratio_absolute_error`.
- `binary_inconsistency_gap`.
- KL divergence for optional synthetic distributions.
- Mechanism checks:
  - ranking candidate posterior normalized
  - ranking ratio recovered
  - binary self-normalization failed as expected
  - binary limit matched the paper counterexample
  - reduced optimizer step changed parameters

## Workflow

1. Load ranking and binary outputs.
2. Compute absolute error between ranking `x1` ratio and the true `1/3` ratio.
3. Compute the binary gap against the true ratio and check closeness to `3/7`.
4. Verify loss decreased and parameters changed in the reduced optimizer trace.
5. Produce a validator-compatible recovery-result payload.

## Validation

Run the Distiller skill validator with tests. Tests cover ratio metrics, KL computation, and mechanism-check booleans.

## Limitations

This skill evaluates reduced finite-support recovery. It does not compute Penn Treebank perplexity.
