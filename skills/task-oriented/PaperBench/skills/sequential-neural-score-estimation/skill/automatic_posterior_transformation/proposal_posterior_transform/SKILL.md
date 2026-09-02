---
name: proposal_posterior_transform
description: Apply APT proposal-prior log-density corrections to candidate posterior scores for likelihood-free inference.
---

# Proposal Posterior Transform

Use this skill when implementing Automatic Posterior Transformation (APT) training on simulations drawn from a proposal distribution rather than the prior. Do not use it for ordinary prior-only neural posterior estimation, where proposal and prior corrections cancel.

## Inputs
- `model_log_scores`: posterior log-score values for the same candidate atoms.
- `prior_log_probs`: log prior density for every candidate atom.
- `proposal_log_probs`: log proposal density for every candidate atom.

## Outputs
- `corrected_logits`: `model_log_score + proposal_log_prob - prior_log_prob` for every atom.
- `probabilities`: numerically stable softmax probabilities over corrected logits.

## Workflow
1. Confirm all arrays have equal non-zero length.
2. Add the proposal-minus-prior correction to every model score.
3. Normalize with a max-subtracted softmax.
4. Propagate impossible support through `-inf` log densities and fail if the normalized mass is invalid.

## Validation
Run `python scripts/apt_transform.py --self-test` or the skill-tree validator with tests enabled.

## Limitations
This skill implements deterministic correction math only. It does not train a neural density estimator or choose proposal schedules.
