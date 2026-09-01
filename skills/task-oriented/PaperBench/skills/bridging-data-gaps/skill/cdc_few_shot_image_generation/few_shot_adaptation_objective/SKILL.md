---
name: few_shot_adaptation_objective
description: Execute a bounded CDC-regularized few-shot adaptation optimizer step with route-aware realism terms.
---

# Few-Shot Adaptation Objective

Use this skill when a recovery or implementation must show that generator adaptation combines target realism pressure with cross-domain distance consistency. It is designed for small executable experiments and supports a finite-difference optimizer so it can run without deep-learning packages.

## Inputs
- Source feature vectors generated from a fixed source generator or proxy.
- Initial adapted scale and bias parameters for a tiny adapted generator.
- Target anchor feature vectors representing few-shot target examples.
- Latent route information from the anchor/patch protocol.
- Weights for CDC, image-anchor realism, and patch realism.

## Outputs
- Loss before and after one optimizer step.
- Parameters before and after the step.
- Components for CDC, image realism, and patch realism.
- Mechanism booleans suitable for `recovery_result.json`.

## Workflow
1. Generate adapted features using trainable scale and bias parameters.
2. Compute CDC loss against source features using the CDC skill.
3. Compute image-route realism against target anchors and patch-route smoothness against local feature magnitudes.
4. Combine the weighted losses and estimate finite-difference gradients.
5. Apply one optimizer step and record whether parameters and loss changed.

## Validation
Run `python tests/test_adaptation_objective.py` or validate this skill tree with `validate_skill_tree.py --run-tests`.

## Limitations
This skill is not full StyleGAN training. If used without torch/CUDA/checkpoints it must be described as reduced recovery, although the optimizer step and CDC calculation are real.
