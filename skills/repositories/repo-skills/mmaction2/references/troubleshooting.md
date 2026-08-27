# Cross-cutting troubleshooting

## When to read

Read this before retrying a failed MMAction2 install, import, config parse, API call, training/test command, optional demo, or export/deployment step. For workflow-specific errors, also read the nearest sub-skill troubleshooting reference.

## Import and version failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `AssertionError: MMCV==... is used but incompatible` | Installed `mmcv` is outside MMAction2's expected `>=2.0.0rc4,<2.2.0` range. | Reinstall a compatible MMCV build matching the active PyTorch CPU/CUDA variant. Use MIM when possible. |
| `AssertionError: MMEngine==... is used but incompatible` | Installed `mmengine` is below `0.7.1` or at/above `1.0.0`. | Install `mmengine>=0.7.1,<1.0.0` in the environment used to run MMAction2. |
| `ModuleNotFoundError: mmaction` | MMAction2 is not installed in the current Python, or a different environment is active. | Run the root environment helper, check `python -m pip show mmaction2`, and install the package in the current environment. |
| Import succeeds from one shell but fails elsewhere | Multiple Python environments or user-site packages. | Run `python -c "import sys; print(sys.executable)"` in both shells and reinstall only in the intended environment. |

## Optional dependency failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `Failed to import inference_detector` or `init_detector` | Detector-assisted demo or API path needs `mmdet`. | Install a compatible MMDetection stack only if the task actually needs spatio-temporal detection or skeleton pose extraction. |
| `Failed to import inference_topdown` or `init_model` | Pose-assisted path needs `mmpose`. | Install MMPose and provide local pose config/checkpoint, or narrow the task to recognizer-only inference. |
| Missing CLIP/tokenizer/multimodal imports | Multimodal/retrieval config imports optional packages. | Use `models-and-extension` to identify the config family and install only the selected optional extras. |
| Missing ONNX/TorchServe/model-archiver imports | Export/deployment helper needs deployment extras. | Use `models-and-extension` export/deployment reference; verify artifact paths and optional tools before mutating outputs. |

## Backend and hardware issues

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| API defaults to `cuda:0` and fails on CPU-only host | Several public APIs default to CUDA-like devices. | Pass `device="cpu"` explicitly or preview CPU commands with `CUDA_VISIBLE_DEVICES=-1`. |
| `torch.cuda.is_available()` is false despite a visible GPU | CPU-only torch, driver/container passthrough mismatch, or incompatible wheel. | Fix the PyTorch CUDA installation first; do not debug MMAction2 model code until a tiny CUDA tensor allocation works. |
| CUDA out-of-memory during inference/testing | Multi-crop/test-time augmentation, large clip count, high resolution, or too large batch. | Reduce batch size, use center crop/single clip for smoke checks, lower resolution, or run CPU/build-only checks first. |
| Distributed launch hangs or ranks disagree | Port collision, wrong `MASTER_ADDR`, `NNODES`, `NODE_RANK`, or network visibility. | Use the command builder to preview env vars and assign unique ports per job. |

## Data/config and checkpoint issues

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `FileNotFoundError` for videos, frames, annotations, or proposals | Incorrect `data_prefix`, relative path, or annotation file row. | Use `data-and-configs` and its config inspector to verify dataset type, `ann_file`, `data_prefix`, and pipeline decoder. |
| `KeyError` or registry class not found in config | Missing custom import, wrong default scope, or config family mismatch. | Use `models-and-extension` to check `custom_imports`, registry decorators, and `register_all_modules`. |
| Classifier head shape mismatch | `num_classes`, checkpoint head, dataset labels, or model family changed. | Align `model.cls_head.num_classes`, label map, and whether the checkpoint should load the old head strictly. |
| Checkpoint load errors | Config and checkpoint are from different model families or class counts. | Choose a matching config/checkpoint pair; for fine-tuning, load backbone-compatible weights and update the head deliberately. |

## Workflow boundary checks

- If the failure appears before a model is built, start with `data-and-configs` or `models-and-extension`.
- If the failure appears while creating commands, launching jobs, resuming, dumping predictions, or computing metrics, use `training-and-evaluation`.
- If the failure appears while reading a single media input, producing top-k scores, or saving visualization, use `inference-and-demos`.
- If an export or publishing tool would overwrite or create artifacts, require explicit user approval and a target path before running it.

## Stop conditions

Stop and ask for user input when the next step would install or change a shared environment, download large data/checkpoints, run long training/testing, submit a cluster job, delete/rewrite user data, or require credentials/network access that the user has not authorized.
