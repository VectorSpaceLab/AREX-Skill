---
name: block_fisher_rearrangement
description: Rearrange binary pruning masks using block-diagonal Fisher interactions while preserving per-layer cardinality.
---

# Block Fisher Rearrangement

Use this skill after diagonal Fisher mask search has produced binary layer masks. It improves pruning locations within each Transformer layer by using a block Fisher matrix. Do not use it to change the pruning ratio; the paper's rearrangement stage preserves per-layer kept counts and therefore preserves cost.

## Inputs

- A binary mask for each layer.
- A square Fisher block for each layer.
- Optional maximum number of greedy passes.

## Outputs

- Rearranged masks with the same cardinality as inputs.
- Objective values before and after rearrangement.
- Swap trace.

## Workflow

For each layer, score `(1-m)^T I (1-m)`. Try swaps between pruned and kept units and commit only objective-improving swaps. Repeat until no improvement or a pass limit is reached.

## Validation

Run the included tests or `validate_skill_tree.py --run-tests`.
