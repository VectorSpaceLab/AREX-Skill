---
name: sr3_degradation_schedule
description: Build paired low/high-resolution items and cumulative diffusion schedules that match SR3 equations. This reusable skill supports bounded SR3 recovery experiments.
---

# sr3_degradation_schedule

Use this skill for SR3 proxy recovery when implementing degradation_schedule. Inputs are tiny numeric arrays or metadata; outputs are deterministic logs or metrics. Workflow follows SR3 paper equations for degradation, noising, denoising loss, reverse refinement, or evaluation as appropriate. Validate with `validate_skill_tree.py --run-tests`. Limitations: not a full SR3 U-Net implementation and not a substitute for FFHQ/ImageNet-scale training.
