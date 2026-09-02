---
name: mas_unlabeled_importance
description: Estimate Memory Aware Synapses parameter importance from unlabeled inputs using output-sensitivity gradients.
---
# MAS Unlabeled Importance
Use when MAS recovery needs label-free importance. Inputs are weights and unlabeled samples; outputs are nonnegative importance values and sample-count metadata. Compute squared-output-norm gradients, average absolute values, and reject empty streams. Validate with `python tests/test_importance.py`.
