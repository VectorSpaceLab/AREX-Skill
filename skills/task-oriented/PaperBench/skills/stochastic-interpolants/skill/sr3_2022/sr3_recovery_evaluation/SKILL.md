---
name: sr3_recovery_evaluation
description: Evaluate SR3-style proxy runs with consistency metrics, source-boundary records, and mechanism checks. This reusable skill supports bounded SR3 recovery experiments.
---

# sr3_recovery_evaluation

Use this skill for SR3 proxy recovery when implementing recovery_evaluation. Inputs are tiny numeric arrays or metadata; outputs are deterministic logs or metrics. Workflow follows SR3 paper equations for degradation, noising, denoising loss, reverse refinement, or evaluation as appropriate. Validate with `validate_skill_tree.py --run-tests`. Limitations: not a full SR3 U-Net implementation and not a substitute for FFHQ/ImageNet-scale training.
