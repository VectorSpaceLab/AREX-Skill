# Training and Validation API Reference

This reference summarizes the public Ultralytics package facts relevant to training and validation. Verified package facts: distribution `ultralytics`, version `8.4.72`, console scripts `yolo` and `ultralytics`, tasks `classify`, `detect`, `obb`, `pose`, `segment`, `semantic`, and modes `benchmark`, `export`, `predict`, `track`, `train`, `val`.

## Public Entrypoints

```python
from ultralytics import YOLO

model = YOLO("yolo26n.pt", task=None, verbose=False)
metrics = model.train(**kwargs)
metrics = model.val(**kwargs)
model.tune(iterations=10, use_ray=False, **kwargs)
```

Relevant signatures:

- `YOLO(model: str | Path = "yolo26n.pt", task: str | None = None, verbose: bool = False)`.
- `Model.train(self, trainer=None, **kwargs)`.
- `Model.val(self, validator=None, **kwargs)`.
- `Model.tune(self, use_ray=False, iterations=10, *args, **kwargs)`.

## CLI Shape

```bash
yolo TASK MODE arg=value arg=value
ultralytics TASK MODE arg=value arg=value
```

Examples:

```bash
yolo train data=coco8.yaml model=yolo26n.pt epochs=10 lr0=0.01
yolo detect train data=coco8.yaml model=yolo26n.pt epochs=1 imgsz=32 device=cpu
yolo val model=yolo26n.pt data=coco8.yaml batch=1 imgsz=640
yolo detect val model=runs/detect/train/weights/best.pt data=custom.yaml imgsz=640
```

## Common Train Arguments

| Argument | Use |
| --- | --- |
| `model` | Checkpoint name/path or model YAML. Named checkpoints may download. |
| `data` | Dataset YAML/path/name. Built-in names may download. |
| `epochs` | Number of training epochs; tiny smoke plans use `1`. |
| `time` | Optional hour-based time limit. |
| `patience` | Early-stopping patience in epochs. |
| `batch` | Batch size; `-1` auto-estimates on single GPU. |
| `imgsz` | Image size; tiny plans use `32`, normal detection often uses `640`. |
| `device` | `cpu`, `mps`, CUDA index such as `0`, multi-GPU such as `0,1`, or idle selector `-1`. |
| `workers` | DataLoader workers; use `0` for safe CPU/MPS plans. |
| `project`, `name`, `exist_ok` | Control output run directory and overwrite/increment behavior. |
| `pretrained` | `True`, `False`, or checkpoint path for transfer learning. |
| `optimizer` | `auto`, `SGD`, `MuSGD`, `Adam`, `AdamW`, `NAdam`, `RAdam`, or `RMSProp`. |
| `resume` | Continue an incomplete checkpoint with saved optimizer/epoch state. |
| `amp` | Automatic mixed precision; default is enabled where supported. |
| `fraction` | Train on a fraction of the dataset for quick experiments. |
| `cache` | `False`, `True`/RAM, or `disk`; may increase memory/disk use. |
| `close_mosaic` | Disable mosaic augmentation during final epochs. |
| `multi_scale` | Vary image size per batch when training. |
| `compile` | Try PyTorch compile; can improve speed but may introduce backend issues. |
| `val` | Whether to run validation during training. |
| `plots` | Save plots; disable in smoke tests with `plots=False`. |

## Common Validation Arguments

| Argument | Use |
| --- | --- |
| `model` | Checkpoint or exported model to validate. |
| `data` | Dataset config; explicit is more reproducible than relying on remembered settings. |
| `imgsz` | Validation image size. |
| `batch` | Validation batch size. |
| `device` | CPU/GPU/MPS selection. |
| `split` | Dataset split, commonly `val` or `test`. |
| `conf` | Confidence threshold; default is low for validation. |
| `iou` | NMS IoU threshold. |
| `max_det` | Maximum detections per image. |
| `half` | FP16 validation on compatible devices/backends. |
| `dnn` | Use OpenCV DNN for ONNX where relevant. |
| `plots` | Save validation plots. |
| `save_json` | Save prediction JSON for supported dataset evaluation flows. |

## Return Values and State

- `model.train(...)` returns task-specific metrics when available. After training, the object reloads the best checkpoint if it exists, otherwise `last.pt`.
- `model.val(...)` returns a task-specific metrics object and stores it on `model.metrics`.
- Validation metrics support export helpers such as `to_df()`, `to_csv()`, and `to_json()`.
- Detection metrics expose box metrics such as `metrics.box.map`, `metrics.box.map50`, `metrics.box.map75`, `metrics.box.maps`, and per-image metrics in `metrics.box.image_metrics`.
- The confusion matrix supports export helpers, for example `metrics.confusion_matrix.to_df()`.
- Distributed training can write expected outputs while returning `None` or no direct metrics to the caller.

## Run Outputs

Training normally creates a run directory such as `runs/detect/train` unless `project` or `name` changes it. Important files include:

- `args.yaml`: resolved run arguments.
- `weights/last.pt`: latest checkpoint.
- `weights/best.pt`: best checkpoint when validation identifies one.
- `results.csv`: training and validation metrics over epochs.
- Plots and sample images when `plots=True`.

Validation may create a validation run directory and can save plots, labels, or `predictions.json` depending on arguments.

## Tuning API

```python
from ultralytics import YOLO

YOLO("yolo26n.pt").tune(data="coco8.yaml", epochs=1, iterations=2, imgsz=32, device="cpu", plots=False)
```

- Built-in tuning uses an internal genetic search and writes a tune directory with `tune_results.ndjson`, plots, best hyperparameters, and best weights where possible.
- `iterations` is the number of sequential trials for the built-in tuner.
- `use_ray=True` switches to Ray Tune and requires optional dependencies.
- Tuning can accept a list of datasets; the top-level fitness is the mean of per-dataset fitness values.

## Advanced Trainer/Validator Hooks

Use custom trainers and validators only when the user explicitly needs source-level customization:

```python
from ultralytics import YOLO
from ultralytics.models.yolo import detect

model = YOLO("yolo26n.pt")
model.train(data="custom.yaml", trainer=detect.DetectionTrainer)
metrics = model.val(data="custom.yaml", validator=detect.DetectionValidator)
```

Callbacks can be registered with `model.add_callback(...)`, trainer `add_callback(...)`, or validator `add_callback(...)`. Keep standard user workflows on public `YOLO` methods unless custom callbacks, dataloaders, losses, or validators are required.
