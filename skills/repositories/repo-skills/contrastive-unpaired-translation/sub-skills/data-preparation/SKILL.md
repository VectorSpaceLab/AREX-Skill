---
name: data-preparation
description: "Routes dataset layout checks, Cityscapes preparation, pair
  assembly, aligned export, and cat-face crop workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# data-preparation

Use this sub-skill when the task is about shaping data for CUT, FastCUT, or SinCUT: building the expected folder layout, converting Cityscapes, assembling paired images, exporting aligned composites, or cropping cat faces for the grumpifycat example.

## Read this when

- The user needs to prepare a `trainA/trainB` or `testA/testB` dataset.
- The user needs the single-image dataset layout with exactly one image per domain.
- The user wants to convert Cityscapes into CUT-ready folders.
- The user wants to combine two directories into side-by-side pix2pix-style pairs.
- The user wants to build aligned `train` and `test` composite images from A/B folders.
- The user needs a cat-face crop helper for the grumpifycat workflow.

## What this sub-skill covers

- Dataset layout conventions from `docs/datasets.md` and the dataset loader modules.
- `scripts/prepare_cityscapes_dataset.py` for Cityscapes conversion.
- `scripts/combine_A_and_B.py` for paired A/B assembly.
- `scripts/make_dataset_aligned.py` for aligned composite exports.
- `scripts/detect_cat_face.py` for cat-face cropping.

## What this sub-skill does not cover

- Training, testing, checkpoint loading, or output inspection. Read `../translation-workflows/` for those tasks.
- Launcher presets or tmux orchestration. Read `../experiment-launchers/` for those tasks.
- Network download shell scripts. They are reference-only because they fetch external datasets.

## Use the bundled helpers

- `scripts/prepare_cityscapes_dataset.py` converts raw Cityscapes exports into CUT/pix2pix-style folders.
- `scripts/combine_A_and_B.py` builds paired composite images from two parallel trees.
- `scripts/make_dataset_aligned.py` exports side-by-side aligned images from `trainA/trainB` and `testA/testB`.
- `scripts/detect_cat_face.py` crops detected cat faces for the grumpifycat-style example.

## Recommended reading order

- `references/data-formats.md` for the exact folder structures and naming rules.
- `references/workflows.md` for end-to-end preparation recipes.
- `references/troubleshooting.md` for missing images, filename mismatches, and OpenCV/cascade issues.

## Common routing choices

- If the user only needs a data folder layout explanation, stay here and read `references/data-formats.md`.
- If the user also needs to train or test afterward, hand off to `../translation-workflows/` after the data is prepared.
- If the user wants to print experiment command strings, hand off to `../experiment-launchers/`.

## Quick reminders

- `data.unaligned_dataset.UnalignedDataset` expects unpaired folders such as `trainA` and `trainB`.
- `data.singleimage_dataset.SingleImageDataset` expects exactly one image in `trainA` and one in `trainB`.
- The bundled helpers are intentionally deterministic and self-contained so they do not depend on the original checkout.
- The network download scripts stay out of the runtime tree because they fetch external data and are not safe default helpers.
