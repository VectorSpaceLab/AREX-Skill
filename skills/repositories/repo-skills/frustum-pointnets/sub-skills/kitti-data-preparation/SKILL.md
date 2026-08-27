---
name: kitti-data-preparation
description: "Validate KITTI object data and plan Frustum PointNets
  frustum-pickle preparation from ground-truth or RGB 2D boxes."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# KITTI data preparation

Use this route to validate KITTI Object Detection data, inspect detector rows,
and plan the repository's ground-truth or RGB-detection frustum extraction.
Do not start a multi-gigabyte conversion until the selected branch passes its
layout and schema checks.

## Workflow

1. Read [data formats](references/data-formats.md) and identify whether the
   input uses ground-truth 2D boxes or external RGB detections.
2. Run the non-destructive validator:

   ```bash
   python scripts/validate_kitti_layout.py \
     --dataset-root /data/KITTI/object \
     --index-file /data/splits/val.txt \
     --detector-file /data/detections/val.txt
   ```

   Omit `--detector-file` for a ground-truth branch. Add
   `--require-labels` for `train`/`val` generation. Use `--check-complete` only
   when every listed frame must be checked rather than sampled.
3. Read [workflows](references/workflows.md), select `train`, `val`, or
   `val_rgb_detection`, and stage output on a filesystem with enough space.
4. Verify the resulting sequential pickle stream before moving it into a
   training or inference workflow. Route training to `../training/SKILL.md`.

## Source-equivalent modes

| Mode | Required evidence | Output basename |
|---|---|---|
| train | training images, Velodyne, calibration, labels, train IDs | `frustum_{caronly|carpedcyc}_train.pickle` |
| val | training images, Velodyne, calibration, labels, val IDs | `frustum_{caronly|carpedcyc}_val.pickle` |
| val RGB detections | training images, Velodyne, calibration, detector rows, val IDs | `frustum_{caronly|carpedcyc}_val_rgb_detection.pickle` |

The standard all-mode command is estimated by the repository to generate about
4.7 GB. `--car_only` changes both the class whitelist and output prefix;
without it, Car, Pedestrian, and Cyclist are selected.

## Boundaries

The source targets Python 2 and uses `cPickle`. A Python-3 port must use an
explicit compatibility import and account for integer-division differences.
Layout and geometry checks are CPU-safe; they do not validate TensorFlow, CUDA,
or v2 custom operators. Read [troubleshooting](references/troubleshooting.md)
for malformed detector rows, missing labels, empty frustums, and partial
pickles. Route installation to `../runtime-and-custom-ops/SKILL.md` and KITTI
result scoring to `../inference-and-evaluation/SKILL.md`.
