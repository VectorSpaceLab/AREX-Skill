---
name: sr3_conditional_denoising_loss
description: Compute and optimize the SR3 conditional denoising objective for a lightweight trainable denoiser. This reusable skill supports bounded SR3 recovery experiments.
---

# sr3_conditional_denoising_loss

Use this skill for SR3 proxy recovery when implementing conditional_denoising_loss. Inputs are tiny numeric arrays or metadata; outputs are deterministic logs or metrics. Workflow follows SR3 paper equations for degradation, noising, denoising loss, reverse refinement, or evaluation as appropriate. Validate with `validate_skill_tree.py --run-tests`. Limitations: not a full SR3 U-Net implementation and not a substitute for FFHQ/ImageNet-scale training.
