---
name: privacy-accounting
description: "Routes TensorFlow Privacy users who want privacy budgets,
  epsilon/delta statements, or the repo's privacy accounting CLIs."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Privacy accounting

Use this sub-skill when the user wants to compute privacy budgets, find a noise multiplier, or explain the accounting assumptions behind a DP-SGD run.

## Trigger phrases

- "compute epsilon"
- "find the noise multiplier"
- "DP-SGD privacy statement"
- "privacy budget"
- "accountant type"
- "user-level privacy"
- "tree aggregation accounting"

## What this sub-skill covers

- `compute_dp_sgd_privacy` / `compute_dp_sgd_privacy_statement`
- `compute_noise_from_budget`
- the `RDP` and `PLD` accountant choices
- tree-aggregation privacy accounting helpers
- user-level privacy notes when `max_examples_per_user` matters

## What it does not cover

- training-loop integration -> `../training/`
- `DPQuery` internals -> `../queries/`
- attack analysis -> `../privacy-tests/`
- fast clipping internals -> `../fast-clipping/`

## Read this before you act

- `references/api-reference.md` for the verified function signatures and the CLI flag map.
- `references/troubleshooting.md` for missing-flag, delta, user-level, and accountant-selection failures.
- `../../references/install-and-scope.md` for the minimum runtime.

## Typical workflow

1. Determine whether the user needs an example-level or user-level statement.
2. Choose `RDP` unless the user explicitly wants `PLD`.
3. Use the bundled CLI helper when a command-line answer is enough.
4. Use the API reference when the user wants to embed the calculation in code.
5. If the user wants a tree-aggregation variant, read the tree-accounting notes before answering.

## Bundled helpers

- `scripts/compute_dp_sgd_privacy.py` mirrors the privacy-statement CLI with the same core parameters.
- `scripts/compute_noise_from_budget.py` mirrors the inverse search CLI that solves for a noise multiplier.

## Cross-links

- `../training/` usually feeds the values that this sub-skill consumes.
- `../queries/` owns the lower-level query math that eventually feeds some accounting paths.
