---
name: task-generalization
description: "Operate Transfer Learning Library domain-generalization and
  task-adaptation workflows using TLLib regularization, normalization, and
  reweighting APIs."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Task Generalization Skill

Use this sub-skill when a user needs TLLib guidance for **domain generalization** or **task adaptation / fine-tuning** rather than unsupervised domain adaptation.

## Route here for

- Domain generalization with source-domain-only training: ERM baselines, MixStyle, IBN, StochNorm-style normalization, CORAL as a DG penalty, GroupDRO, IRM, VREx, and MLDG-style meta-learning patterns.
- Task adaptation / fine-tuning regularizers: L2, L2-SP, DELTA, BSS, Co-Tuning, LwF, StochNorm, and Bi-Tuning.
- Safe CPU-level checks of `tllib.regularization`, `tllib.normalization`, `tllib.reweight.groupdro`, and CORAL loss components.
- Checkpoint conversion planning for MoCo-style pretraining outputs before fine-tuning.

## Route elsewhere

- Datasets, image-list formats, dataloaders, model factories, transforms, and metrics: [vision-data-models](../vision-data-models/SKILL.md).
- Unsupervised, partial, open-set, or adversarial domain adaptation: [domain-adaptation](../domain-adaptation/SKILL.md).
- Semi-supervised learning, pseudo-labeling, Mean Teacher, FixMatch/FlexMatch, UDA, DST, and Noisy Student workflows: [self-training](../self-training/SKILL.md).

## Operating sequence

1. Identify whether the task is **DG** (train on labeled source domains and test on held-out unseen domains) or **task adaptation** (fine-tune a pretrained model on a new labeled target task).
2. Confirm data/model readiness through [vision-data-models](../vision-data-models/SKILL.md) before discussing full training. The benchmark-scale workflows require datasets, pretrained weights, and usually CUDA; this sub-skill only claims CPU component-level verification.
3. Choose the method family:
   - DG style/normalization: MixStyle or IBN.
   - DG robust objective: GroupDRO, IRM, VREx, MLDG, or CORAL penalty.
   - Fine-tuning regularization: L2-SP/DELTA/BSS/Co-Tuning/LwF/StochNorm/Bi-Tuning.
4. Use the bundled references for implementation details and warning checks; do not copy or execute repository benchmark trainers as runtime helpers.
5. For installation/API sanity, run `scripts/tllib_task_generalization_smoke.py` from any directory where `tllib` is installed.

## References

- [API reference](references/api-reference.md)
- [Domain-generalization workflows](references/domain-generalization-workflows.md)
- [Task-adaptation workflows](references/task-adaptation-workflows.md)
- [Checkpoint conversion](references/checkpoint-conversion.md)
- [Troubleshooting](references/troubleshooting.md)

## Verification status

The bundled smoke script exercises small CPU tensors for regularization, normalization, reweighting, and CORAL components. It does **not** run benchmark training, download datasets, download pretrained checkpoints, or verify optional `timm`, `higher`, WILDS, Detectron2, or CUDA training stacks.
