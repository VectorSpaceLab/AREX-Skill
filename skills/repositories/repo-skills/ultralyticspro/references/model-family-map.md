# Model Family Map

## Purpose

Read this when you are choosing which preset or source script matches a user
request.

## Source scripts and bundled preset targets

| Source repo script | User-facing workflow | Bundled preset target | Notes |
| --- | --- | --- | --- |
| `train_v8.py` | YOLOv8 detection training | `sub-skills/training/scripts/run_train.py --preset train-v8` | Common detect preset with `coco128.yaml`. |
| `train_v8_linux.py` | YOLOv8 detection training on CPU | `sub-skills/training/scripts/run_train.py --preset train-v8-linux` | Same model path as `train_v8.py`, but the source example pins `device=cpu` and `workers=0`. |
| `train_yolo11.py` | YOLO11 detection training | `sub-skills/training/scripts/run_train.py --preset train-yolo11` | Matches the main YOLO11 detect example. |
| `train_yolov10.py` | YOLOv10 detection training | `sub-skills/training/scripts/run_train.py --preset train-yolov10` | Source example pins `device=0`. |
| `train_yolo12.py` | YOLOv12 detection training | `sub-skills/training/scripts/run_train.py --preset train-yolo12` | Uses a custom local config file path that is not bundled in the verified `ultralytics` install. |
| `train_cls.py` | Classification training | `sub-skills/training/scripts/run_train.py --preset train-cls` | Uses `mnist160`. |
| `train_obb.py` | Oriented bounding-box training | `sub-skills/training/scripts/run_train.py --preset train-obb` | Uses `dota8.yaml`. |
| `train_pose.py` | Pose training | `sub-skills/training/scripts/run_train.py --preset train-pose` | Uses `coco8-pose.yaml`. |
| `train_seg01.py` | Segmentation training | `sub-skills/training/scripts/run_train.py --preset train-seg` | Uses `coco8-seg.yaml`. |
| `train_rtdetr.py` | RT-DETR training | `sub-skills/training/scripts/run_train.py --preset train-rtdetr` | Uses the `RTDETR` class instead of `YOLO`. |
| `predict_v8.py` | YOLOv8 single-image prediction | `sub-skills/prediction/scripts/run_predict.py --preset predict-v8` | Uses the packaged `zidane.jpg` sample. |
| `predict_yolo11.py` | YOLO11 single-image prediction | `sub-skills/prediction/scripts/run_predict.py --preset predict-yolo11` | Uses the packaged `zidane.jpg` sample. |
| `predict_yolov10.py` | YOLOv10 single-image prediction | `sub-skills/prediction/scripts/run_predict.py --preset predict-yolov10` | Uses the packaged `zidane.jpg` sample. |

## How to read the map

- Choose the training sub-skill when the task mentions any of the `train_*.py`
  scripts, a model family plus dataset YAML, or a device-specific training run.
- Choose the prediction sub-skill when the task mentions any of the
  `predict_*.py` scripts, a single image, or a YOLO inference preset.
- Use `scripts/check_ultralytics_env.py --show-presets` when you want a quick
  machine-readable reminder of the preset names without opening the wrappers.
