# MambaVision training data formats

## What the training script expects

The training entry point works from a dataset root plus split names.
The default split names are `train` and `validation`.

Important:
- `--data_dir` should point to the dataset root, not a class folder or a split folder.
- `--train-split` and `--val-split` are split names, not absolute paths.
- The common ImageNet-1K layout is ImageFolder-style directories with one class folder per label.

## Plain ImageFolder layout

A standard launch uses a tree like this:

```text
${DATA_DIR}/train/
  n01440764/
    image1.JPEG
    image2.JPEG
${DATA_DIR}/validation/
  n01440764/
    image3.JPEG
    image4.JPEG
```

If your validation split is named `val`, set `--val-split val` and use `val/` instead of `validation/`.

The loader expects:
- a top-level `train` split for training
- a top-level validation split that contains class subdirectories
- class names or a class map that are consistent across splits

## LMDB cache branch

The repo also supports an LMDB-backed path that caches ImageFolder contents.
This is still rooted in the same ImageFolder tree; it is not a different label format.

Typical cache outputs created on first access:

```text
${DATA_DIR}/train_faster_imagefolder.lmdb.pt
${DATA_DIR}/train_faster_imagefolder.lmdb/
${DATA_DIR}/val_faster_imagefolder.lmdb.pt
${DATA_DIR}/val_faster_imagefolder.lmdb/
```

The helper builds the cache from the source ImageFolder tree, stores a `.pt` snapshot, and then reuses the LMDB data on later runs.
Do not mix a stale cache with a different source tree.

## Split-name assumptions used by training

- Default training split: `train`
- Default validation split: `validation`
- Some dataset roots still use `val`; that is fine if you override `--val-split val`
- The fallback checks in the training script look for `train/` and then `val/` or `validation/` depending on the selected mode

## Validation loop expectations

The evaluation loader used during training follows the same split/root assumptions as the training loader.
Because `resolve_data_config` is used, the loader also respects the preset's image size, interpolation, mean, std, and crop percentage.

Practical consequences:
- validation uses the expected center-crop behavior from the preset
- image tensors are normalized with ImageNet statistics unless a preset overrides them
- if you change input size, the train and validation transforms change together

## Quick preflight checks

Before launching a long run, confirm:
- the dataset root exists
- the `train` split exists
- one validation split exists (`validation` or `val`)
- each split contains class subdirectories, not flat images
- the chosen split name matches the command line
- the dataset root and cache branch are not mixed accidentally
