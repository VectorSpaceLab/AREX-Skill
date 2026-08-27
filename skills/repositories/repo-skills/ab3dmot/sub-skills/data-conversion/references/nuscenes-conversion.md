# nuScenes conversion for AB3DMOT

AB3DMOT runs nuScenes tracking through a KITTI-like intermediate layout. Raw nuScenes data and raw nuScenes detector JSON must be converted before `main.py` can use them.

## Required raw-data tree

Place or symlink nuScenes v1.0 data under:

```text
data/nuScenes/data/
  samples/
  sweeps/
  v1.0-mini/        # optional for other tools; AB3DMOT docs target full v1.0
  v1.0-trainval/
  v1.0-test/
```

AB3DMOT conversion writes a KITTI-like tree under:

```text
data/nuScenes/nuKITTI/
  tracking/
    produced/
      correspondence/
      split/
    val/
      calib/
      image_02/
      label_02/
      oxts/
      velodyne/
    test/
      calib/
      image_02/
      oxts/
      velodyne/
```

`main.py --dataset nuScenes` reads `data/nuScenes/nuKITTI/tracking/<split>` plus `data/nuScenes/detection/<det_name>_<category>_<split>`.

## Optional dependencies

The nuScenes route needs the repo's base dependencies plus the nuScenes extras:

```text
nuscenes-devkit==1.1.9
motmetrics<=1.1.3
pandas>=0.24
fire
pyquaternion
```

If a task is only validating AB3DMOT detection rows, these optional packages are not needed. If a task invokes `scripts/nuScenes/export_kitti.py` or official nuScenes evaluation, they are required.

## Convert nuScenes ground truth to KITTI-like tracking data

After raw data is available, build the KITTI-like tracking tree:

```bash
python scripts/nuScenes/export_kitti.py nuscenes_gt2kitti_trk --split val
python scripts/nuScenes/export_kitti.py nuscenes_gt2kitti_trk --split test
```

This is a dataset-writing operation. It can copy/convert images, lidar, calibration, labels, ego poses, split files, and correspondence files. Run it only when the target data root and disk budget are correct.

## Convert nuScenes detector JSON to AB3DMOT inputs

For a detector result JSON at:

```text
data/nuScenes/data/produced/results/detection/<detname>/results_val.json
```

use the converter to write KITTI object-format detection files:

```bash
python scripts/nuScenes/export_kitti.py nuscenes_obj_result2kitti --result_name <detname> --split val
```

Then convert those frame-wise KITTI object results into AB3DMOT per-sequence detection inputs:

```bash
python scripts/pre_processing/convert_det2input.py --dataset nuScenes --split val --det_name <detname>
```

Expected AB3DMOT detector folders include:

```text
data/nuScenes/detection/<detname>_Car_val/
data/nuScenes/detection/<detname>_Pedestrian_val/
data/nuScenes/detection/<detname>_Truck_val/
data/nuScenes/detection/<detname>_all_val/
```

Validate representative sequence files after conversion:

```bash
python3 sub-skills/data-conversion/scripts/validate_ab3dmot_detection.py \
  --dataset nuScenes data/nuScenes/detection/<detname>_Car_val/scene-0003.txt
```

## Track with converted nuScenes inputs

After data and detector folders exist, route to tracking-pipeline. Typical commands are:

```bash
python main.py --dataset nuScenes --det_name megvii --split val
python main.py --dataset nuScenes --det_name centerpoint --split val
```

The default nuScenes config tracks seven categories: `Car`, `Pedestrian`, `Bicycle`, `Motorcycle`, `Bus`, `Trailer`, and `Truck`.

## Conversion method names exposed by the Fire CLI

The conversion script wraps a `KittiConverter` class. Common methods used by AB3DMOT workflows include:

- `nuscenes_gt2kitti_trk`: raw nuScenes ground truth to KITTI-like tracking tree.
- `nuscenes_obj_result2kitti`: raw nuScenes detection result JSON to KITTI object-result files.
- `kitti_trk_result2nuscenes`: AB3DMOT KITTI-like tracking results to nuScenes tracking JSON for evaluation/submission.

Evaluation/result export details are owned by the evaluation-visualization sub-skill.

## Cautions

- The converter assumes front camera `CAM_FRONT` and lidar `LIDAR_TOP` by default.
- Official test-set metrics require the nuScenes/eval.ai server; local test labels are not available.
- Do not run conversion against a partially downloaded raw dataset; missing samples can fail late after many writes.
- Use explicit `--split` and `--result_name` values. Defaults are convenient for Megvii validation but are easy to misuse for custom detectors.
