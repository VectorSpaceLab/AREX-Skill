# PySOT training data formats

PySOT training data is loaded by `TrkDataset` and `SubDataset`. The loader does not discover datasets automatically; it follows the effective YACS config after `cfg.merge_from_file(<config>)`.

## Config contract

`cfg.DATASET.NAMES` is an ordered list/tuple of dataset names. For every name in that list, `cfg.DATASET.<NAME>` must provide:

| Field | Meaning | Common values |
| --- | --- | --- |
| `ROOT` | Crop root relative to the PySOT checkout root, or an absolute crop root. | `training_dataset/vid/crop511` |
| `ANNO` | Training annotation JSON relative to the checkout root, or an absolute JSON file. | `training_dataset/vid/train.json` |
| `FRAME_RANGE` | Maximum temporal index window used when choosing positive template/search pairs around a selected frame. | `VID: 100`, `YOUTUBEBB: 3`, still-image datasets: `1` |
| `NUM_USE` | Number of videos/items to sample from this subdataset before repetition. `-1` means use all items once per shuffle. | `VID: 100000`, others often `-1` |

Dataset defaults in the base config select `('VID', 'COCO', 'DET', 'YOUTUBEBB')`. Experiment config files may override `DATASET.NAMES` but often rely on inherited `ROOT`/`ANNO` defaults.

## Annotation JSON schema

The JSON is a nested dictionary:

```json
{
  "video_or_image_relative_dir": {
    "track_id": {
      "000000": [x1, y1, x2, y2],
      "000001": [x1, y1, x2, y2]
    }
  }
}
```

Rules enforced or assumed by the loader:

- Top-level keys are relative directories under the configured `ROOT`.
- Track keys are strings, typically zero-padded two-digit ids such as `"00"`.
- Frame keys must be numeric strings; the loader keeps keys for which `key.isdigit()` is true, converts them to integers, sorts them, and later formats them as six digits.
- Bboxes from the repository helpers are `[x1, y1, x2, y2]`. The loader also tolerates two-number size-like values in its zero-size filter, but the normal generated schema is four coordinates.
- Any bbox with `x2 - x1 <= 0` or `y2 - y1 <= 0` is filtered out before training. Tracks with no frames and videos with no tracks are removed.

## Crop image path contract

For a sampled `(video, track, frame)` the loader constructs:

```text
<ROOT>/<video>/<frame:06d>.<track>.x.jpg
```

Examples:

```text
training_dataset/vid/crop511/a/ILSVRC2015_train_00000000/000123.00.x.jpg
training_dataset/det/crop511/a/ILSVRC2013_train_00000001/000000.00.x.jpg
training_dataset/coco/crop511/train2017/000000391895/000000.00.x.jpg
training_dataset/yt_bb/crop511/yt_bb_detection_train/5/<youtube_id>/000012.03.x.jpg
```

The crop helpers also write `.z.jpg` files, but `SubDataset.path_format` is `{}.{}.{}.jpg` and `get_image_anno()` passes the suffix `x`. Therefore a dataset can contain `.z.jpg` files and still fail if the corresponding `.x.jpg` file is missing.

## Sampling behavior

- `SubDataset.shuffle()` repeats shuffled item indices until it reaches `NUM_USE`; with `NUM_USE = -1`, it uses the number of valid top-level videos/items.
- `TrkDataset` concatenates all selected subdatasets, then if `cfg.DATASET.VIDEOS_PER_EPOCH > 0`, uses that value as videos/items per epoch before multiplying by `cfg.TRAIN.EPOCH`.
- Positive pairs come from the same track within `FRAME_RANGE` around the template frame.
- Negative pairs are controlled by `cfg.DATASET.NEG`; the search image may come from a different selected subdataset.
- `cv2.imread()` is not checked before using image shapes. Missing or corrupt crop images usually surface later as `NoneType`/shape/augmentation errors, not as a clean file-not-found exception.

## Anchor/label shapes

`AnchorTarget` computes the number of anchors per location as:

```text
len(cfg.ANCHOR.RATIOS) * len(cfg.ANCHOR.SCALES)
```

This should match both `cfg.ANCHOR.ANCHOR_NUM` and, when present, `cfg.RPN.KWARGS.anchor_num`. The generated classification label has shape `(anchor_num, OUTPUT_SIZE, OUTPUT_SIZE)`, and regression labels have shape `(4, anchor_num, OUTPUT_SIZE, OUTPUT_SIZE)`.

## Safe validation

Use the bundled validator for structural checks:

```bash
python scripts/validate_training_config.py \
  --repo-root <pysot-checkout> \
  --config <config.yaml> \
  --check-files
```

If it fails with a missing `ROOT`/`ANNO` field, fix the config before debugging the data. If it passes but training still fails inside `TrkDataset.__getitem__`, sample a few JSON entries manually and verify that the computed `.x.jpg` files are readable with OpenCV.
