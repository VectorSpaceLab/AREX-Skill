# Workflows

## 1) Convert raw TuSimple labels

The raw TuSimple archive should contain the label JSON files at the archive root and the lane-image tree referenced by `raw_file` entries. The converter reads each JSON line, expects `raw_file`, `h_samples`, and `lanes`, and skips `-2` lane coordinates when drawing.

Run the bundled converter on the unzipped archive root:

```bash
python skills/disco/lanenet-lane-detection/sub-skills/data-preparation/scripts/generate_tusimple_dataset.py \
  --src_dir /path/to/unzipped_tusimple
```

What it creates:
- `training/gt_image/` with the source frames copied as PNGs
- `training/gt_binary_image/` with binary lane masks
- `training/gt_instance_image/` with lane-instance masks
- `training/train.txt` with one row per generated sample
- `training/` and `testing/` copies of the original JSON label files

Upstream note: the 2018.12.13 update only automated the training-sample conversion and `training/train.txt`. If you need a fixed validation or test split, create those list files yourself or let the TFRecord producer regenerate them later.

## 2) Stage the dataset for TFRecord generation

The TFRecord producer expects a dataset root that contains these siblings at the top level:

- `gt_image/`
- `gt_binary_image/`
- `gt_instance_image/`
- `train.txt`
- `val.txt`
- `test.txt`

The easiest path is to point the TFRecord step at the raw archive's `training/` folder after conversion. That folder already contains the `gt_*` directories and the generated `train.txt`.

If you prefer a separate dataset root, copy or symlink the three `gt_*` folders and keep the list files beside them. Do not leave the shipped `ROOT_PATH` placeholders in place.

## 3) Generate TFRecords

The bundled wrapper resolves the repository root, loads the LaneNet config in-memory, and validates the dataset layout before calling the producer.

```bash
python skills/disco/lanenet-lane-detection/sub-skills/data-preparation/scripts/make_tusimple_tfrecords.py \
  --data-dir /path/to/unzipped_tusimple/training
```

If you already curated a custom dataset root, point `--data-dir` at that root instead. It must contain `gt_image/`, `gt_binary_image/`, and `gt_instance_image/`.

Expected TFRecord outputs:
- `tfrecords/tusimple_train.tfrecords`
- `tfrecords/tusimple_val.tfrecords`
- `tfrecords/tusimple_test.tfrecords`

## 4) Validate the prepared layout

Recommended checks:

1. Confirm the three `gt_*` folders exist and share the same basenames.
2. Confirm every row in each list file has exactly three paths.
3. Confirm no row still contains `ROOT_PATH` or `REPO_ROOT_PATH` placeholders.
4. Confirm the TFRecords can be opened by the LaneNet feeder.

Optional feeder smoke after generation:

```bash
PYTHONPATH=$PWD python - <<'PY'
from data_provider.lanenet_data_feed_pipline import LaneNetDataFeeder
feeder = LaneNetDataFeeder(flags='train')
print('train batches:', len(feeder))
PY
```

## Recovery rules

- If `train.txt`, `val.txt`, or `test.txt` are missing, the producer can auto-split from `gt_image/` as long as the three `gt_*` folders exist.
- If only some list files exist, delete the stale trio first if you want the producer to regenerate all three.
- If the sample data tree still uses `image/` instead of `gt_image/`, rename or restage it before TFRecord generation.
