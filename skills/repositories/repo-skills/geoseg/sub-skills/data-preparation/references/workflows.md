# Data preparation workflows

## 1. Acquire and stage data

Download or obtain the datasets from their official providers outside this
skill. Keep the raw tree read-only and create a separate processed tree. Do not
mix datasets, urban/rural domains, or eroded/non-eroded masks in one output
directory.

Before conversion, inspect a few files and confirm stems:

```bash
find /abs/data/LoveDA/Train -type f | sort | head
find /abs/data/vaihingen/train_images -maxdepth 1 -type f -name '*.tif' | sort | head
find /abs/data/potsdam/train_images -maxdepth 1 -type f -name '*_RGB.tif' | sort | head
find /abs/data/uavid/uavid_train_val -mindepth 2 -maxdepth 3 -type f | sort | head
```

The scripts are runnable from any current working directory. Paths are
resolved by the shell as supplied; the scripts do not assume the GeoSeg repo
is the current directory.

## 2. Convert LoveDA masks first

Run once per domain/split containing masks:

```bash
python /path/to/convert_loveda_masks.py \
  --mask-dir /abs/data/LoveDA/Train/Rural/masks_png \
  --output-mask-dir /abs/data/LoveDA/Train/Rural/masks_png_convert
python /path/to/convert_loveda_masks.py \
  --mask-dir /abs/data/LoveDA/Train/Urban/masks_png \
  --output-mask-dir /abs/data/LoveDA/Train/Urban/masks_png_convert
python /path/to/convert_loveda_masks.py \
  --mask-dir /abs/data/LoveDA/Val/Rural/masks_png \
  --output-mask-dir /abs/data/LoveDA/Val/Rural/masks_png_convert
python /path/to/convert_loveda_masks.py \
  --mask-dir /abs/data/LoveDA/Val/Urban/masks_png \
  --output-mask-dir /abs/data/LoveDA/Val/Urban/masks_png_convert
```

The command creates both `masks_png_convert/` and the sibling
`masks_png_convert_rgb/`. It validates all source masks before writing any
output. If a conversion already exists, either use a new destination or pass
`--overwrite` deliberately. Then verify each converted directory has the same
stems as its `images_png` directory; conversion does not repair missing images.

## 3. Split Vaihingen

Training patches (raw color masks):

```bash
python /path/to/split_vaihingen_patches.py \
  --img-dir /abs/data/vaihingen/train_images \
  --mask-dir /abs/data/vaihingen/train_masks \
  --output-img-dir /abs/data/vaihingen/train/images_1024 \
  --output-mask-dir /abs/data/vaihingen/train/masks_1024 \
  --mode train --split-size 1024 --stride 512
```

Validation/test patches from eroded masks:

```bash
python /path/to/split_vaihingen_patches.py \
  --img-dir /abs/data/vaihingen/test_images \
  --mask-dir /abs/data/vaihingen/test_masks_eroded \
  --output-img-dir /abs/data/vaihingen/test/images_1024 \
  --output-mask-dir /abs/data/vaihingen/test/masks_1024 \
  --mode val --split-size 1024 --stride 1024 --eroded
```

For RGB ground-truth visualization, use the non-eroded color masks and a
separate destination:

```bash
python /path/to/split_vaihingen_patches.py \
  --img-dir /abs/data/vaihingen/test_images \
  --mask-dir /abs/data/vaihingen/test_masks \
  --output-img-dir /abs/data/vaihingen/test/images_1024 \
  --output-mask-dir /abs/data/vaihingen/test/masks_1024_rgb \
  --mode val --split-size 1024 --stride 1024 --gt
```

The output image suffix is `.tif`; ordinary masks are `.png`. A pair with a
missing stem or a shape mismatch stops before that pair is processed. Use
`--val-scale` only when a downstream config expects a scaled validation image.

## 4. Split Potsdam

Select the source imagery explicitly:

```bash
python /path/to/split_potsdam_patches.py \
  --img-dir /abs/data/potsdam/train_images \
  --mask-dir /abs/data/potsdam/train_masks \
  --output-img-dir /abs/data/potsdam/train/images_1024 \
  --output-mask-dir /abs/data/potsdam/train/masks_1024 \
  --mode train --split-size 1024 --stride 1024 --rgb-image
```

For an eroded validation set, use `--eroded` and an input directory containing
`<stem>_label_noBoundary.tif`. For visualization use `--gt` and a separate
mask destination. Do not combine `--rgb-image` with a directory that only has
`_IRRG.tif`; the failure should be fixed by selecting the correct raw input,
not by renaming masks.

## 5. Split UAVid nested sequences

```bash
python /path/to/split_uavid_patches.py \
  --input-dir /abs/data/uavid/uavid_train_val \
  --output-img-dir /abs/data/uavid/train_val/images \
  --output-mask-dir /abs/data/uavid/train_val/masks \
  --mode train --split-size-h 1024 --split-size-w 1024 \
  --stride-h 1024 --stride-w 1024
```

Use separate output directories for `uavid_train`, `uavid_val`, and
`uavid_test`; the mode is a naming/data contract, not a download or split
operation. For a deliberate rectangular tiling, for example, use
`--split-size-h 64 --split-size-w 96 --stride-h 64 --stride-w 96`. The script
pads only bottom/right and emits no partial tile.

## 6. Validate before handoff

A minimal paired-file check (works for any two flat processed directories) is:

```bash
python - <<'PY'
from pathlib import Path
images = {p.stem for p in Path('/abs/data/uavid/train_val/images').glob('*.png')}
masks = {p.stem for p in Path('/abs/data/uavid/train_val/masks').glob('*.png')}
print('images', len(images), 'masks', len(masks), 'missing masks', sorted(images-masks)[:5],
      'missing images', sorted(masks-images)[:5])
assert images == masks
PY
```

For Vaihingen/Potsdam, remember images are `.tif` and masks `.png`; compare
stems, not filenames. Confirm a sample image and mask have equal height/width
and inspect `numpy.unique(mask)` for the expected label set. Only after this
handoff should the sibling [training](../../training/SKILL.md),
[model-and-config](../../model-and-config/SKILL.md), and
[evaluation-inference](../../evaluation-inference/SKILL.md) workflows consume
the processed directories.
