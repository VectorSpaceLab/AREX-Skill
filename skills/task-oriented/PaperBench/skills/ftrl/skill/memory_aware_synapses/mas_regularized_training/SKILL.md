---
name: mas_regularized_training
description: Apply the MAS quadratic regularizer during later-task training and log parameter drift evidence.
---
# MAS Regularized Training
Use for later-task optimizer steps with `task_loss + lambda * sum(Omega * (theta-theta_star)^2)`. Inputs are weights, task data, snapshot, importance, lambda, and optimizer settings. Outputs are updated parameters and loss/penalty traces. Validate with `python tests/test_regularizer.py`.
