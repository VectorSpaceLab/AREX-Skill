# RF-DETR Troubleshooting

## When to read

Read this for cross-cutting RF-DETR failures before opening a workflow-specific troubleshooting file. Then route to the nearest sub-skill when the failure is clearly about inference, training/CLI, export/deployment, or repository development.

## Install and import failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ModuleNotFoundError: No module named 'rfdetr'` | Package not installed in the active Python | Install with `pip install rfdetr` in the environment that will run the code. Verify with `python -c "import rfdetr; print(rfdetr.__all__)"`. |
| `ImportError` for `pytorch_lightning`, `torchmetrics`, `pycocotools`, or `roboflow` during training | Missing training extra | Install `pip install "rfdetr[train]"`; add `cli`, `augment`, or `loggers` only if those surfaces are used. |
| CLI command `rfdetr` is missing or help fails | Missing `cli` extra or wrong Python environment | Install `pip install "rfdetr[train,cli]"` and run `python -m rfdetr --help` to avoid PATH ambiguity. |
| Import error for `rfdetr.util` or `rfdetr.deploy` | Removed legacy modules | Use `rfdetr.utilities` and `rfdetr.export` respectively. |
| Plus model class import raises an install hint | `rfdetr_plus` package is absent or license/account prerequisite is unmet | Install `pip install "rfdetr[plus]"` only when the task needs Plus models and the user accepts Plus package/license requirements. |

Use the root script for a read-only diagnosis:

```bash
python scripts/check_rfdetr_environment.py --extras train cli onnx augment --check-cuda
```

## Pretrained weight and checkpoint failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Model construction hangs or fails while downloading weights | Network/proxy/cache issue for pretrained weights | Use a local checkpoint via `pretrain_weights=...`, retry with network access, or pre-populate the package cache. Do not treat this as an import failure. |
| `FileNotFoundError` when loading `pretrain_weights` or checkpoint | Wrong path or moved artifact | Check the path before constructing the model; use absolute or correct relative paths in user code. |
| Safe checkpoint loading rejects a file | Checkpoint requires full pickle deserialization | Keep `trust_checkpoint=False` for untrusted sources. Set `trust_checkpoint=True` only for fully trusted checkpoints because full pickle can execute code. |
| Fine-tuned labels look wrong | Code indexes `COCO_CLASSES` for a custom checkpoint | Use `detections.data["class_name"]` or `key_points.data["class_name"]`; reserve `COCO_CLASSES` for COCO-pretrained detections. |

## Shape and device failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `shape must have both dimensions divisible by ...` | `predict(shape=...)` or `export(shape=...)` does not match `patch_size * num_windows` | Choose dimensions divisible by the model block size. Detection `small/medium/large/nano` commonly use `32`; many segmentation/keypoint variants use `24`; segmentation nano uses `12`. |
| CUDA requested but not used | Host, torch build, or Lightning device config mismatch | Probe torch CUDA with `python -c "import torch; print(torch.cuda.is_available(), torch.version.cuda)"`. For training under `torchrun`, pass `devices="auto"` or an explicit count. |
| Out-of-memory during inference/training/export | Model size, resolution, batch size, precision, or retained source images exceed memory | Lower resolution/batch size, switch to a smaller model, use `include_source_image=False`, or use `model.inference(..., dtype="float16", inplace=True)` only for inference-only sessions. |

## Data and config failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Training says dataset format is not detected | Missing COCO `train/_annotations.coco.json` or YOLO `data.yaml` plus split image/label directories | Run `sub-skills/training-and-cli/scripts/validate_dataset_layout.py DATASET --task auto`, then fix the missing split or metadata. |
| Keypoint training fails schema checks | COCO categories lack keypoint schema or YOLO pose `data.yaml` lacks `kpt_shape` | Use the training sub-skill's dataset reference and validator with `--task keypoint --infer-keypoint-schema`. |
| CLI YAML parses but run fails later | Config class paths, nested overrides, or linked model/data config arguments are wrong | Inspect with `sub-skills/training-and-cli/scripts/inspect_training_config.py --config CONFIG --strict`, then use bundled config examples as templates. |

## Optional export backend failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ImportError` for `onnx`, `onnxruntime`, or `onnxsim` | Missing ONNX extra | Install `pip install "rfdetr[onnx]"`. |
| TensorRT export works on one machine but not another | `.trt` engines are non-portable and tied to build GPU/TensorRT version | Build TensorRT on the deployment GPU/runtime or export ONNX for portable transfer. |
| ExecuTorch/CoreML rejects `dynamic_batch=True` | Fixed-batch export requirement | Export one fixed-batch artifact per target batch size. |
| ExecuTorch QNN complains about backend or SoC | QNN requires target SoC and vendor build chain | Provide `backend="qnn"`, `soc="SM8650"`-style target, and validate the QNN toolchain separately. |

Use `sub-skills/export-and-deployment/scripts/inspect_export_options.py` to catch static option errors before model tracing.

## Where to go next

- Prediction/model errors: [../sub-skills/inference-and-models/references/troubleshooting.md](../sub-skills/inference-and-models/references/troubleshooting.md)
- Training/CLI/data errors: [../sub-skills/training-and-cli/references/troubleshooting.md](../sub-skills/training-and-cli/references/troubleshooting.md)
- Export/deployment errors: [../sub-skills/export-and-deployment/references/troubleshooting.md](../sub-skills/export-and-deployment/references/troubleshooting.md)
- Repository development/check failures: [../sub-skills/repository-development/references/troubleshooting.md](../sub-skills/repository-development/references/troubleshooting.md)
