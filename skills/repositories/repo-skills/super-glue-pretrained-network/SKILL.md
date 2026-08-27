---
name: super-glue-pretrained-network
description: "Use Magic Leap SuperGluePretrainedNetwork for SuperPoint plus
  SuperGlue image matching, pair evaluation, live demos, and Python API
  workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# SuperGluePretrainedNetwork

Use this repo skill when a task involves Magic Leap's SuperGluePretrainedNetwork codebase: SuperPoint feature extraction, SuperGlue feature matching, batch pair evaluation, visualization, or direct Python use of the shipped pretrained checkpoints.

This repository is a source-only research release, not a packaged training framework. It provides inference/evaluation code, pretrained SuperPoint/SuperGlue weights, sample images and pair manifests, and two top-level command workflows. It does **not** release SuperGlue training code, SIFT-based SuperGlue models, or homography models.

## Read first

- [Repository provenance](references/repo-provenance.md): source snapshot, evidence paths, package status, and refresh rules.
- [Setup and installation](references/setup-and-installation.md): dependency expectations, source-only import model, CPU/CUDA guidance, and smoke checks.
- [Model overview](references/model-overview.md): SuperPoint/SuperGlue roles, indoor/outdoor weights, data flow, and output conventions.
- [Troubleshooting](references/troubleshooting.md): cross-cutting install/import, weights, backend, OpenCV, license, and performance issues.
- [`scripts/check_superglue_environment.py`](scripts/check_superglue_environment.py): safe environment/import/weight/backend diagnostic helper that accepts an explicit `--repo-root`.

## Route by task

| User task | Read |
| --- | --- |
| Write Python that imports `models.Matching`, `SuperPoint`, `SuperGlue`, or `models.utils`; inspect configs, tensors, outputs, or geometry helpers; run a tiny API smoke. | [programmatic-api](sub-skills/programmatic-api/SKILL.md) |
| Run or adapt `match_pairs.py` behavior for batch image-pair matching, pose evaluation, `.npz` outputs, pair-file validation, indoor/outdoor settings, or cache/visualization flags. | [pair-matching-evaluation](sub-skills/pair-matching-evaluation/SKILL.md) |
| Run or adapt `demo_superglue.py` behavior for webcam/IP/video/image-directory live matching, headless remote sequence processing, keyboard controls, or rendered match visualizations. | [live-demo-and-visualization](sub-skills/live-demo-and-visualization/SKILL.md) |

## Minimal setup check

From a SuperGluePretrainedNetwork checkout or equivalent source distribution that contains `models/`, `models/weights/`, and the two top-level scripts, install the runtime dependencies documented by the release:

```bash
python -m pip install numpy torch matplotlib opencv-python
```

Then run the bundled checker from this skill directory:

```bash
python scripts/check_superglue_environment.py --repo-root <superglue-repo-root>
```

For direct imports, the runtime Python must be able to import the repository's top-level `models` package. In ad hoc scripts, add the repository root to `PYTHONPATH` or run from the checkout root before importing:

```python
from models.matching import Matching
```

Use CPU for portable checks. CUDA is optional acceleration: the repo scripts automatically choose CUDA when PyTorch reports it unless `--force_cpu` is set.

## Operating constraints

- Inputs are grayscale images or image pairs; color images are converted to grayscale before inference in the repo utilities.
- The released pretrained weights are `indoor` and `outdoor`; choose indoor for ScanNet-like indoor pairs and outdoor for wide-baseline outdoor scenes.
- Pair evaluation requires ground-truth intrinsics and relative pose in the pair manifest. Match-only manifests should not use `--eval`.
- Full ScanNet/YFCC/Phototourism table reproduction needs external datasets or challenge infrastructure; the bundled samples are suitable for smoke tests and workflow validation.
- Respect the repository's noncommercial research license when using code, weights, or derivatives.

## When not to use this skill

- General local feature matching libraries unrelated to SuperGluePretrainedNetwork.
- Training, fine-tuning, or checkpoint conversion requests; the release does not include training code.
- Hierarchical localization workflows outside this repo's two demo/evaluation scripts unless the task explicitly asks for SuperGluePretrainedNetwork internals.
