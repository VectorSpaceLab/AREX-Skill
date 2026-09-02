---
name: pplm_latent_perturbation
description: Use when a PPLM-style controller must perturb latent/logit state at inference time with attribute and KL losses while freezing the base model.
---

# PPLM Latent Perturbation

Use this skill to implement the core PPLM inference-time update.

## Inputs
- Base next-token logits or latent state.
- Attribute loss function.
- Step size, iteration count, KL scale.

## Outputs
- Perturbed probability distribution.
- Trace with before/after loss, KL, and perturbation values.

## Workflow
1. Copy the base logits/state and keep it immutable.
2. Initialize a perturbation at zero.
3. Iteratively estimate the gradient of attribute loss plus KL-to-base penalty.
4. Update only the perturbation.
5. Return the final distribution and trace proving the target probability changed.

## Validation
Run `python tests/test_latent_perturbation.py`.

## Limitations
Reduced proxy implementations must declare that they are not full GPT-2 345M reproduction.
