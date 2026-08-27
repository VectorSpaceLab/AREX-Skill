# Training and Validation Workflows

This reference covers concrete Ultralytics train, validation, resume, tuning, device, and metrics workflows for future agents. It is self-contained and does not require opening the source repository.

## CLI Basics

Ultralytics console scripts are `yolo` and `ultralytics`. The normal shape is:

```bash
yolo TASK MODE arg=value arg=value
```

- `TASK` is optional when it can be inferred, and may be `detect`, `segment`, `pose`, `obb`, `classify`, or `semantic`.
- `MODE` is required for these workflows: `train` or `val`.
- CLI overrides must be `arg=value`, not `--arg value`. Boolean and numeric values are passed as values, for example `plots=False`, `epochs=1`, `device=cpu`.

## Safe CPU Tiny Plans

Use these when the user asks for a smoke plan or when hardware is unknown:

```bash
yolo detect train model=yolo26n.pt data=coco8.yaml epochs=1 imgsz=32 device=cpu batch=1 workers=0 plots=False save=True
yolo detect val model=yolo26n.pt data=coco8.yaml imgsz=32 device=cpu batch=1 workers=0 plots=False
```

Equivalent Python:

```python
from ultralytics import YOLO

model = YOLO("yolo26n.pt")
train_metrics = model.train(
    data="coco8.yaml",
    epochs=1,
    imgsz=32,
    device="cpu",
    batch=1,
    workers=0,
    plots=False,
)
val_metrics = model.val(data="coco8.yaml", imgsz=32, device="cpu", batch=1, workers=0, plots=False)
```

`coco8.yaml` is a tiny built-in dataset name, but it may still trigger a dataset download. If downloads are not acceptable, ask for a local dataset YAML and route dataset validation to `../../data-and-configuration/SKILL.md`.

## Training Workflow

1. Confirm task and model. Use `model-families-and-tasks` if the user is unsure whether they need detection, segmentation, pose, OBB, classification, or semantic segmentation.
2. Confirm data source. A `data` value is required for reliable train and validation; built-in names may auto-download.
3. Pick device and resource limits:
   - `device=cpu` for deterministic safe plans and no GPU dependency.
   - `device=0` or `device=0,1` for explicit CUDA devices.
   - `device=-1` or `device=-1,-1` for idle-GPU selection.
   - `device=mps` for Apple Silicon when PyTorch MPS is available.
4. Start with conservative run settings for smoke tests: `epochs=1`, `imgsz=32`, `batch=1`, `workers=0`, `plots=False`.
5. For real training, increase `imgsz`, `epochs`, `batch`, and `workers` deliberately; consider `patience`, `fraction`, `cache`, `amp`, `optimizer`, `lr0`, and `close_mosaic`.
6. Record side effects: run directories, `weights/last.pt`, `weights/best.pt`, `args.yaml`, metrics CSV, plots if enabled, and possible weight/dataset downloads.

Common real-training command skeleton:

```bash
yolo detect train model=yolo26n.pt data=custom.yaml epochs=100 imgsz=640 device=0 batch=16 patience=50 optimizer=auto
```

## Validation Workflow

Validation can use settings remembered in a trained checkpoint, but explicit `data` and `imgsz` make runs reproducible:

```bash
yolo detect val model=runs/detect/train/weights/best.pt data=custom.yaml imgsz=640 batch=16 device=0 conf=0.25 iou=0.7
```

Python metric access for detection:

```python
from ultralytics import YOLO

metrics = YOLO("runs/detect/train/weights/best.pt").val(data="custom.yaml", imgsz=640)
print(metrics.box.map)      # mAP50-95
print(metrics.box.map50)    # mAP at IoU 0.50
print(metrics.box.map75)    # mAP at IoU 0.75
print(metrics.box.maps)     # per-class mAP50-95
print(metrics.confusion_matrix.to_df())
print(metrics.to_json())
```

For segmentation, pose, and OBB, metric namespaces follow the task, for example `metrics.seg`, `metrics.pose`, or `metrics.box`/OBB-specific fields. Classification focuses on top-1/top-5 style metrics and does not expose per-image box metrics.

## Resume Training

Use resume only for an interrupted training checkpoint that contains epoch and optimizer state. Normal fine-tuning from pretrained weights is not resume.

CLI:

```bash
yolo train resume model=runs/detect/train/weights/last.pt
```

Python:

```python
from ultralytics import YOLO

model = YOLO("runs/detect/train/weights/last.pt")
model.train(resume=True)
```

Important behaviors:

- `resume=True` on a loaded `last.pt` continues from the saved epoch and optimizer state.
- A checkpoint missing training epoch or optimizer state is not resumable; use it as `model=...` for a new fine-tune instead.
- Checkpoints are normally saved at epoch end, so a run must complete at least one epoch to have a useful `last.pt`.
- If the run directory is missing but the checkpoint file exists, resume can still work from the checkpoint path; if the checkpoint itself is missing, ask the user to locate `last.pt` or start a new run.

## Hyperparameter Tuning

The built-in tuner runs repeated training trials, mutates hyperparameters, and logs fitness/results. It is expensive by design.

Python example with a tiny CPU budget:

```python
from ultralytics import YOLO

YOLO("yolo26n.pt").tune(data="coco8.yaml", epochs=1, iterations=2, imgsz=32, device="cpu", plots=False)
```

Production-style skeleton:

```python
from ultralytics import YOLO

search_space = {"lr0": (1e-5, 1e-2), "degrees": (0.0, 45.0)}
YOLO("yolo26n.pt").tune(
    data="custom.yaml",
    epochs=50,
    iterations=40,
    optimizer="AdamW",
    space=search_space,
    plots=False,
    save=False,
)
```

Tuning notes:

- `iterations` is the number of trials for the built-in tuner, not a population size.
- Each trial trains a model, so `iterations=40, epochs=50` schedules up to 40 independent 50-epoch trainings.
- `resume=True` resumes tuning from an existing tune directory; repeat the prior `data`, `epochs`, `iterations`, and `space` arguments.
- Built-in tuning writes `tune_results.ndjson`, plots, best hyperparameters, and best weights where available.
- `use_ray=True` requires optional Ray Tune dependencies and changes the tuning backend.

## Device and Resource Choices

- CPU: safest for command planning and tiny verification; slower but avoids CUDA/MPS problems.
- CUDA single GPU: `device=0`; pair with explicit `batch` and consider `amp=True` default.
- CUDA multi-GPU: `device=0,1` in CLI or `device=[0, 1]` in Python. Ultralytics uses distributed training internally for standard runs.
- Idle GPUs: `device=-1` or `device=-1,-1` lets Ultralytics choose least-busy GPU(s).
- Apple Silicon: `device=mps` when PyTorch MPS support is installed and stable.
- CPU/MPS validation and training force `workers=0` internally in core trainer/validator behavior, but setting it explicitly is clearer for safe plans.
- `batch=-1` can auto-estimate batch size for single-GPU training. Avoid it in tiny CPU plans and multi-GPU plans.

## Metrics Interpretation

Detection validation commonly reports:

- `metrics/precision(B)`: precision for boxes.
- `metrics/recall(B)`: recall for boxes.
- `metrics/mAP50(B)`: AP at IoU 0.50.
- `metrics/mAP50-95(B)`: AP averaged over IoU 0.50 through 0.95.
- `fitness`: task-specific summary used by training/tuning to compare checkpoints.
- Speed fields: preprocess, inference, loss, and postprocess milliseconds per image.

During training, the trainer validates at the final epoch and optionally during training, stores the latest validator metrics, and reloads `best.pt` when available or `last.pt` after training. In distributed training, metrics may not be returned directly to the caller even though files are written.

## Trainer and Validator Ownership

- `YOLO(...).train()` creates the task-specific trainer and stores it on `model.trainer`.
- The trainer owns dataloaders, optimizer, scheduler, callbacks, EMA, checkpoints, `save_dir`, `weights/last.pt`, and `weights/best.pt`.
- The trainer creates a task-specific validator for validation during training.
- `YOLO(...).val()` creates the task-specific validator and stores returned metrics on `model.metrics`.
- Custom trainer/validator classes can be passed through the Python API for advanced use; for standard workflows prefer normal `YOLO` methods and CLI arguments.

## Safe Side-Effect Checklist

Before executing training or validation, tell the user if the plan may:

- Download named weights or datasets.
- Create or overwrite a run directory, especially when `project`, `name`, or `exist_ok=True` is used.
- Write checkpoints, plots, labels, predictions JSON, or metrics files.
- Use GPU memory, spawn distributed subprocesses, or compile a model.
- Consume significant time due to large `epochs`, `iterations`, `imgsz`, dataset size, or tuning trials.
