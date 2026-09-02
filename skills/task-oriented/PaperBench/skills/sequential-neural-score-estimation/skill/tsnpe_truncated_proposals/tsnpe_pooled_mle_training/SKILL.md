---
name: tsnpe_pooled_mle_training
description: Fit a reduced Gaussian posterior surrogate with pooled maximum-likelihood updates.
---

# Tsnpe Pooled Mle Training

Use this skill to implement the TSNPE training contract after simulations from prior or truncated proposals have been collected. The update must pool round data and minimize ordinary negative log likelihood; it must not apply APT atomic-loss proposal correction.

Inputs: JSON with `theta`, `x`, `observation`, initial `mean`/`log_std`, learning rate, and steps. Outputs: updated parameters, before/after loss, and optimizer-change evidence. Validation: run `python tests/test_train.py`.

