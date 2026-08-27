# Data Layout Reference

## Purpose

Read this before pointing the repo at a dataset or trying to interpret cache and result files.

## COCO layout expected by the shipped code

The shipped dataset class expects this structure under the configured `data_dir`:

```text
data/coco/
  annotations/
    instances_trainval2014.json
    instances_minival2014.json
    instances_testdev2017.json
  images/
    trainval2014/
    minival2014/
    testdev2017/
```

### Split mapping

| Internal split | COCO folder | Annotation file |
| --- | --- | --- |
| `trainval` | `trainval2014` | `instances_trainval2014.json` |
| `minival` | `minival2014` | `instances_minival2014.json` |
| `testdev` | `testdev2017` | `instances_testdev2017.json` |

## Cache and output layout

```text
cache/
  coco_trainval.pkl
  coco_minival.pkl
  coco_testdev.pkl
  nnet/
    <snapshot_name>/
      <snapshot_name>_<iter>.pkl
results/
  <snapshot_name>/
    <iter>/
      <split>/
        results.json
        debug/        # only when --debug is used
      <split>/<suffix>/
        results.json
        debug/
```

## What the cache files mean

- `cache/coco_<split>.pkl` stores extracted detections and image IDs for the selected split.
- The file is created lazily the first time the dataset is loaded.
- The cache is keyed by the split name and the configured `data_dir`.

## What the result files mean

- `results.json` is COCO-format detections written by the evaluation pipeline.
- `debug/` contains visualization images and PDFs for sampled detections when `--debug` is used.
- `testdev` does not have ground-truth COCO evaluation in this repo, so the written result file is the main artifact.

## Common layout mistakes

- Placing annotation JSON files somewhere other than `data/coco/annotations/`.
- Leaving images in the COCO download tree instead of copying them into the split-specific folders.
- Setting `data_dir` so it does not line up with the config's relative `../data` default.
- Deleting `cache/` or `results/` and then expecting the repo to find previous checkpoints or evaluation outputs automatically.
