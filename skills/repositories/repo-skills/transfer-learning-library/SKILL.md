---
name: transfer-learning-library
description: "Use Transfer Learning Library (TLLib) for PyTorch transfer
  learning, domain adaptation, domain generalization, task adaptation,
  self-training, model selection, and vision data/model workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Transfer Learning Library (TLLib)

Use this repo skill when a task names **Transfer Learning Library**, **TLLib**, `tllib`, or asks for PyTorch transfer-learning workflows such as domain adaptation, domain generalization, task adaptation/fine-tuning, self-training, model ranking, or TLLib vision datasets/models.

## First checks

1. Confirm the package imports before following any workflow:

   ```bash
   python - <<'PY'
   import tllib, torch, torchvision, numpy
   print('tllib', tllib.__version__)
   print('torch', torch.__version__)
   print('torchvision', torchvision.__version__)
   print('numpy', numpy.__version__)
   PY
   ```

2. For TLLib 0.4, prefer an older compatible stack when model factories or losses fail under modern dependencies: Python 3.8, PyTorch/TorchVision from the 1.8/0.9 era, and `numpy<1.24` are known-good inspection choices.
3. Run the bundled root smoke check when diagnosing install/import problems:

   ```bash
   python scripts/check_tllib_install.py
   ```

4. Read [`references/repo-provenance.md`](references/repo-provenance.md) before deciding whether this skill is current for a checkout. Read [`references/troubleshooting.md`](references/troubleshooting.md) for install/import, dependency, dataset, and backend failures.

## Route by task

| User task | Read |
| --- | --- |
| Unsupervised/partial/open-set/domain-adversarial adaptation; DANN, CDAN, DAN, JAN, MDD, MCD, MCC, AFN, BSP, RegDA, D-adapt, WILDS adaptation | [`sub-skills/domain-adaptation/SKILL.md`](sub-skills/domain-adaptation/SKILL.md) |
| Dataset roots, `ImageList` text files, domain names, transforms, vision model factories, re-id/keypoint/segmentation utilities, metrics/loggers | [`sub-skills/vision-data-models/SKILL.md`](sub-skills/vision-data-models/SKILL.md) |
| Domain generalization or fine-tuning/task adaptation; MixStyle, IBN, StochNorm, GroupDRO, IRM/VREx/MLDG, L2-SP, DELTA, BSS, Co-Tuning, LwF, Bi-Tuning | [`sub-skills/task-generalization/SKILL.md`](sub-skills/task-generalization/SKILL.md) |
| Semi-supervised learning or self-training; pseudo-labeling, Pi Model, Mean Teacher, UDA, FixMatch/FlexMatch, MCC, Self-Tuning, DST, Noisy Student | [`sub-skills/self-training/SKILL.md`](sub-skills/self-training/SKILL.md) |
| Rank or choose pretrained models by transferability metrics; H-score, regularized H-score, LEEP, NCE, LogME, TransRate | [`sub-skills/model-selection/SKILL.md`](sub-skills/model-selection/SKILL.md) |
| CycleGAN/FDA/CyCADA/SPGAN image or domain translation components | [`sub-skills/translation/SKILL.md`](sub-skills/translation/SKILL.md) |

Use [`references/capability-map.md`](references/capability-map.md) when the user names an algorithm and you need to find its TLLib module, owning sub-skill, optional dependencies, or validation route.

## Operating boundaries

- This skill teaches the installed `tllib` package and distilled workflow patterns. It does **not** require the original repository checkout at runtime.
- Original benchmark examples are treated as evidence only. Their reusable behavior is distilled into references and bundled scripts; do not ask future users to open or run source-tree examples.
- CPU smoke checks validate public APIs and tensor/array contracts. Real benchmark training is usually long-running, dataset-dependent, and GPU-recommended.
- Object detection adaptation, WILDS, text/molecule examples, and some DG trainers need optional stacks such as Detectron2, MMCV, WILDS, TensorFlow, Transformers, Torch Geometric, OGB, `timm`, or `higher`. Install only the optional stack that the user explicitly needs.
- Dataset downloads are external and may be broken or license-restricted. Prefer user-provided local datasets and validate layouts with the `vision-data-models` scripts.

## Bundled root assets

- [`scripts/check_tllib_install.py`](scripts/check_tllib_install.py) verifies imports, version compatibility, representative public APIs, and optional backend visibility without downloading data.
- [`references/troubleshooting.md`](references/troubleshooting.md) covers cross-cutting failures before routing to workflow-specific troubleshooting.
- [`references/repo-routing-metadata.json`](references/repo-routing-metadata.json) contains structured metadata for managed repo-skill routing.
