---
name: stochastic_actor_update
description: Run a deterministic SAC-style stochastic actor update with reparameterized Gaussian action, log probability, and policy-gradient diagnostics.
---

# Stochastic Actor Update

Use this skill when a recovery needs to exercise the actor component of SAC without depending on a full deep-learning stack. It implements a tiny scalar Gaussian actor with fixed noise so the reparameterized policy loss can be audited deterministically.

## Inputs
- Actor mean and log standard deviation parameters.
- State feature and deterministic noise sample.
- A differentiable quadratic Q proxy target.
- Learning rate.

## Outputs
- Action, log probability, Q value, policy loss.
- Updated actor parameters and parameter-change evidence.

## Workflow
1. Reparameterize the action as `mean * state + exp(log_std) * noise`.
2. Evaluate Gaussian log probability for the noise-scaled action.
3. Compute SAC policy loss `alpha * log_prob - Q(action)`.
4. Use analytic gradients for the scalar actor and update parameters.
5. Record before/after parameters for validation.

## Validation
Run `python tests/test_actor_update.py` or the Distiller skill validator.

## Limitations
This is a scalar deterministic proxy for the SAC actor update. It preserves the optimization contract but is not a neural-network policy implementation.
