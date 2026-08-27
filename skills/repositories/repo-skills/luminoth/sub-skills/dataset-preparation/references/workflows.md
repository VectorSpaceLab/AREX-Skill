# Dataset Preparation Workflows

## Purpose

Use this reference for the concrete `lumi dataset transform` and `lumi dataset
merge` flows.

## Transform flow

`lumi dataset transform` converts one or more source splits into TFRecords and a
`classes.json` file. The command uses a reader selected with `--type` and a
source directory passed through `--data-dir`.

Common flags:

- `--type`: reader type. Known built-ins are `pascal`, `imagenet`, `coco`,
  `openimages`, `csv`, `flat`, and `taggerine`.
- `--data-dir`: source dataset root.
- `--output-dir`: destination directory for TFRecords and `classes.json`.
- `--split`: one or more splits to transform.
- `--only-classes`: comma-separated class whitelist.
- `--only-images`: image-id whitelist.
- `--limit-examples`: stop after N images.
- `--class-examples`: try to collect roughly N examples per class.
- `--override`: reader-specific constructor values.
- `--debug`: verbose logging.

Example:

```bash
lumi dataset transform \
  --type pascal \
  --data-dir ./VOCdevkit/VOC2012 \
  --output-dir ./tf \
  --split train --split val
```

### What the command writes

For each split, the writer creates:

- one `<split>.tfrecords` file,
- one `classes.json` file shared by the output directory.

The TFRecord payload is a `tf.train.SequenceExample` with context features for
`image_raw`, `filename`, `width`, `height`, and `depth`, plus a per-object
sequence for `label`, `xmin`, `ymin`, `xmax`, and `ymax`.

## Merge flow

`lumi dataset merge` concatenates already converted TFRecord files into a new
TFRecord file. It does not inspect the dataset layout; it only reads TFRecord
records and writes them to the destination.

Example:

```bash
lumi dataset merge \
  ./a/train.tfrecords ./b/train.tfrecords ./merged/train.tfrecords
```

## Reader selection hints

- Use `pascal` for VOC-style `ImageSets/Main`, `JPEGImages`, and `Annotations`
  folders.
- Use `imagenet` for ImageNet DET layouts under `ImageSets/DET`, `Data/DET`,
  and `Annotations/DET`.
- Use `coco` for COCO JSON annotations plus split-specific image directories.
- Use `csv` when annotations live in `{split}.csv` and images are grouped under
  `{split}/`.
- Use `flat` when each split directory contains images with sidecar JSON
  annotations.
- Use `taggerine` when annotations are stored as Taggerine-style JSON files.
- Use `openimages` only when the CSV metadata files and OpenImages access are
  already prepared.

## Why `--class-examples` matters

`--class-examples` is not a hard exact-count guarantee. The reader will stop
when its heuristics consider each class sufficiently represented, but the final
counts can vary with the dataset structure.

## What to read next

- `references/data-formats.md` for source layout details.
- `references/troubleshooting.md` when a reader cannot find annotations,
  columns, or images.
- `scripts/validate_dataset_layout.py` for a safe preflight.
