# Training and Validation Troubleshooting

Use this reference to diagnose failures in Ultralytics train, val, resume, tuning, metrics, and device workflows.

## Install or Import Failures

Symptoms:

- `ModuleNotFoundError: No module named 'ultralytics'`.
- Import errors for PyTorch, TorchVision, OpenCV, PIL, Polars, or optional integrations.
- `yolo: command not found` or `ultralytics: command not found`.

Likely causes and fixes:

- The package is not installed in the active Python environment. Verify with `python -c "import ultralytics; print(ultralytics.__version__)"`.
- The CLI script is not on `PATH`. Use `python -m ultralytics.cfg.__init__ train ...` as a fallback, or fix the environment activation.
- Optional tuning backend `use_ray=True` requires Ray Tune dependencies; retry with `use_ray=False` or install the optional backend.
- MongoDB-based distributed tuning requires `pymongo` and a reachable MongoDB Atlas URI; omit `mongodb_uri` for local NDJSON tuning.

## CLI Syntax Misuse

Symptoms:

- Help text says Ultralytics commands use `yolo TASK MODE ARGS`.
- Arguments are ignored or rejected when written as `--epochs 1`.
- Task/mode appears swapped or missing.

Fix:

```bash
# Correct
yolo detect train model=yolo26n.pt data=coco8.yaml epochs=1 imgsz=32

# Also valid when task can be inferred
yolo train model=yolo26n.pt data=coco8.yaml epochs=1 imgsz=32
```

Rules:

- Use `arg=value` pairs.
- `MODE` must be one of the supported modes such as `train` or `val`.
- `TASK` may be `detect`, `segment`, `pose`, `obb`, `classify`, or `semantic`.
- Use quoted values only when the shell needs them, for example paths with spaces.

## Bad Data or Config Paths

Symptoms:

- Dataset YAML not found.
- Dataset split missing, especially `train`, `val`, or selected `split`.
- Validation says no labels were found or metrics cannot be computed.
- Built-in dataset unexpectedly downloads.

Fixes:

- Ask for the dataset YAML path and route schema/layout checks to `../../data-and-configuration/SKILL.md`.
- For smoke tests that must avoid network, do not use built-in names such as `coco8.yaml`; require a local YAML and local images/labels.
- For validation, pass `data=...` explicitly rather than relying on checkpoint-remembered settings when reproducibility matters.
- For classification datasets, ensure the directory/class layout matches classification expectations; for detection/segment/pose/OBB/semantic, ensure the dataset YAML and label formats match the task.

## Device and Backend Problems

Symptoms:

- CUDA out of memory.
- CUDNN backend errors such as unable to find an engine.
- MPS failures or CPU fallback concerns.
- Multi-GPU failures involving distributed subprocesses.
- PyTorch compile failures.

Fixes:

- Retry with `device=cpu imgsz=32 batch=1 workers=0 plots=False` to separate data/config failures from accelerator failures.
- Reduce `batch`, `imgsz`, and `workers`; disable expensive options like `cache=True`, `compile=True`, and plots.
- On single GPU, Ultralytics may auto-reduce batch for early CUDA OOMs, but do not rely on that for production planning.
- Use `device=0` for a known GPU, `device=0,1` for explicit multi-GPU, or `device=-1`/`-1,-1` for idle GPU selection.
- Avoid `batch=-1` in multi-GPU plans because auto-batch is not supported for multi-GPU training.
- For custom trainers, validators, or complex Python objects, launch distributed training explicitly with `torch.distributed.run`; automatic DDP works best for standard CLI and simple scripts.
- Set `compile=False` if failures appear only with PyTorch compilation.
- Set `amp=False` when mixed precision causes numerical or backend instability.

## Resume Failures

Symptoms:

- `last.pt` path is missing.
- Resume starts a fresh training run instead of continuing.
- Warning says the model is not a resumable training checkpoint because epoch or optimizer state is missing.
- Assertion or mismatch when trying to resume a completed run.

Fixes:

- Use `resume=True` only with an interrupted training checkpoint that contains training epoch and optimizer state.
- Load `last.pt`, not `best.pt`, for a normal interrupted-run resume.
- If only a pretrained or exported model exists, start a new fine-tune with `model=that_file` instead of `resume=True`.
- Ensure at least one epoch completed before expecting a resumable `last.pt`.
- If the run directory is gone but `last.pt` still exists, use the checkpoint path directly; if the checkpoint is gone, the run cannot be resumed.

## Download and Network Risks

Symptoms:

- Named weights or datasets trigger downloads.
- Offline environment fails on `yolo26n.pt`, `coco8.yaml`, or remote NDJSON/dataset URLs.
- Slow tests or training due to network access.

Fixes:

- Use local model and dataset paths when network is prohibited.
- Warn before using built-in names in generated plans.
- Avoid URL data sources in safe CPU tiny plans unless the user explicitly accepts network access.
- If a download failed halfway, remove the partial artifact or provide a known-good local path.

## Expensive or Unwanted Side Effects

Symptoms:

- Training created large `runs/...` directories or checkpoints.
- Validation saved plots, labels, or JSON.
- Tuning created many train directories or took much longer than expected.
- Export/media operations appear in a train/val request.

Fixes:

- For planning only, use `scripts/plan_training_run.py`; it prints commands and does not execute Ultralytics.
- For smoke runs, use `epochs=1 imgsz=32 batch=1 device=cpu workers=0 plots=False`.
- Set `project` and `name` deliberately to keep outputs isolated.
- Avoid `exist_ok=True` unless overwriting/reusing an output directory is intended.
- For tuning, multiply `iterations * epochs` to communicate the real training budget before execution.
- Route export/deployment side effects to `../../export-and-deployment/SKILL.md` and media/prediction side effects to `../../inference-and-results/SKILL.md`.

## Metrics Look Wrong or Empty

Symptoms:

- `metrics` is `None` after training.
- mAP is zero or near zero.
- Validation reports no labels.
- Classification metrics are accessed as `metrics.box.*` and fail.

Fixes:

- In distributed training, direct Python return metrics may be unavailable; inspect saved run outputs instead.
- Ensure the model task matches the data task and labels.
- For untrained YAML models, validation can produce zero mAP; use a trained checkpoint for meaningful validation.
- Use task-appropriate metric namespaces: detection uses `box`, segmentation uses segmentation metrics, pose uses pose metrics, and classification uses classification metrics.
- Validate with explicit `data`, `imgsz`, and `split` to avoid relying on stale remembered checkpoint settings.
