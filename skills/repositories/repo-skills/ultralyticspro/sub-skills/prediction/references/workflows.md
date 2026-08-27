# Prediction Workflows

## Purpose

Read this when you want to reproduce or adapt one of the repository's single-
image prediction examples.

## Dry-run pattern

Start with a dry run so you can see the resolved model, source image, and
kwargs before launching inference:

```bash
python sub-skills/prediction/scripts/run_predict.py --preset predict-yolo11
```

This prints the effective plan and exits without running inference.

## Real run pattern

When the model weight and source are ready and the user wants to actually run
prediction, add `--execute`:

```bash
python sub-skills/prediction/scripts/run_predict.py --preset predict-yolo11 --execute
```

Useful overrides:

- `--model` for a custom weight file or URL
- `--source` for a different image, video, or stream source
- `--imgsz`, `--conf`, `--save`, `--device`
- `--project` and `--name` for run organization

## Recommended source-script translations

- `predict_v8.py` → `--preset predict-v8`
- `predict_yolo11.py` → `--preset predict-yolo11`
- `predict_yolov10.py` → `--preset predict-yolov10`

## Default source image

The helper uses the packaged `ultralytics/assets/zidane.jpg` sample by default.
That means the wrapper stays self-contained and does not depend on the original
repository checkout.
