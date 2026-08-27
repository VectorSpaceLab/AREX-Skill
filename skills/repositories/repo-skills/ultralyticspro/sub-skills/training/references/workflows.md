# Training Workflows

## Purpose

Read this when you want to turn a source script into a bundled training
command.

## Dry-run pattern

Start with a dry run so you can see the resolved preset, model, dataset, and
kwargs before launching any training job:

```bash
python sub-skills/training/scripts/run_train.py --preset train-yolo11
```

This prints the effective plan and exits without starting training.

## Real run pattern

When the model config and dataset are available and the user wants to actually
train, add `--execute`:

```bash
python sub-skills/training/scripts/run_train.py --preset train-yolo11 --execute
```

Useful overrides:

- `--model` for a custom YAML or weight file
- `--data` for a different dataset YAML or dataset name
- `--epochs`, `--imgsz`, `--workers`, `--batch`, `--device`
- `--project` and `--name` for run organization

## Recommended source-script translations

- `train_v8.py` → `--preset train-v8`
- `train_v8_linux.py` → `--preset train-v8-linux`
- `train_yolo11.py` → `--preset train-yolo11`
- `train_yolov10.py` → `--preset train-yolov10`
- `train_yolo12.py` → `--preset train-yolo12`
- `train_cls.py` → `--preset train-cls`
- `train_obb.py` → `--preset train-obb`
- `train_pose.py` → `--preset train-pose`
- `train_seg01.py` → `--preset train-seg`
- `train_rtdetr.py` → `--preset train-rtdetr`

## When to read the preset map

Use `references/presets.md` when you need the exact model path, dataset, and
default hyperparameters for a source script before you decide whether to
execute the wrapper.
