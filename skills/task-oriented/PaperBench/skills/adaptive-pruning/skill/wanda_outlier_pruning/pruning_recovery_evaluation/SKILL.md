---
name: pruning_recovery_evaluation
description: Evaluate Wanda pruning masks for sparsity, no-update invariants, and linear-output reconstruction error.
---

# Pruning Recovery Evaluation

Use this skill to validate that a pruning experiment actually applied a mask, left unmasked weights unchanged, and produced numeric output-error evidence. It is suitable for reduced Wanda recovery when full LLM perplexity evaluation is not feasible.

## Inputs
- Original and pruned weight matrices.
- Evaluation activation matrix shaped examples by input channels.
- Boolean prune mask.
- Optional baseline error for comparison.

## Outputs
- Exact sparsity ratio.
- Relative output error `||XW^T - XW_pruned^T||_2 / ||XW^T||_2`.
- `unmasked_weights_unchanged` and `masked_weights_zero` invariant booleans.

## Workflow
1. Check matrix dimensions and mask shape.
2. Compute dense and pruned linear outputs.
3. Compute relative reconstruction error with a safe zero-denominator rule.
4. Verify Wanda's no-update claim: unmasked values must exactly match the original and masked values must be zero.

## Validation
Tests cover exact sparsity, unchanged unmasked weights, and a known linear-output error.

## Limitations
This skill does not claim full paper reproduction; it supplies mechanism evidence for proxy recovery.
