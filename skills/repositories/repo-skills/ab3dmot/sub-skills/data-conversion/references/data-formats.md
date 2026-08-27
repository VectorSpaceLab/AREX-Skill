# AB3DMOT detection and data formats

AB3DMOT consumes one comma-separated detection text file per sequence and per category. Each line is a detector object at one frame, converted into a compact 15-column tracker input row.

## Tracker input row

The conversion helper writes rows with this order:

| Column | Name | Type | Meaning |
| --- | --- | --- | --- |
| 0 | `frame` | integer | Frame index within the sequence. |
| 1 | `type_id` | integer | Dataset category id used by AB3DMOT. |
| 2 | `x1` | float | 2D bounding-box left pixel. |
| 3 | `y1` | float | 2D bounding-box top pixel. |
| 4 | `x2` | float | 2D bounding-box right pixel. |
| 5 | `y2` | float | 2D bounding-box bottom pixel. |
| 6 | `score` | float | Detector confidence. |
| 7 | `h` | float | 3D box height in camera coordinates. |
| 8 | `w` | float | 3D box width in camera coordinates. |
| 9 | `l` | float | 3D box length in camera coordinates. |
| 10 | `x` | float | 3D box center x in camera coordinates. |
| 11 | `y` | float | 3D box center y in camera coordinates. |
| 12 | `z` | float | 3D box center z in camera coordinates. |
| 13 | `ry` | float | Yaw angle around camera Y-axis. |
| 14 | `alpha` | float | Observation angle used as additional tracker info. |

`main.py` reads the full sequence file, selects rows for a frame, passes columns `7:14` to `AB3DMOT.track` as `dets`, and builds the seven-column `info` array from `alpha` plus columns `1:7`.

## Category ids

KITTI ids:

| id | Category |
| --- | --- |
| 1 | `Pedestrian` |
| 2 | `Car` |
| 3 | `Cyclist` |

nuScenes ids:

| id | Category |
| --- | --- |
| 1 | `Pedestrian` |
| 2 | `Car` |
| 3 | `Bicycle` |
| 4 | `Motorcycle` |
| 5 | `Bus` |
| 6 | `Trailer` |
| 7 | `Truck` |
| 8 | `Construction_vehicle` |
| 9 | `Barrier` |
| 10 | `Traffic_cone` |

The default nuScenes config tracks `Car`, `Pedestrian`, `Bicycle`, `Motorcycle`, `Bus`, `Trailer`, and `Truck`; detector folders for `Barrier`, `Construction_vehicle`, and `Traffic_cone` may exist but are not tracked unless the config is changed and tracker parameters are added.

## Detection folder naming

AB3DMOT expects category-specific detection roots built from:

```text
data/<dataset>/detection/<det_name>_<category>_<split>/<sequence>.txt
```

Examples:

```text
data/KITTI/detection/pointrcnn_Car_val/0001.txt
data/KITTI/detection/pointrcnn_Pedestrian_test/0008.txt
data/nuScenes/detection/megvii_Car_val/scene-0003.txt
data/nuScenes/detection/centerpoint_all_val/scene-0003.txt
```

`main.py` loops the configured categories and reads the category-specific folders, not just the `_all_` folder. The `_all_` folder is useful for inspection but does not replace category folders for normal tracking.

## Validation script

Use the bundled validator before running tracking:

```bash
python3 sub-skills/data-conversion/scripts/validate_ab3dmot_detection.py \
  --dataset KITTI \
  data/KITTI/detection/pointrcnn_Car_val/0001.txt
```

For multiple files:

```bash
python3 sub-skills/data-conversion/scripts/validate_ab3dmot_detection.py \
  --dataset nuScenes \
  data/nuScenes/detection/megvii_Car_val/scene-0003.txt \
  data/nuScenes/detection/megvii_Pedestrian_val/scene-0003.txt
```

The script checks column count, numeric parsing, nonnegative frame ids, category ids, positive 3D dimensions, and basic 2D box ordering. It does not require AB3DMOT imports or dataset images.

## Common schema pitfalls

- Raw KITTI object-label rows are space-separated and start with a string class such as `Car`; they must be converted before AB3DMOT tracking.
- AB3DMOT rows are comma-separated and start with an integer frame id and integer type id.
- Use `--allow-empty` only when a sequence file is legitimately empty; otherwise treat empties as a conversion problem.
- A valid score can be larger than 1.0 for some detector outputs; do not clamp scores unless a downstream evaluation protocol requires it.
- Some converted nuScenes boxes may have placeholder 2D boxes if they are outside the front camera; treat box-order warnings as data-quality signals, not automatic proof that every 3D field is invalid.
- Detection row order matters: swapping score and height or alpha and rotation can still parse as floats but will break tracking semantics.
