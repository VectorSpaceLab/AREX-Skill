---
name: probabilistic_mask_relaxation
description: Build Bernoulli coreset mask probabilities, sample masks, and compute score-function gradients for probabilistic bilevel coreset selection.
---

# Probabilistic Mask Relaxation

Use this skill when a coreset method needs to replace discrete subset membership with independent Bernoulli random variables. It is appropriate for reduced or full implementations of Probabilistic Bilevel Coreset Selection and for diagnostics that need reproducible mask sampling.

Do not use this skill for deterministic greedy addition rules or for weighted coreset objectives with separate learned sample weights; the paper removes those weights so the score-function estimator can operate on binary masks.

## Inputs
- `n`: positive dataset size.
- `budget`: expected coreset size `K` with `0 <= K <= n`.
- Optional `probabilities`: a length-`n` vector in `[0, 1]`.
- Optional `seed`: integer seed for deterministic sampling.

## Outputs
- Initial or validated probability vectors whose sum is bounded by `K`.
- Binary mask samples with one element per training item.
- Bernoulli score gradients `grad_s log p(m|s)` using clipped probabilities for numerical stability.

## Workflow
1. Initialize all probabilities to `K / n` when no vector is supplied.
2. Clip only for gradient safety, not as a substitute for the capped-simplex projection skill.
3. Sample each mask element independently from `Bernoulli(s_i)`.
4. Compute score gradients as `(m_i - s_i) / (s_i * (1 - s_i))`.
5. Pass probability updates to the projection skill before reusing them.

## Validation
Run `python tests/test_mask_relaxation.py` or validate this skill tree with `validate_skill_tree.py --run-tests`. The tests check budget initialization, deterministic sampling, binary outputs, and finite gradients.

## Limitations
This skill does not train the inner model and does not evaluate validation loss. It only owns the probabilistic mask representation required by the outer-loop skill.
