# KITTI data layout for AB3DMOT

AB3DMOT's KITTI workflow combines external KITTI tracking data with repo-provided or user-provided detector text files.

## Required tracking tree

Place or symlink the official KITTI multi-object tracking dataset under `data/KITTI/tracking`:

```text
data/KITTI/
  tracking/
    training/
      calib/
      image_02/
      label_02/
      oxts/
      velodyne/
    testing/
      calib/
      image_02/
      oxts/
      velodyne/
  detection/
    pointrcnn_Car_val/
    pointrcnn_Pedestrian_val/
    pointrcnn_Cyclist_val/
    pointrcnn_Car_test/
    ...
```

For `--split val`, AB3DMOT uses the `training` subfolder and the validation sequence list hard-coded in the utility module. For `--split test`, it uses the `testing` subfolder and sequence ids `0000` through `0028`.

`main.py` does not fall back to the mini image folders used by the visualization helper. If only detector text files and mini images are present, command-level tracking will still fail because calibration and ego-motion files are missing from the expected tracking root.

## Supported KITTI detector/category combinations

The default KITTI config uses:

```yaml
dataset: KITTI
split: val
det_name: pointrcnn
cat_list: ['Car', 'Pedestrian', 'Cyclist']
```

Tracker parameter branches exist for `pointrcnn`, `pvrcnn`, and a `deprecated` detector name. In normal reproduced workflows, use PointRCNN:

```bash
python main.py --dataset KITTI --split val --det_name pointrcnn
python main.py --dataset KITTI --split test --det_name pointrcnn
```

AB3DMOT reads each category from a separate detection root such as `data/KITTI/detection/pointrcnn_Car_val`. Confirm that every configured category has a matching folder before running.

## KITTI-style detector conversion

If your detector outputs raw KITTI object-detection rows, convert them into AB3DMOT tracker input rows before tracking. AB3DMOT's conversion script expects detector object results under the KITTI object-result tree and writes category-specific per-sequence files under `data/KITTI/detection/`.

The conversion route is conceptually:

1. Ensure each detector frame file is in KITTI object detection format with class name, truncation, occlusion, alpha, 2D box, 3D box, rotation, and score.
2. Convert each object into the 15-column comma-separated AB3DMOT row.
3. Split output by category folder and, optionally, an `all` folder.
4. Validate representative output files with the bundled validator.

For already-converted repo detector files, only run the validator; do not reconvert.

## Quick preflight checklist

```bash
# validate one sequence/category input
python3 sub-skills/data-conversion/scripts/validate_ab3dmot_detection.py \
  --dataset KITTI data/KITTI/detection/pointrcnn_Car_val/0001.txt

# confirm expected tracking data roots before running main.py
ls data/KITTI/tracking/training/calib data/KITTI/tracking/training/image_02 data/KITTI/tracking/training/oxts
```

If preflight passes, route to the tracking-pipeline sub-skill to build and run the tracking command.

## What not to automate blindly

- Do not download KITTI from scripts without user consent; the official dataset is large and may require terms/account acceptance.
- Do not treat the presence of `data/KITTI/detection/` as proof that full tracking data is available.
- Do not use the KITTI test split for local metric validation; test labels are not available locally.
