# Shared CLI and Config Keys

## Command Shape

Ultralytics CLI commands use this shape:

```bash
yolo [TASK] MODE arg=value arg=value
```

`TASK` is optional for many model files but should be explicit when the model or request is ambiguous. `MODE` is required. Do not use normal `--flag value` syntax for ordinary YOLO configuration keys.

## Verified Tasks and Modes

- Tasks: `classify`, `detect`, `obb`, `pose`, `segment`, `semantic`.
- Modes: `benchmark`, `export`, `predict`, `track`, `train`, `val`.

## Common Config Groups

- Model/data: `model`, `data`, `task`, `mode`, `pretrained`, `resume`.
- Runtime: `device`, `workers`, `batch`, `imgsz`, `half`, `amp`, `compile`, `cache`.
- Training: `epochs`, `patience`, `optimizer`, `lr0`, `lrf`, `momentum`, `weight_decay`, `warmup_epochs`, `close_mosaic`, `fraction`, `seed`, `deterministic`.
- Prediction/tracking: `source`, `conf`, `iou`, `max_det`, `vid_stride`, `stream_buffer`, `save`, `save_txt`, `save_conf`, `save_crop`, `show`, `tracker`.
- Export/benchmark: `format`, `keras`, `optimize`, `int8`, `dynamic`, `simplify`, `opset`, `workspace`, `nms`.
- Output: `project`, `name`, `exist_ok`, `plots`, `verbose`, `save_json`, `save_hybrid`.

## Validation Rules

- Validate spelling before execution; unknown keys often indicate typos or stale docs.
- Translate Python booleans to `True`/`False` strings in CLI examples.
- Quote values containing spaces, shell metacharacters, lists, dicts, or JSON-like structures.
- Prefer `device=cpu`, `workers=0`, `batch=1`, and small `imgsz` for safe smoke commands.
- Surface side effects for keys such as `save=True`, `save_txt=True`, `save_crop=True`, `cache=True`, `download`, `project`, `name`, and export `format`.

## Shared Troubleshooting

- If `yolo` is missing, check that the `ultralytics` package is installed in the active Python environment and that console scripts are on `PATH`.
- If imports fail with `cv2`, `torch`, or optional backend modules missing, install the base package or the narrow optional extra for the selected workflow.
- If a CLI command treats an argument as invalid, check for `--flag value` misuse, missing `MODE`, invalid `TASK`, typos, or deprecated keys.
- If a command downloads unexpectedly, replace built-in names with explicit local paths or prepare the needed weights/datasets first.
