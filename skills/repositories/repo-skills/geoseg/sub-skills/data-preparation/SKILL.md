---
name: data-preparation
description: "Prepare and validate GeoSeg LoveDA masks and Vaihingen, Potsdam,
  and UAVid image-mask patches with deterministic, path-explicit workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: GPL 3.0
---

# GeoSeg data preparation

Use this sub-skill to stage externally acquired datasets, convert LoveDA labels,
split ISPRS/UAVid imagery into loader-compatible patches, and diagnose pairing,
encoding, suffix, and shape failures. This skill does not download data, train a
model, load checkpoints, evaluate predictions, or run inference.

## Route first

- Read [data-formats.md](references/data-formats.md) for source trees,
  suffixes, dimensions, class values, palettes, and output schemas.
- Follow [workflows.md](references/workflows.md) for concrete commands and
  preflight/validation order.
- Use [troubleshooting.md](references/troubleshooting.md) for dependency,
  data/config, CLI, backend, and workflow failures.
- Run the bundled scripts from any current working directory with explicit
  input and output paths:
  - [`convert_loveda_masks.py`](scripts/convert_loveda_masks.py)
  - [`split_vaihingen_patches.py`](scripts/split_vaihingen_patches.py)
  - [`split_potsdam_patches.py`](scripts/split_potsdam_patches.py)
  - [`split_uavid_patches.py`](scripts/split_uavid_patches.py)

Conceptually hand processed directories to the sibling [training](../training/SKILL.md)
sub-skill only after paired-file and label checks. Route model/backbone and
config choices to [model-and-config](../model-and-config/SKILL.md), and route
checkpoint evaluation or inference rendering to
[evaluation-inference](../evaluation-inference/SKILL.md).

## Operating contract

1. Confirm dataset acquisition and preserve a read-only raw tree. Choose a
   separate processed output tree; never mix dataset families or eroded and
   non-eroded masks.
2. Inspect source stems and suffixes before running a splitter. The bundled
   scripts pair files by exact stem, sort them, validate all expected pairs,
   and fail loudly on missing partners rather than pairing by directory order.
3. Validate image/mask height and width and reject unsupported mask colors or
   label values. Mask resampling is nearest-neighbor; image resampling is
   bicubic. Never use bilinear/bicubic interpolation on class IDs.
4. Treat output directories as immutable by default. Existing outputs require
   a new destination or explicit `--overwrite`; writes use temporary files and
   atomic replacement. Do not point a training loader at a `--gt` RGB
   visualization directory.
5. Record dataset name/domain/split, raw and processed roots, selected suffix
   flags, tile and stride sizes, mode, label encoding, script command, and
   validation result in the handoff. Do not claim the dataset is valid based on
   file counts alone.

## Fast commands

LoveDA conversion (repeat for each Urban/Rural Train or Val mask directory):

```bash
python /path/to/convert_loveda_masks.py \
  --mask-dir /abs/data/LoveDA/Train/Rural/masks_png \
  --output-mask-dir /abs/data/LoveDA/Train/Rural/masks_png_convert
```

Vaihingen 1024 training patches:

```bash
python /path/to/split_vaihingen_patches.py \
  --img-dir /abs/data/vaihingen/train_images \
  --mask-dir /abs/data/vaihingen/train_masks \
  --output-img-dir /abs/data/vaihingen/train/images_1024 \
  --output-mask-dir /abs/data/vaihingen/train/masks_1024 \
  --mode train --split-size 1024 --stride 512
```

Potsdam RGB 1024 patches:

```bash
python /path/to/split_potsdam_patches.py \
  --img-dir /abs/data/potsdam/train_images \
  --mask-dir /abs/data/potsdam/train_masks \
  --output-img-dir /abs/data/potsdam/train/images_1024 \
  --output-mask-dir /abs/data/potsdam/train/masks_1024 \
  --mode train --split-size 1024 --stride 1024 --rgb-image
```

UAVid nested sequence patches:

```bash
python /path/to/split_uavid_patches.py \
  --input-dir /abs/data/uavid/uavid_train_val \
  --output-img-dir /abs/data/uavid/train_val/images \
  --output-mask-dir /abs/data/uavid/train_val/masks \
  --mode train --split-size-h 1024 --split-size-w 1024 \
  --stride-h 1024 --stride-w 1024
```

Use `--help` on each script to confirm defaults and flags. All four scripts
require explicit paths in this adapted runtime; this avoids silently writing
relative to an arbitrary checkout. `--mode` is retained for compatibility and
output semantics. Vaihingen/Potsdam train mode emits deterministic source,
horizontal-flip, and vertical-flip variants; validation/test emits one. UAVid
emits no augmentation, as in the source utility. The adaptations intentionally
do not reproduce source multiprocessing or random crop/car augmentation: they
prioritize reproducible, auditable patch production while preserving the
source flags and loader file contracts.

## Acceptance checks

A successful preparation handoff must include:

- source layout and external acquisition status;
- exact command and effective absolute input/output paths;
- counts of input pairs and output patches;
- image/mask stem equality in each processed directory;
- sample shapes and `numpy.unique`/palette validation;
- LoveDA indexed-vs-RGB distinction, or ISPRS/UAVid class mapping;
- tile/stride/padding and mode details;
- any skipped edge regions or rejected files;
- unresolved dataset or backend limitations.

The checkout had no bundled datasets, tests, docs, or examples beyond the
README/configs/tools/root scripts. LoveDA's validation dataset is constructed
at import and therefore requires an external Val layout. The verified
inspection environment was Python 3.8 with OpenCV/Pillow-compatible tooling;
this sub-skill scripts use only Python plus Pillow and NumPy. Do not infer that
training dependencies or optional `mamba_ssm` are installed from preprocessing
success.
