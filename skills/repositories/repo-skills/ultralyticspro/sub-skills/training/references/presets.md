# Training Presets

## Purpose

Read this when you need to map one of the repository's training scripts to the
bundled `run_train.py` helper.

## Preset table

| Preset | Source script equivalent | Model config or class | Dataset default | Key defaults | Notes |
| --- | --- | --- | --- | --- | --- |
| `train-v8` | `train_v8.py` | `cfg/models/v8/yolov8.yaml` | `coco128.yaml` | `epochs=2`, `imgsz=640`, `workers=2`, `batch=2` | Standard YOLOv8 detect example. |
| `train-v8-linux` | `train_v8_linux.py` | `cfg/models/v8/yolov8.yaml` | `coco128.yaml` | `epochs=2`, `imgsz=640`, `workers=0`, `batch=1`, `device=cpu` | CPU-leaning variant that mirrors the Linux example. |
| `train-yolo11` | `train_yolo11.py` | `cfg/models/11/yolo11.yaml` | `coco128.yaml` | `epochs=2`, `imgsz=640`, `workers=2`, `batch=2` | Main YOLO11 detect example. |
| `train-yolov10` | `train_yolov10.py` | `cfg/models/v10/yolov10s.yaml` | `coco128.yaml` | `epochs=10`, `imgsz=640`, `workers=2`, `batch=2`, `device=0` | Source script pins GPU 0. |
| `train-yolo12` | `train_yolo12.py` | `cfg_yolov12/yolo12.yaml` | `coco128.yaml` | `epochs=2`, `imgsz=640`, `workers=2`, `batch=2` | Requires a custom local YAML file in the verified public install. |
| `train-cls` | `train_cls.py` | `cfg/models/11/yolo11-cls.yaml` | `mnist160` | `epochs=100`, `imgsz=640`, `workers=2`, `batch=8` | Classification example. |
| `train-obb` | `train_obb.py` | `cfg/models/11/yolo11-obb.yaml` | `dota8.yaml` | `epochs=2`, `imgsz=640`, `workers=2`, `batch=2` | Oriented bounding-box example. |
| `train-pose` | `train_pose.py` | `cfg/models/11/yolo11-pose.yaml` | `coco8-pose.yaml` | `epochs=300`, `imgsz=640`, `workers=2`, `batch=4` | Pose estimation example. |
| `train-seg` | `train_seg01.py` | `cfg/models/11/yolo11-seg.yaml` | `coco8-seg.yaml` | `epochs=300`, `imgsz=640`, `workers=2`, `batch=2` | Instance-segmentation example. |
| `train-rtdetr` | `train_rtdetr.py` | `cfg/models/rt-detr/rtdetr-l.yaml` with `RTDETR` | `coco128.yaml` | `epochs=100`, `imgsz=320`, `workers=1`, `batch=1` | Uses the `RTDETR` class instead of `YOLO`. |

## Notes

- The helper resolves package-relative model configs against the installed
  `ultralytics` package before execution.
- The helper stays in dry-run mode unless `--execute` is provided.
- The `train-yolo12` preset is intentionally treated as a custom local-file
  case because the verified public install did not ship the referenced YAML.
