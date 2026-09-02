---
name: generalization_gap_bound
description: Validate paper-target metadata, aggregate influence tolerance, and observed pruning metric gaps for generalization-influence pruning.
---

# Generalization Gap Bound Check

Use this skill when a candidate pruned subset has been selected and the recovery needs a deterministic pass/fail check linking aggregate influence to the declared target. It is a metadata and mechanism gate, not a replacement for training or evaluation.

## Inputs

- Module-plan target metadata.
- Aggregate influence norm and epsilon.
- Baseline and retained metrics or losses when available.
- Booleans describing whether proxy/full training and optimizer steps executed.

## Outputs

- Bound status and observed metric gap.
- Mechanism checks suitable for `recovery_result.json`.
- Reasons for any failure.

## Workflow

1. Compare recovery target metadata against the module plan.
2. Check `aggregate_norm <= epsilon`.
3. Compute the observed absolute metric gap.
4. Require influence estimation, aggregate optimization, and some training/evaluation evidence for proxy acceptance.

## Validation

Run `python scripts/check_gap_bound.py --demo` and `python tests/test_check_gap_bound.py` from this skill directory.

## Limitations

This skill records a paper-inspired bound check for reduced experiments; it does not prove the full theorem for arbitrary neural networks.
