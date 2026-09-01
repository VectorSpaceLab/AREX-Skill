---
name: p3o_surrogate_loss
description: Build decomposed P3O surrogate loss terms with clipped replay gradients and behavior-to-target KL regularization.
---

# P3O Surrogate Loss

Use this skill when a recovery or implementation must preserve the P3O objective from Equation 14. It is not a full RL framework; it computes deterministic scalar components that can be embedded in a learner.

## Inputs
- On-policy score-gradient proxies and advantages.
- Off-policy score-gradient proxies, advantages, and importance ratios.
- Target and behavior action distributions for KL estimation.
- `clip_threshold` and `kl_coefficient`, usually from the ESS scheduler.

## Outputs
- `on_policy`, `off_policy`, `kl_penalty`, and `objective` scalar values.
- Clipped ratios used for replay data.

## Workflow
1. Multiply on-policy advantages by score-gradient proxies.
2. Clip each replay importance ratio at `c` and multiply by replay advantage and score proxy.
3. Compute `KL(beta || pi_theta)` over behavior and target distributions.
4. Combine terms as `on + off - lambda * KL`.

## Source Boundary
Use this skill with the paper, module documents, generated artifacts, and ordinary package documentation. Do not read or depend on the original P3O repository.

## Validation
Run `python scripts/<script>.py --self-test` or `python -m pytest tests` from the skill directory. The bundled tests use only the Python standard library.

