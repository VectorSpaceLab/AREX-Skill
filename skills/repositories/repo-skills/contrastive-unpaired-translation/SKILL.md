---
name: contrastive-unpaired-translation
description: "Routes CUT/FastCUT/SinCUT workflows, dataset preparation, and
  launcher presets for the contrastive-unpaired-translation repository."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Contrastive Unpaired Translation

Use this repo skill for the CUT family of image-to-image translation workflows in this checkout: CUT, FastCUT, and SinCUT; dataset preparation and layout checks; and preset experiment command generation.

## Start here

- Read `references/repo-provenance.md` when you need to confirm whether this skill matches the current checkout or before refreshing the skill.
- Use `scripts/check_runtime.py` when you want a quick import and CLI smoke check from a repo root.
- Read `references/troubleshooting.md` when smoke checks, checkpoint paths, legacy imports, or launcher commands misbehave.
- If you only want the main model workflows, go to `sub-skills/translation-workflows/`.
- If you need dataset conversion or folder-layout prep, go to `sub-skills/data-preparation/`.
- If you want preset command strings or launcher behavior, go to `sub-skills/experiment-launchers/`.

## Install and smoke check

The checked code runs from a Python environment with a compatible PyTorch and torchvision build plus the small runtime dependencies used by the repo scripts.

Typical install shape:

1. Create an isolated Python environment.
2. Install a CUDA-capable or CPU-compatible `torch`/`torchvision` pair for your host.
3. Install the repository runtime dependencies from `requirements.txt`.
4. Add `opencv-python-headless` when you plan to use the dataset-preparation helpers that import `cv2`.

A minimal smoke check is:

```bash
python scripts/check_runtime.py --repo-root .
```

If you only need the CLI entry points, `python train.py --help` and `python test.py --help` are the quickest verified checks.

## What this skill covers

- Training and testing CUT/FastCUT on unaligned datasets.
- Switching CUT mode between CUT and FastCUT.
- SinCUT single-image translation defaults and workflow notes.
- Loading checkpoints and writing results to `checkpoints/` and `results/`.
- Visualizer/HTML output behavior and visdom usage.
- Dataset helpers for Cityscapes, aligned side-by-side pairs, and cat-face cropping.
- Launcher command presets for `python -m experiments`.

## What this skill does not promise

- It does not promise the stale `--model test` example from upstream README text; this checkout has no `models/test_model.py`.
- It does not promote legacy CycleGAN as a first-class supported route. The legacy code is noted in troubleshooting only because it still exists in the checkout but has incomplete option wiring.
- It does not require or bundle network download scripts for large datasets.

## Routes

### `sub-skills/translation-workflows/`
Read this for CUT/FastCUT/SinCUT model selection, option families, checkpoint loading, output inspection, and the public training/test CLI.

### `sub-skills/data-preparation/`
Read this for dataset directory structure, Cityscapes preparation, A/B pair assembly, aligned side-by-side exports, and grumpifycat-style image cropping.

### `sub-skills/experiment-launchers/`
Read this for safe command generation, launcher presets, GPU ID selection rules, and the `python -m experiments` CLI shape.

## Freshness check

Before you trust the route map, compare the current checkout against `references/repo-provenance.md`. If the commit or evidence paths changed, refresh this skill rather than assuming the guidance is still current.
