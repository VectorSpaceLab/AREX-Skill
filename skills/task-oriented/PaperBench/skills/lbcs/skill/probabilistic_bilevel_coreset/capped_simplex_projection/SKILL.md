---
name: capped_simplex_projection
description: Project coreset probability vectors onto the box-constrained simplex budget used by probabilistic bilevel coreset selection.
---

# Capped Simplex Projection

Use this skill after any outer-loop update to ensure coreset probabilities remain in the feasible set `0 <= s_i <= 1` and `sum_i s_i <= K`. It is the feasibility operator in the paper's projected stochastic-gradient update.

Do not use this skill as a ranking or selection algorithm. It only repairs a probability vector after another component has proposed an update.

## Inputs
- A finite numeric vector of probabilities or raw updated scores.
- A nonnegative budget `K`.

## Outputs
- A vector with the same length.
- Every element lies in `[0, 1]`.
- The vector sum is no greater than `K`, with equality when the input exceeds the budget and `0 < K < n`.

## Workflow
1. Validate all inputs are finite.
2. Clip values to the probability box.
3. Return immediately when the clipped vector is already within budget.
4. Otherwise find the threshold that makes `sum_i clip(v_i - tau, 0, 1) = K`.
5. Use the projected vector in subsequent Bernoulli sampling.

## Validation
Run `python tests/test_projection.py` or `validate_skill_tree.py --run-tests`. Tests cover feasible vectors, active budget projection, zero budget, and full budget clipping.

## Limitations
The projection is deterministic and numeric; it does not decide whether the learned coreset is semantically useful and does not compute validation losses.
