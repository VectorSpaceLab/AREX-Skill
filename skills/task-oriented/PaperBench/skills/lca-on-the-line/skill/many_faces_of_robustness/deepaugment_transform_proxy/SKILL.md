---
name: deepaugment_transform_proxy
description: Create deterministic semantic-preserving texture and style perturbations for bounded DeepAugment-style recovery tests.
---

# DeepAugment Transform Proxy

Use this skill when full DeepAugment image-to-image networks are unavailable but a bounded recovery must still exercise the paper mechanism: label-preserving changes to texture-like/local-statistic features. Do not use this skill as evidence of full ImageNet-scale DeepAugment training.

## Inputs
- Examples with numeric `features` and a `label`.
- A deterministic seed and perturbation strength.

## Outputs
- Augmented examples with unchanged labels.
- A transformation log naming the applied perturbation families.

## Workflow
1. Keep semantic coordinates stable enough for the class label to remain valid.
2. Perturb nuisance or texture-like coordinates with contrast, noise, and mixture operations.
3. Emit a log for every generated example.
4. Verify transformed examples differ from clean inputs while preserving labels.

## Validation
Run `python tests/test_transform.py` or the Distiller skill validator with tests enabled.

## Limitations
The proxy operates on tiny numeric features, not real images or perturbed neural image translators. It is acceptable only for declared soft-mode reduced recovery.
