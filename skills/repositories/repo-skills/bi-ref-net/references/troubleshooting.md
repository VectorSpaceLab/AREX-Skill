# Cross-Cutting Troubleshooting

Read this for failures that span multiple BiRefNet workflows. For workflow-specific fixes, use the nearest sub-skill troubleshooting file.

## Install and import

| Symptom | Likely cause | Recovery |
|---|---|---|
| `ModuleNotFoundError: models` or `ModuleNotFoundError: config` | BiRefNet is source-code-first and the checkout is not on `PYTHONPATH` / `--repo-root` is wrong. | Pass `--repo-root` to bundled helpers or run source workflows from the user's BiRefNet checkout root. |
| `ModuleNotFoundError: timm`, `kornia`, `einops`, `skimage`, `prettytable`, or `accelerate` | Base requirements are incomplete. | Install `requirements.txt` in the active environment and rerun `scripts/check_birefnet_environment.py`. |
| `ModuleNotFoundError: transformers` while using `AutoModelForImageSegmentation` | README's Transformers path uses an extra package not declared in `requirements.txt`. | Install `transformers` or use the source `BiRefNet.from_pretrained(...)` path instead. |
| NumPy/OpenCV/scikit-image binary errors | Incompatible compiled wheels or `numpy>=2` despite repo requirement. | Use Python 3.11, keep `numpy<2`, and reinstall OpenCV/scikit-image against that NumPy version. |

## Backend and hardware

| Symptom | Likely cause | Recovery |
|---|---|---|
| CUDA requested but unavailable | CPU-only PyTorch build, hidden GPU, or driver/container passthrough problem. | Run `python -c "import torch; print(torch.__version__, torch.version.cuda, torch.cuda.is_available())"`; install a CUDA-capable PyTorch wheel only if the task requires CUDA. |
| GPU inference/training OOM | Default model uses Swin-L and high resolution; training uses large batches and multi-scale supervision. | Lower resolution, choose a lite/tiny backbone with matching weights, reduce batch size, disable optional outputs only when the workflow allows it, or use a higher-memory GPU. |
| `torch.compile` failures or slowdowns | Version/backend incompatibility or dynamic-size behavior. | The repository expects PyTorch >= 2.5.0 for compile stability; set `compile=False` in `Config` when debugging or using dynamic sizes. |
| BF16/FP16 autocast errors | Backend does not support requested precision. | Use CPU/FP32 or choose a CUDA device with supported precision; inference helpers disable autocast on CPU. |

## Data and model assets

| Symptom | Likely cause | Recovery |
|---|---|---|
| Dataset path is empty or missing `im`/`gt` | `Config.data_root_dir`, `Config.task`, or dataset folder names do not match the expected tree. | Use `sub-skills/configuration-and-data/scripts/birefnet_dataset_check.py` before training/evaluation. |
| Many missing/unexpected checkpoint keys | DDP/compiled prefixes, wrong backbone/config, or wrong checkpoint family. | First clean prefixes with `check_state_dict`; if mismatch remains, route to `model-architecture` to compare `config.bb` and architecture flags. |
| Backbone weights missing when constructing with `bb_pretrained=True` | `Config.weights_root_dir` does not contain the expected backbone `.pth` files. | Use `bb_pretrained=False` for local checkpoint loading or put backbone weights under the configured weights root. |
| Full inference/evaluation cannot start | External model weights or dataset trees were not supplied. | Use bundled dry-run/smoke scripts first; download or provide assets only after confirming hardware and paths. |

## Unsafe or expensive source scripts

- Do not run cleanup scripts that remove checkpoints, logs, predictions, or images unless the user explicitly approves destructive cleanup.
- Do not run Slurm submission or multi-GPU training launchers without user-provided scheduler, GPU, budget, and data details.
- Do not run ONNX conversion by default; it needs optional dependencies, model weights, and substantial memory.

## Where to go next

- Data/config failures: `sub-skills/configuration-and-data/references/troubleshooting.md`
- Model/checkpoint/export failures: `sub-skills/model-architecture/references/troubleshooting.md`
- Inference/postprocessing failures: `sub-skills/inference-and-postprocessing/references/troubleshooting.md`
- Training/evaluation failures: `sub-skills/training-and-evaluation/references/troubleshooting.md`
