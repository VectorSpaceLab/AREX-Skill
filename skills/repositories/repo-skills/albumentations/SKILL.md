---
name: albumentations
description: "Build, debug, serialize, and integrate Albumentations 2.x
  augmentation pipelines for images, masks, bboxes, keypoints, volumes, and
  PyTorch-style datasets."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Albumentations Repo Skill

Use this skill when a coding agent needs to work with Albumentations 2.x augmentation pipelines, choose transforms, validate targets, serialize/replay pipelines, or integrate augmentations into PyTorch-style data loading.

Albumentations is a NumPy/OpenCV-based augmentation library for computer vision and medical-imaging workflows. This skill covers the MIT-licensed `albumentations` package at version `2.0.8`. The upstream README states that the original Albumentations repository is no longer maintained and points users to AlbumentationsX for active development; keep that maintenance status in mind when recommending new dependencies or migrations.

## Quick Start

For deterministic/offline agent checks, suppress the package's import-time update check:

```bash
NO_ALBUMENTATIONS_UPDATE=1 python - <<'PY'
import albumentations as A
print(A.__version__)
PY
```

Minimal image pipeline:

```python
import albumentations as A

transform = A.Compose(
    [
        A.Resize(256, 256),
        A.HorizontalFlip(p=0.5),
        A.RandomBrightnessContrast(p=0.2),
    ],
    strict=True,
    seed=137,
)
result = transform(image=image_np)
augmented = result["image"]
```

Install the base package for NumPy/OpenCV augmentation:

```bash
pip install albumentations
```

Install optional integrations only when needed:

```bash
pip install "albumentations[pytorch]"  # ToTensorV2 / ToTensor3D
pip install "albumentations[hub]"      # Hugging Face Hub helpers
pip install "albumentations[text]"     # text rendering helpers
```

## Route By Task

- Use `sub-skills/pipeline-composition/` to build or debug `Compose`, `ReplayCompose`, `OneOf`, `SomeOf`, `RandomOrder`, `Sequential`, `OneOrOther`, `SelectiveChannelTransform`, strict validation, additional targets, seeds, and pipeline operator edits.
- Use `sub-skills/transform-catalog/` to choose transform families and parameters for pixel/color/noise/blur, crop/resize/pad/geometric, dropout, domain adaptation, spectrogram, text, and segmentation-safe pipelines.
- Use `sub-skills/targets-and-formats/` to handle input/output keys, masks, bboxes, keypoints, labels, additional targets, multiple images, volumes, and 3D masks.
- Use `sub-skills/serialization-and-reproducibility/` to save/load JSON or YAML configs, replay exact random choices, inspect applied parameters, handle custom `Lambda` objects, and reason about reproducibility.
- Use `sub-skills/framework-integration/` for PyTorch-style `Dataset` integration, `ToTensorV2`, `ToTensor3D`, optional extras, tensor shapes, dtype/range expectations, and DataLoader worker seeding.

## Shared References And Helpers

- `references/installation-and-maintenance.md`: package version, Python/dependency expectations, optional extras, maintenance status, and import/update-check behavior.
- `references/troubleshooting.md`: cross-cutting install/import, OpenCV, optional dependency, offline, validation, and migration troubleshooting.
- `references/repo-provenance.md`: source snapshot, evidence paths, and refresh baseline for staleness checks.
- `scripts/albumentations_smoke_check.py`: tiny safe import and pipeline smoke check for installed environments.

## Common Decision Points

- Keep images as NumPy arrays in `H,W,C` until a final framework tensor transform; route tensor issues to `framework-integration`.
- Use `strict=True` while developing pipelines to catch unknown keys and invalid transform arguments early; route Compose-level validation to `pipeline-composition`.
- Declare `bbox_params` and `keypoint_params` on `Compose` whenever calls include `bboxes` or `keypoints`; route coordinate issues to `targets-and-formats`.
- For segmentation masks, prefer nearest-neighbor mask interpolation and explicit `fill_mask`; route transform support decisions to `transform-catalog`.
- For reproducible debugging, use `seed`, `ReplayCompose`, or `save_applied_params=True` depending on whether you need repeatable streams, exact replay, or sampled-parameter inspection.
- Do not assume optional PyTorch, Hub, or text helpers are available from a base install; check extras and imports first.

## Safety And Self-Containment

This generated skill is self-contained. Runtime instructions, references, and helper scripts live inside this skill directory and do not require opening the original repository checkout. Treat original tests and source files as provenance evidence only; use the bundled sub-skills and helpers for future work.
