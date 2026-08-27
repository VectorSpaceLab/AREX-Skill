---
name: data-providers-and-launchers
description: "Work with tf_unet data providers, toy generators, paired image
  files, and launcher-style dataset workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: GPL 3.0
---

# data-providers-and-launchers

Use this sub-skill when the task is about `BaseDataProvider`, `SimpleDataProvider`, `ImageDataProvider`, `GrayScaleDataProvider`, `RgbDataProvider`, toy data generation, TIFF mask pairing, or launcher-style dataset preparation.

If the question is really about the model graph, loss, optimizer, or checkpointing, switch to `../training-and-inference/SKILL.md`.

## Start here

- Read `references/data-formats.md` for shapes, label conventions, and file layouts.
- Read `references/workflows.md` for the toy, paired-image, and launcher-style workflows.
- Run `scripts/smoke_data_providers.py` when you want to validate provider shapes on synthetic fixtures.
- If the environment itself is failing, run the root smoke helper `../../scripts/check_tf_unet_env.py` first.

## Core decisions

- `BaseDataProvider` normalizes the absolute value of the data and then scales it into a 0-1 range.
- `ImageDataProvider` expects matching data and mask file names with the configured suffixes.
- The toy generators are easiest to use for tiny inspections when you keep `border` small enough for the chosen image size.
- `GrayScaleDataProvider` and `RgbDataProvider` are the safest way to create synthetic fixtures for quick smoke checks.
- External HDF5 workflows are format patterns, not bundled data; document them, but do not assume the files are present.

## What to mention in answers

- `SimpleDataProvider` is for already-prepared arrays; make sure the label shape matches the class layout you want.
- `ImageDataProvider` infers channel and class counts from the first matched image pair.
- `create_image_and_label(...)` and the toy data providers can be used to generate quick segmentation fixtures.
- The dataset-specific launcher patterns in this package are useful references even when the original data is unavailable.

## Bundled references

- `references/data-formats.md` — read for array shapes, mask/file suffixes, and launcher data layouts.
- `references/workflows.md` — read for NumPy, TIFF, and toy-generator recipes.
- `references/troubleshooting.md` — read when you hit file layout, shape, size, or dependency issues.

## Bundled script

- `scripts/smoke_data_providers.py` — run to validate synthetic NumPy, toy-generator, and paired-image fixtures.

## Common safety notes

- Keep the toy generator sizes large enough for the chosen `border` and `cnt` settings.
- Do not point future agents at the original checkout's dataset files as if they were bundled runtime assets.
- If the task is about a launcher workflow that needs external data, document the required file layout first and only then decide whether a synthetic smoke is possible.
