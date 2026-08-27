# DAMO-YOLO troubleshooting

Use this root troubleshooting guide for cross-cutting problems. Sub-skill troubleshooting references go deeper for workflow-specific issues.

## Package and import problems

| Symptom | Likely cause | Recovery |
|---|---|---|
| `ModuleNotFoundError: damo` | The package is not installed in the active environment. | Install the package or use a prepared environment where `damo` imports cleanly. |
| `ImportError` from `torch`, `torchvision`, `opencv_python`, `PIL`, or `onnxruntime` | Required base or optional dependency is missing. | Install the dependency set needed for the chosen workflow, then rerun the bundled smoke or helper script. |
| `CUDA`/`NCCL` errors during training or evaluation | The training/eval path is GPU-only in this repo version. | Use a CUDA-enabled PyTorch build and confirm NCCL availability before launching. |

## Config and dataset problems

| Symptom | Likely cause | Recovery |
|---|---|---|
| `Only support coco format dataset now!` | Dataset names do not contain `coco`. | Rename the dataset entries or the catalog keys so the substring match succeeds. |
| `cfg.dataset.class_names` missing or head class-count mismatch | Config and checkpoint/class list are inconsistent. | Edit the config file so `cfg.dataset.class_names` and `cfg.model.head.num_classes` agree before training/export. |
| Relative TinyNAS structure file not found | Config uses a relative structure path from the wrong working directory. | Pass `--workdir` to the launcher/helper or make the structure path absolute in the config. |
| `Config.merge()` did not update a nested value | Command-line overrides only replace exact top-level keys. | Edit the config file directly for nested model/train/test/dataset changes. |

## Demo and deployment problems

| Symptom | Likely cause | Recovery |
|---|---|---|
| Torch demo falls back to CPU | CUDA was unavailable or not selected. | Confirm the requested device and the installed Torch build; use CPU-only expectations only for Torch demo workflows. |
| ONNX demo says CUDA provider is missing | `onnxruntime` is installed without CUDA support or GPU provider. | Install the appropriate ONNX Runtime build or run the ONNX model on CPU. |
| TensorRT import fails | TensorRT Python bindings or runtime libraries are missing. | Run the deployment backend check, then install the approved TensorRT stack before claiming TensorRT support. |
| Partial INT8 quantization cannot start | `pytorch_quantization` or calibration assets are missing. | Use the deployment backend check and provide the calibration dataset expected by the chosen model type. |

## Helper-first recovery order

1. Run `scripts/check_model_smoke.py` for a fast package/config/model sanity check.
2. If the task is training or evaluation, run `sub-skills/training/scripts/validate_coco_config.py` before a long job.
3. If the task is inference, use `sub-skills/inference/scripts/damo_yolo_safe_demo.py --check-only` to validate engine and media inputs first.
4. If the task is deployment, run `sub-skills/deployment/scripts/check_deploy_env.py` before any export or TensorRT planning.

If the helper scripts and the config still disagree, prefer fixing the config file or the dataset path over forcing command-line overrides.
