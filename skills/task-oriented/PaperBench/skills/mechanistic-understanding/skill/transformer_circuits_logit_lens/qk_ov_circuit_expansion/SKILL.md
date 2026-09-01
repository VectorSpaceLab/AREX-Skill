---
name: qk_ov_circuit_expansion
description: Expand attention-head QK and OV weights into token-level circuit matrices and copying diagnostics.
---

# QK and OV Circuit Expansion

Use this skill when analyzing an attention head as separable query-key and output-value circuits. It is designed for mechanistic interpretability of attention-only or attention-isolated transformer components. Do not use its copying score as definitive proof by itself; pair it with behavioral tests or ablations.

## Inputs

- `embedding`: vocabulary-by-model matrix.
- `unembedding`: model-by-vocabulary matrix.
- `w_qk`: model-by-model combined query-key matrix, or already-combined equivalent.
- `w_ov`: model-by-model combined output-value matrix.

The included script uses row-vector convention and computes `embedding @ w_qk @ embedding.T` and `embedding @ w_ov @ unembedding`.

## Outputs

- Expanded QK token-score circuit.
- Expanded OV token-to-logit circuit.
- Diagnostics such as diagonal mean, off-diagonal mean, diagonal dominance, and positive-real-eigenvalue fraction for two-by-two matrices.

## Workflow

1. Validate matrix compatibility.
2. Multiply out QK and OV circuits through token embeddings and unembeddings.
3. Summarize whether the OV matrix preferentially copies matching token identities.
4. Use the expanded matrices as inputs to skip-trigram, induction-head, or path-expansion analysis.

## Validation

Run the tests or the Paper2Skills skill-tree validator with `--run-tests`.

## Limitations

The script intentionally avoids heavy numerical dependencies. Eigenvalue diagnostics are exact only for one-by-one and two-by-two examples; larger matrices still get diagonal dominance summaries.
