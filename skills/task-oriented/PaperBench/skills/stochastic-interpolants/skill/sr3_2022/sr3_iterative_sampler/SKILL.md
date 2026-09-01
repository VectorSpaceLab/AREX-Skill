---
name: sr3_iterative_sampler
description: Apply the SR3 reverse-chain update from Gaussian noise to a refined high-resolution image. This reusable skill supports bounded SR3 recovery experiments.
---

# sr3_iterative_sampler

Use this skill for SR3 proxy recovery when implementing iterative_sampler. Inputs are tiny numeric arrays or metadata; outputs are deterministic logs or metrics. Workflow follows SR3 paper equations for degradation, noising, denoising loss, reverse refinement, or evaluation as appropriate. Validate with `validate_skill_tree.py --run-tests`. Limitations: not a full SR3 U-Net implementation and not a substitute for FFHQ/ImageNet-scale training.
