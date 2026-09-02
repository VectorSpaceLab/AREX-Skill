---
name: pplm_perturbation_loop
description: Run PPLM-style iterative normalized gradient perturbations with KL regularization and optimizer trace evidence.
---

# PPLM Perturbation Loop

Use this skill when a recovery or implementation needs the central PPLM mechanism: optimizing an inference-time perturbation while the base language-model parameters remain fixed.

## Inputs
- Base logits or hidden-state proxy values.
- Objective callback returning loss, gradient, and diagnostics.
- Step size, iteration count, optional KL regularization scale, and gradient normalization flag.

## Outputs
- Perturbed logits/proxy values.
- Per-step trace with loss, target mass, KL to the base distribution, and parameter values.
- Booleans showing an optimizer step changed the perturbation.

## Workflow
1. Initialize perturbation to zeros or supplied values.
2. Evaluate the attribute objective on `base + perturbation`.
3. Add a KL-style gradient term toward the base distribution when requested.
4. Normalize nonzero gradients, take a descent step, and log before/after values.
5. Return the final perturbed logits and trace.

## Validation
Run `python tests/test_perturbation_loop.py` or use the Distiller validator.

## Limitations
The helper is a faithful low-dimensional proxy for PPLM optimization, not a transformer past-key-value implementation.
