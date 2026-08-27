---
name: domain-adaptation
description: "Router for Transfer-Learning-Library domain adaptation workflows,
  losses, and optional benchmark stacks."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Domain Adaptation

Use this sub-skill for TLLib domain-adaptation workflows, loss wiring, and benchmark recipe selection.

## What it covers
- Closed-set feature alignment: DANN, CDAN, ADDA, DAN, JAN, CORAL, BSP, MCD, MDD.
- Partial and open-set adaptation: PADA, IWAN, OSBP, class-weight reweighting, unknown-class thresholding.
- Special DA variants: AFN, MCC, RegDA keypoint, D-adapt object detection, and WILDS DA examples.

## Route elsewhere when
- Datasets, ImageList formats, model factories, or transforms are the main question: `../vision-data-models/SKILL.md`
- Translation, CycleGAN, FDA, or style-transfer is the main question: `../translation/SKILL.md`
- SSL, pseudo-labeling, or teacher/student training is the main question: `../self-training/SKILL.md`
- DG, fine-tuning, or standalone transfer regularization is the main question: `../task-generalization/SKILL.md`

## How to use
1. Identify the transfer setting: closed-set, partial, open-set, regression, keypoint, detection, or WILDS.
2. Pick the matching API or workflow reference in `references/`.
3. For CPU-safe validation, use `scripts/tllib_domain_adaptation_smoke.py`.
4. Treat object-detection and WILDS coverage as optional-stack guidance unless the user explicitly has those dependencies.

## Notes
- AFN appears here because it is used in DA workflows, but its standalone module mechanics live in the task-generalization / normalization path.
- MCC appears here because it is used in DA workflows, but its standalone semi-supervised mechanics live in the self-training path.
- Do not point users back to the source checkout or benchmark launchers; keep them on the bundled references and smoke helper.
- Keep benchmark-scale training, downloads, and optional dependency setup out of the smoke path.

## Reference map
- `references/api-reference.md` - public modules, losses, shapes, and common traps.
- `references/domain-adaptation-workflows.md` - classifier, regression, keypoint, and WILDS workflow patterns.
- `references/object-detection-adaptation.md` - D-adapt, Detectron2, proposal and feedback flow, optional stack notes.
- `references/wilds-workflows.md` - WILDS-specific CLI and dependency patterns.
- `references/troubleshooting.md` - shape, NumPy, TorchVision, CUDA, Detectron2, and WILDS issues.
- `scripts/tllib_domain_adaptation_smoke.py` - tiny CPU tensor smoke using installed `tllib`.
