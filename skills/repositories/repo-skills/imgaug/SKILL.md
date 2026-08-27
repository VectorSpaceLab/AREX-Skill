---
name: imgaug
description: "Use when working with imgaug image augmentation pipelines, aligned
  annotations, stochastic parameters, dtype/data utilities, or multicore
  augmentation for computer-vision data."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# imgaug Repo Skill

Use this skill when a task involves the Python package **imgaug**: building image augmentation pipelines, applying identical transforms to annotations, choosing stochastic parameters, debugging dtype/shape issues, or running background augmentation for computer-vision training data.

This is a self-contained operating guide. Do not rely on the original repository checkout being available; use the bundled references and scripts in this skill.

## First checks

For a fresh environment, install a compatible runtime before using examples:

```bash
python -m pip install "imgaug==0.4.0" "numpy<2" "opencv-python-headless<4.12"
```

If installing from a local clone of imgaug 0.4.0, modern build isolation can fail because `setup.py` imports `pkg_resources`. Use a private environment and, only when needed, install `setuptools<81` before a no-build-isolation local install. Prefer the public package install above for ordinary use.

Run the bundled environment check whenever installation, imports, optional dependencies, or compatibility are uncertain:

```bash
python scripts/check_imgaug_env.py
```

Run a short end-to-end smoke that adapts imgaug's documented examples without display, network, or large data:

```bash
python scripts/smoke_imgaug_workflows.py
```

## Route by task

| Task signal | Read next |
| --- | --- |
| Build `iaa.Sequential`, `SomeOf`, `OneOf`, `Sometimes`, `WithChannels`, image-only augmentation, or choose augmenter families such as affine, blur, color, contrast, dropout, weather, superpixels, or PIL-like effects | [`sub-skills/augmentation-pipelines/SKILL.md`](sub-skills/augmentation-pipelines/SKILL.md) |
| Apply one transform consistently to keypoints, bounding boxes, polygons, line strings, heatmaps, segmentation maps, or mixed `Batch`/`UnnormalizedBatch` objects | [`sub-skills/augmentables-and-batches/SKILL.md`](sub-skills/augmentables-and-batches/SKILL.md) |
| Control random sampling, seeds, deterministic replay, stochastic parameter distributions, dtype conversion, example quokka data, image resizing, grids, or display helpers | [`sub-skills/parameters-random-and-utilities/SKILL.md`](sub-skills/parameters-random-and-utilities/SKILL.md) |
| Speed up augmentation with `augment_batches(..., background=True)`, `Augmenter.pool()`, `imgaug.multicore.Pool`, `BatchLoader`, or debug multiprocessing/performance issues | [`sub-skills/multicore-and-diagnostics/SKILL.md`](sub-skills/multicore-and-diagnostics/SKILL.md) |

## Core usage pattern

Most workflows start with NumPy arrays in image shape `(N, H, W, C)` or a list of `(H, W, C)` arrays. Images should usually be RGB `uint8` with values `0..255`; convert BGR images loaded by OpenCV before color augmentations.

```python
import numpy as np
import imgaug.augmenters as iaa

images = np.zeros((8, 64, 64, 3), dtype=np.uint8)
seq = iaa.Sequential([
    iaa.Fliplr(0.5),
    iaa.Affine(rotate=(-10, 10)),
    iaa.GaussianBlur(sigma=(0.0, 1.0)),
])
images_aug = seq(images=images)
```

When images have annotations, pass them in the same call so geometric parameters are sampled once and applied consistently:

```python
images_aug, keypoints_aug = seq(images=images, keypoints=keypoints)
```

Use `to_deterministic()` when you must apply the same sampled transform in separate calls, but prefer a single call containing all aligned augmentables when possible.

## Bundled references

- [`references/package-overview.md`](references/package-overview.md) gives the package map, supported workflows, dependencies, and source-artifact replacement map.
- [`references/troubleshooting.md`](references/troubleshooting.md) covers cross-cutting install/import, NumPy/OpenCV, dtype/shape, optional dependency, display, and multiprocessing failures.
- [`references/repo-provenance.md`](references/repo-provenance.md) records the source snapshot used to build this skill; read it before deciding whether a checkout needs `refresh-repo-skill`.
- [`references/repo-routing-metadata.json`](references/repo-routing-metadata.json) is structured metadata for managed repo-skill routing.

## What this skill does not cover

- It does not teach general computer-vision model training frameworks beyond preparing augmented arrays/batches for them.
- It does not run long visual/performance checks from the source repository; bundled scripts use tiny deterministic fixtures.
- It does not verify optional `imagecorruptions` or `numba` acceleration unless the current task explicitly requires them.
