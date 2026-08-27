---
name: self-training
description: "Operate Transfer Learning Library semi-supervised and
  self-training workflows using TLLib pseudo-label, consistency, teacher,
  thresholding, and debiasing APIs."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Self-Training Skill

Use this sub-skill when a user needs TLLib guidance for **semi-supervised learning** or **self-training** on image classification tasks: pseudo-labeling, Pi Model, Mean Teacher, UDA, FixMatch, FlexMatch, Self-Tuning, DST, DebiasMatch-style thresholding, Noisy Student, or MCC-like self-training regularizers.

## Route here for

- Confidence-based pseudo-label selection, consistency losses, weak/strong augmentation training loops, EMA teacher/student updates, dynamic thresholding, class-balance regularization, DST worst-case estimation, and Self-Tuning queues.
- Choosing between Pseudo Label, Pi Model, Mean Teacher, UDA, FixMatch, FlexMatch, Noisy Student, Self-Tuning, DebiasMatch-style debiasing, DST, and MCC-style regularization.
- Safe CPU checks for `tllib.self_training` losses/helpers without datasets, checkpoints, GPUs, or benchmark training.
- MoCo-style checkpoint conversion planning before SSL fine-tuning.

## Route elsewhere

- Datasets, image-list formats, class-balanced labeled subsets, transforms, model factories, metrics, and utility loaders: [vision-data-models](../vision-data-models/SKILL.md).
- Task adaptation / fine-tuning regularizers or checkpoint use after conversion: [task-generalization](../task-generalization/SKILL.md).
- Domain-adaptation tasks that use MCC on target-domain predictions: [domain-adaptation](../domain-adaptation/SKILL.md).

## Operating sequence

1. Confirm the task is semi-supervised/self-training: a small labeled split plus a larger unlabeled split, or a teacher/student self-training loop. If the user is adapting across source/target domains, route DA-specific pieces to [domain-adaptation](../domain-adaptation/SKILL.md).
2. Confirm data/model readiness through [vision-data-models](../vision-data-models/SKILL.md). Full SSL training needs datasets, class-balanced labeled sampling, weak/strong augmentations, pretrained backbones or checkpoints, and usually CUDA; this sub-skill only claims CPU component-level verification.
3. Choose the method family:
   - Simple pseudo labels: `ConfidenceBasedSelfTrainingLoss`.
   - Prediction consistency: `L2ConsistencyLoss` / `ConsistencyLoss`.
   - Teacher/student averaging: `EMATeacher` plus a consistency loss.
   - Weak/strong augmentation: UDA or FixMatch-style losses.
   - Curriculum thresholding: `DynamicThresholdingModule` for FlexMatch.
   - Self-supervised or contrastive adaptation: Self-Tuning and MoCo checkpoint conversion.
   - Debiasing: DST heads/losses or DebiasMatch-style class-balance/threshold checks.
4. Use the bundled references for API signatures, workflow recipes, checkpoint conversion, and troubleshooting. Do not copy or execute repository benchmark trainers as runtime helpers.
5. For installation/API sanity, run `scripts/tllib_self_training_smoke.py` from any directory where `tllib` is installed.

## References

- [API reference](references/api-reference.md)
- [Self-training workflows](references/self-training-workflows.md)
- [Checkpoint conversion](references/checkpoint-conversion.md)
- [Troubleshooting](references/troubleshooting.md)

## Verification status

The bundled smoke script exercises tiny CPU tensors for pseudo-label selection, consistency, EMA teacher updates, UDA weak/strong loss, MCC, FlexMatch dynamic thresholds, class-balance loss, and DST worst-case estimation. It does **not** run benchmark training, download datasets, download pretrained checkpoints, perform MoCo conversion on external files, or verify optional `timm`/CUDA training stacks.
