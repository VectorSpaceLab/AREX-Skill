---
name: atomic_loss_training
description: Build and optimize the finite-atom APT contrastive loss with proposal posterior correction.
---

# Atomic Loss Training

Use this skill to implement the APT finite-atom objective from Section 3.2. It is appropriate for reduced recovery, ablations, and deterministic tests where the posterior estimator is represented by a simple differentiable score function.

## Inputs
- Atom parameter values and the index of the positive simulated parameter.
- Observation value and affine score parameters.
- Prior and proposal log-density values for the atoms.
- Learning rate for one optimizer step.

## Outputs
- Cross-entropy loss before and after update.
- Probability assigned to the positive atom.
- Parameter values before and after the optimizer step.

## Workflow
1. Score each atom with an observation-conditioned affine model.
2. Apply the proposal-posterior transform before computing probabilities.
3. Compute cross-entropy against the positive atom.
4. Compute analytic gradients and update trainable parameters.
5. Record a trace compatible with recovery validation.

## Validation
Run `python scripts/atomic_loss.py --self-test`. The deterministic test verifies that the optimizer changes parameters and reduces loss.

## Limitations
The provided script is a compact recovery implementation. Full APT normally uses neural density estimators such as mixtures or flows.
