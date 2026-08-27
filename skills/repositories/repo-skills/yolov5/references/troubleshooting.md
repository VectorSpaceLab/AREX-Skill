# Cross-Cutting Troubleshooting

## Import and environment failures

### `ModuleNotFoundError: No module named 'models'` or `utils`

Likely causes:

- The command is not being run from a YOLOv5 checkout.
- The repository root is not on `PYTHONPATH`.
- Dependencies were installed, but the clone-run modules are not importable.

Recovery:

1. Run commands from the checkout root when using repo scripts.
2. Verify dependencies with `python scripts/check_yolov5_env.py` from this skill tree when available in the project.
3. Do not assume `pip install -e .` works; this checkout is primarily clone-run.

### Editable install fails with multiple top-level packages

Modern setuptools can reject the flat-layout repository because it sees directories such as `models`, `data`, `segment`, and `classify`. This does not invalidate normal YOLOv5 usage. Install dependencies and run repository scripts from a checkout instead.

### Missing `ultralytics` dependency

Current YOLOv5 code imports utilities from the `ultralytics` package. Install the base requirements or at least the documented runtime dependencies before inspecting Hub/model-loading paths.

## Download and cache failures

Symptoms:

- Checkpoint name fails to resolve.
- PyTorch Hub reports stale cache or validation errors.
- Dataset YAML triggers a download that fails or writes somewhere unexpected.

Recovery:

- Prefer explicit local paths for checkpoints and datasets in offline or reproducible work.
- Confirm network permission and disk budget before using named weights or dataset scripts.
- If PyTorch Hub cache is stale, use the Hub reload option only after the user accepts cache/network mutation.
- Keep task-specific weights aligned: detection `*.pt`, segmentation `*-seg.pt`, classification `*-cls.pt` or torchvision model names.

## Device and precision issues

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `torch.cuda.is_available()` is false | CPU-only PyTorch, no GPU passthrough, incompatible driver/wheel | Install matching PyTorch backend or use `--device cpu` for CPU-compatible checks. |
| Half precision fails on CPU | `--half` requires CUDA in many paths | Remove `--half` or use a CUDA device. |
| CUDA out of memory | Batch/img size too large, model too large, cache retained | Reduce `--batch-size`, `--imgsz`, model size, workers, or use gradient accumulation/training flags where supported. |
| TensorRT engine fails to deserialize | Engine built with different TensorRT/runtime/GPU environment | Rebuild or run with the same TensorRT version and compatible target GPU/runtime. |

## Data/config issues

Common causes:

- YAML `path`, `train`, or `val` resolves to the wrong directory.
- `names` length does not match intended classes.
- Segmentation task receives detection-only labels.
- Classification data is not ImageFolder-style.
- Full COCO/ImageNet commands are run when a tiny fixture was intended.

Recovery:

1. Read `datasets-and-weights.md` and the task sub-skill's data-format reference.
2. Resolve all paths before launching training or validation.
3. Start with tiny datasets such as COCO128 or a local two-class ImageFolder fixture.
4. Use planner scripts to inspect the exact command and warnings before running.

## Output and side-effect surprises

YOLOv5 scripts can write under `runs/`, save media, labels, crops, CSVs, exported models, or benchmark files. Avoid accidental output mixing by setting:

- `--project <dir>`
- `--name <run-name>`
- `--exist-ok` only when intentional
- `--nosave` or `--save-txt`/`--save-crop` choices explicitly for inference

For services, avoid starting long-lived servers until port, model, and auth behavior are confirmed with the serving smoke helper.

## Optional dependency failures

Use `sub-skills/export/scripts/check_export_prereqs.py` before export-format work. It can show which optional modules are importable without exporting a model.

Common optional failures:

- ONNX missing for default export path.
- OpenVINO missing when exporting XML/OpenVINO directories.
- TensorFlow/Keras version conflicts for SavedModel/TFLite/TF.js.
- TensorRT Python package/runtime missing or mismatched.
- CoreML package unavailable or unsupported on the platform.
- Flask missing for the REST API example.
- Comet/ClearML/W&B missing or lacking credentials for logging.

Install only the missing dependency family required by the selected workflow.

## Security and network surfaces

- Remote image URLs and stream sources can access network resources. Validate intent and avoid private/internal URLs.
- Flask serving should bind to localhost unless exposure is intentional.
- Use API keys for service testing when required; avoid logging secrets.
- Export paths and model paths should be passed as argument lists in automation, not through shell-concatenated strings.
