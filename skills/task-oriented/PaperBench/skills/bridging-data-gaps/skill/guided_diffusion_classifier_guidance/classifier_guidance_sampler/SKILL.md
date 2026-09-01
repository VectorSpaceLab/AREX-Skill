---
name: classifier_guidance_sampler
description: Apply noisy classifier log-probability gradients to reverse diffusion steps with explicit guidance-scale checks.
---

# Classifier Guidance Sampler

Use this skill when implementing or auditing the paper's classifier-guided sampling mechanism. It is the central recovery skill for `Diffusion Models Beat GANs on Image Synthesis` because it verifies that `classifier_scale * grad_x log p(y | x_t, t)` changes the reverse update.

## Inputs

- Current noisy state or scalar proxy state.
- Target class label.
- Base reverse mean from a diffusion model or declared proxy update.
- Classifier log-probability gradient.
- Guidance scale and schedule variance or proxy step size.

## Outputs

- Guided state or guided reverse mean.
- Guidance vector.
- Log-probability and target-distance before and after guidance.
- Mechanism checks for recovery validation.

## Workflow

1. Compute the target class gradient with respect to the noisy input.
2. Multiply the gradient by the explicit classifier scale.
3. Add the scaled guidance contribution to the reverse diffusion mean.
4. Compare guided and unguided updates under the same base mean.
5. Record whether the target class log-probability increased and the target distance decreased.

## Validation

Run `python scripts/guidance_proxy.py --output /tmp/guidance.json`. The deterministic proxy uses a two-class Gaussian classifier and asserts that positive guidance improves the target mechanism checks.

## Limitations

This skill can support a reduced scalar proxy when checkpoints are unavailable. Such a run must be declared proxy evidence and must not be described as ImageNet FID recovery.
