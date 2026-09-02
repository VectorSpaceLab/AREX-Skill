---
name: cfm_training_objective
description: Compute Conditional Flow Matching losses and bounded optimizer updates for a small parametric vector field.
---
# CFM Training Objective
Use this skill to compute `E||v_theta(t,x_t)-u_t||^2` and log real optimizer updates. Inputs are path batches and predictor parameters; outputs are scalar loss and a trace with `loss_before`, `loss_after`, `params_before`, and `params_after`. Run `python tests/test_cfm_training.py`. The included nonlinear-feature linear model is for bounded recovery, not full image training.
