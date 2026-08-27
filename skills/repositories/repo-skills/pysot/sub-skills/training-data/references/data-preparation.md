# PySOT training data preparation

PySOT training consumes cropped SiamFC-style search images plus annotation JSON files. The crop helpers are large-data, large-IO scripts: run them only after the user supplies raw datasets, disk space, and permission to create or overwrite `crop511`/JSON outputs.

All commands below are intended to run from the dataset-specific directory under a PySOT checkout, for example `training_dataset/vid`. Use a clean working tree or a separate data workspace because several recipes create symlinks, write `*.json`, and fill `crop511/` with many JPEGs.

## Universal outputs expected by training

- Crop root: usually `training_dataset/<dataset>/crop511`.
- Annotation JSON: e.g. `training_dataset/vid/train.json`, `training_dataset/det/train.json`, `training_dataset/yt_bb/train.json`, or `training_dataset/coco/train2017.json`.
- Crop image names: `{frame:06d}.{track}.x.jpg`; helper scripts also emit `.z.jpg`, but `TrkDataset` loads `.x.jpg` paths for both template and search samples.
- Config entries: `cfg.DATASET.NAMES` selects dataset names; each selected dataset has `ROOT`, `ANNO`, `FRAME_RANGE`, and `NUM_USE` fields. See [data-formats.md](data-formats.md).

## VID / ILSVRC video detection

Purpose: video tracking-style clips with frame ranges.

Raw layout actions:

```bash
cd training_dataset/vid
# After obtaining and extracting ILSVRC2015_VID.tar.gz:
ln -sfb "$PWD/ILSVRC2015/Annotations/VID/train/ILSVRC2015_VID_train_0000" ILSVRC2015/Annotations/VID/train/a
ln -sfb "$PWD/ILSVRC2015/Annotations/VID/train/ILSVRC2015_VID_train_0001" ILSVRC2015/Annotations/VID/train/b
ln -sfb "$PWD/ILSVRC2015/Annotations/VID/train/ILSVRC2015_VID_train_0002" ILSVRC2015/Annotations/VID/train/c
ln -sfb "$PWD/ILSVRC2015/Annotations/VID/train/ILSVRC2015_VID_train_0003" ILSVRC2015/Annotations/VID/train/d
ln -sfb "$PWD/ILSVRC2015/Annotations/VID/val" ILSVRC2015/Annotations/VID/train/e
ln -sfb "$PWD/ILSVRC2015/Data/VID/train/ILSVRC2015_VID_train_0000" ILSVRC2015/Data/VID/train/a
ln -sfb "$PWD/ILSVRC2015/Data/VID/train/ILSVRC2015_VID_train_0001" ILSVRC2015/Data/VID/train/b
ln -sfb "$PWD/ILSVRC2015/Data/VID/train/ILSVRC2015_VID_train_0002" ILSVRC2015/Data/VID/train/c
ln -sfb "$PWD/ILSVRC2015/Data/VID/train/ILSVRC2015_VID_train_0003" ILSVRC2015/Data/VID/train/d
ln -sfb "$PWD/ILSVRC2015/Data/VID/val" ILSVRC2015/Data/VID/train/e
```

Preprocess:

```bash
python parse_vid.py          # writes vid.json from XML annotations
python par_crop.py 511 12    # writes crop511/<subset>/<video>/*.x.jpg and *.z.jpg
python gen_json.py           # writes train.json and val.json
```

Side effects and checks:

- `ln -sfb` can replace existing symlinks; inspect targets before running in a shared data directory.
- `parse_vid.py` expects annotation subfolders named `a` through `e` under `ILSVRC2015/Annotations/VID/train`.
- `gen_json.py` reads `vid.json`; if `vid.json` is stale, regenerate it after changing raw data or symlinks.
- Default config uses `VID.FRAME_RANGE = 100` and `VID.NUM_USE = 100000`.

## DET / ILSVRC object detection

Purpose: still-image object detection converted to one-frame tracks.

Raw layout actions:

```bash
cd training_dataset/det
# After obtaining and extracting ILSVRC2015_DET.tar.gz:
ln -sfb "$PWD/ILSVRC/Annotations/DET/train/ILSVRC2013_train" ILSVRC/Annotations/DET/train/a
ln -sfb "$PWD/ILSVRC/Annotations/DET/train/ILSVRC2014_train_0000" ILSVRC/Annotations/DET/train/b
ln -sfb "$PWD/ILSVRC/Annotations/DET/train/ILSVRC2014_train_0001" ILSVRC/Annotations/DET/train/c
ln -sfb "$PWD/ILSVRC/Annotations/DET/train/ILSVRC2014_train_0002" ILSVRC/Annotations/DET/train/d
ln -sfb "$PWD/ILSVRC/Annotations/DET/train/ILSVRC2014_train_0003" ILSVRC/Annotations/DET/train/e
ln -sfb "$PWD/ILSVRC/Annotations/DET/train/ILSVRC2014_train_0004" ILSVRC/Annotations/DET/train/f
ln -sfb "$PWD/ILSVRC/Annotations/DET/train/ILSVRC2014_train_0005" ILSVRC/Annotations/DET/train/g
ln -sfb "$PWD/ILSVRC/Annotations/DET/train/ILSVRC2014_train_0006" ILSVRC/Annotations/DET/train/h
ln -sfb "$PWD/ILSVRC/Annotations/DET/val" ILSVRC/Annotations/DET/train/i
ln -sfb "$PWD/ILSVRC/Data/DET/train/ILSVRC2013_train" ILSVRC/Data/DET/train/a
ln -sfb "$PWD/ILSVRC/Data/DET/train/ILSVRC2014_train_0000" ILSVRC/Data/DET/train/b
ln -sfb "$PWD/ILSVRC/Data/DET/train/ILSVRC2014_train_0001" ILSVRC/Data/DET/train/c
ln -sfb "$PWD/ILSVRC/Data/DET/train/ILSVRC2014_train_0002" ILSVRC/Data/DET/train/d
ln -sfb "$PWD/ILSVRC/Data/DET/train/ILSVRC2014_train_0003" ILSVRC/Data/DET/train/e
ln -sfb "$PWD/ILSVRC/Data/DET/train/ILSVRC2014_train_0004" ILSVRC/Data/DET/train/f
ln -sfb "$PWD/ILSVRC/Data/DET/train/ILSVRC2014_train_0005" ILSVRC/Data/DET/train/g
ln -sfb "$PWD/ILSVRC/Data/DET/train/ILSVRC2014_train_0006" ILSVRC/Data/DET/train/h
ln -sfb "$PWD/ILSVRC/Data/DET/val" ILSVRC/Data/DET/train/i
```

Preprocess:

```bash
python par_crop.py 511 12    # writes crop511/<subset>/<image-id>/*.x.jpg and *.z.jpg
python gen_json.py           # writes train.json and val.json
```

Side effects and checks:

- DET `gen_json.py` creates one pseudo-frame (`000000`) per object, with track ids formatted as two digits.
- The crop script expects matching XML and JPEG roots under the `ILSVRC` directory.
- Default config uses `DET.FRAME_RANGE = 1` and `DET.NUM_USE = -1`.

## COCO 2017

Purpose: still-image objects converted to one-frame tracks.

Raw layout actions:

```bash
cd training_dataset/coco
# After obtaining train2017.zip, val2017.zip, and annotations_trainval2017.zip:
unzip train2017.zip
unzip val2017.zip
unzip annotations_trainval2017.zip
cd pycocotools && make && cd ..
```

Preprocess:

```bash
python par_crop.py 511 12    # writes crop511/train2017/<image-id> and crop511/val2017/<image-id>
python gen_json.py           # writes train2017.json and val2017.json
```

Side effects and checks:

- `pycocotools` must import before the COCO crop/json scripts run. Legacy code may rely on old NumPy aliases; prefer a compatible environment if `np.float` errors appear.
- Default training config points at `training_dataset/coco/crop511` and `training_dataset/coco/train2017.json`, not `val2017.json`.
- Default config uses `COCO.FRAME_RANGE = 1` and `COCO.NUM_USE = -1`.

## YouTube-BB

Purpose: YouTube-BoundingBoxes converted to object tracks. This is the heaviest bundled preparation recipe.

Raw label steps:

```bash
cd training_dataset/yt_bb
# After obtaining yt_bb_detection_train.csv.gz and yt_bb_detection_validation.csv.gz:
gzip -d yt_bb_detection_train.csv.gz
gzip -d yt_bb_detection_validation.csv.gz
```

Raw image download/crop route:

```bash
# From a parent workspace, after installing the external youtube-bb utility:
python download_detection.py ../ 12
cd ../training_dataset/yt_bb
python par_crop.py
python gen_json.py
```

Side effects and checks:

- Expect very large downloads and long runtime; original guidance estimated hundreds of GB and about a day for crop/json work.
- The repository guidance warned that an old pre-cropped YouTube-BB link was incorrect; if the user supplies pre-cropped data, verify sample images and JSON rather than trusting provenance.
- `checknum.py` can count downloaded images, but it does not prove that all crops and JSON entries are valid.
- Default config uses `YOUTUBEBB.FRAME_RANGE = 3` and `YOUTUBEBB.NUM_USE = -1`.

## Before training

Run the validator after creating or receiving data:

```bash
python scripts/validate_training_config.py \
  --repo-root <pysot-checkout> \
  --config <config.yaml> \
  --check-files
```

Passing this validator only proves config structure and configured paths. It does not prove that every annotation entry has a readable crop image; for a suspected bad dataset, inspect a few JSON entries and confirm each corresponding `{frame:06d}.{track}.x.jpg` file exists under the configured `ROOT`.
