---
name: data-preparation
description: "Prepare zi2zi paired glyph images and pickle streams from
  source/target fonts, charsets, labels, and rendered JPG directories."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# zi2zi data preparation

Use this sub-skill when the task is about creating or validating zi2zi input
data before training or inference. It covers the font-to-image renderer,
charset choices, label naming, JPG pair schema, `train.obj`/`val.obj` packaging,
and safe inspection of generated object files.

## Use this sub-skill when

- The user has source and target font files and wants zi2zi training images.
- The user needs to choose between `CN`, `CN_T`, `JP`, `KR`, or a custom charset.
- The task mentions `font2img.py`, `package.py`, `sample_dir`, `label`,
  `filter`, `shuffle`, `train.obj`, `val.obj`, or pickled `(label, bytes)`
  records.
- Generated data is empty, labels are wrong, glyphs are missing, or a `.obj`
  file cannot be read.

## Route elsewhere

- For training, fine-tuning, losses, label shuffling during training, or
  checkpoints, read [training-and-model](../training-and-model/SKILL.md).
- For checkpoint inference, interpolation, GIFs, or export, read
  [inference-and-export](../inference-and-export/SKILL.md).
- For Python/TensorFlow/SciPy compatibility that affects multiple workflows,
  read the root [compatibility](../../references/compatibility.md) reference.

## What zi2zi expects

- A rendered example is one JPG containing two square glyph canvases side by
  side: target style on the left, source style on the right.
- The filename must start with the integer embedding/style label followed by an
  underscore, for example `0_0000.jpg`.
- `package.py` scans `*.jpg` files in one directory, parses labels from the
  filename prefix, and writes pickled `(label, image_bytes)` records into
  `train.obj` and `val.obj`.
- `train.py` later expects those object files under `experiment/data/` unless
  the user deliberately changes the experiment layout.

## Standard workflow

1. Pick a source font and one or more target fonts.
2. Assign each target font a stable integer label. Avoid reusing a label for a
   different target style within the same training run.
3. Choose a built-in charset (`CN`, `CN_T`, `JP`, `KR`) or create a one-line
   UTF-8 text file for a custom character set.
4. Render paired JPGs with `font2img.py` semantics. Use `--filter=1` when the
   target font may be missing glyphs, and `--shuffle=1` when you want a random
   sample from the charset.
5. Package the rendered JPG directory into `train.obj` and `val.obj` with
   `package.py` semantics.
6. Inspect record counts and label distribution before training.

Read [preprocessing-workflow.md](references/preprocessing-workflow.md) for
complete command templates, multi-font labeling, and validation steps. Read
[data-formats.md](references/data-formats.md) for exact image/object schemas and
charset behavior. Read [troubleshooting.md](references/troubleshooting.md) when
fonts, charsets, filters, labels, or pickle streams fail.

## Bundled helpers

- [scripts/zi2zi_font_pair_planner.py](scripts/zi2zi_font_pair_planner.py)
  prints validated `font2img.py` and `package.py` command templates for one
  source font and one or more target fonts.
- [scripts/inspect_zi2zi_obj.py](scripts/inspect_zi2zi_obj.py) safely reads
  zi2zi `.obj` pickle streams from Python 3 and reports record counts, labels,
  byte sizes, and optional image dimensions.

## Quick checks before training

- The samples directory contains JPGs, not PNGs or nested directories.
- Every filename has an integer prefix before `_`.
- Label count equals or is less than `--embedding_num` planned for training.
- `train.obj` and `val.obj` both exist, even if the validation split is small.
- Inspecting a few records shows image bytes and expected labels.
- If validation is empty because the sample count is tiny and split randomness
  placed all examples in training, either accept that for a smoke test or create
  a deterministic tiny fixture outside the original script.
