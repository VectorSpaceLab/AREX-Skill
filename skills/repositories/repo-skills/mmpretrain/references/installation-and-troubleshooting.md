# Installation and cross-cutting troubleshooting

Read this when MMPreTrain import, model-zoo lookup, backend selection, or optional dependencies fail before a focused workflow can start.

## Install patterns

MMPreTrain is an OpenMMLab package. A typical user install is:

```bash
pip install -U openmim
mim install "mmpretrain>=1.0.0rc8"
```

For development or package-dispatched tools:

```bash
pip install -U openmim
mim install -e .
```

For multi-modal models:

```bash
mim install "mmpretrain[multimodal]>=1.0.0rc8"
```

Public prerequisites from the repository documentation:

- Python 3.7+
- PyTorch 1.8+
- CUDA 10.2+ when GPU execution is selected
- `mmcv>=2.0.0,<2.4.0`
- `mmengine>=0.8.3,<1.0.0`

CPU-only installs are valid for import checks, config inspection, model construction without weights, and many small utilities. GPU/distributed claims require a compatible GPU package stack and a backend smoke check.

## Minimal no-download check

Use the bundled helper:

```bash
python scripts/check_mmpretrain_env.py --backend cpu --pattern resnet18 --skip-build
python scripts/check_mmpretrain_env.py --backend cpu --model resnet18_8xb32_in1k
```

Expected success includes package versions, `mmpretrain` import, a model-list sample, and (unless skipped) a no-download `get_model(..., pretrained=False)` build.

## Common install/import failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `MMCV==... is used but incompatible` | `mmcv` is outside `>=2.0.0,<2.4.0` | Reinstall with MIM so the `mmcv` wheel matches your PyTorch/CUDA version. |
| `MMEngine==... is used but incompatible` | `mmengine` is outside `>=0.8.3,<1.0.0` | Install a compatible `mmengine` version and rerun the environment check. |
| `File ... .mim/model-index.yml does not exist` during `list_models` or `get_model` | Package data for ModelHub/MIM was not installed or an editable install skipped the `.mim` assets | Reinstall with `mim install -e .` or a normal MIM package install so `model-index.yml`, configs, and tools are packaged. Avoid treating `import mmpretrain` alone as a complete check. |
| Torch imports with NumPy ABI warnings | Old PyTorch/MMCV wheel with NumPy 2.x | Use `numpy<2` or a newer compatible PyTorch/MMCV stack; rerun `pip check` and a torch tensor smoke. |
| `opencv-python` conflicts after NumPy downgrade | New OpenCV wheel requires NumPy 2 | Install an OpenCV wheel compatible with the chosen NumPy/PyTorch stack. |
| Inferencer tries to download a checkpoint unexpectedly | Inferencer constructors default to `pretrained=True` | Pass `pretrained=False` for offline architecture checks or pass an explicit local checkpoint path. |
| CUDA device requested but unavailable | CPU-only torch/MMCV, hidden GPUs, driver mismatch, or container passthrough missing | Run the backend section of `scripts/check_mmpretrain_env.py --backend cuda`; install a CUDA-compatible torch/MMCV build only if the task truly requires CUDA. |

## Optional dependency gates

Install optional groups only for selected workflows:

- `mmpretrain[multimodal]` for captioning, VQA, grounding, and some retrieval tasks.
- `grad-cam` for CAM visualization.
- `scikit-learn` for t-SNE and selected analysis utilities.
- TorchServe and model archiver packages for service packaging.
- Dataset-provider CLIs and credentials for MIM dataset downloads.

Do not install all extras just to inspect ordinary configs or no-download APIs.

## Backend policy

- CPU is enough for package import, `list_models`, config inspection, no-download `get_model`, dataset/config validation, and many helper scripts.
- CUDA is required to truthfully validate GPU training/inference performance, NCCL distributed jobs, and accelerator-specific failures.
- A CPU environment cannot be reported as CUDA-verified. If the user asks for GPU behavior, verify `torch.cuda.is_available()`, device count/name, and a tiny tensor allocation before running MMPreTrain GPU commands.

## Network and data boundaries

Some examples download pretrained checkpoints or large datasets. Keep these separate from package checks:

1. Confirm package import/model-zoo/config logic without downloads.
2. Ask whether network and storage are allowed when a checkpoint or dataset must be fetched.
3. Prefer explicit local checkpoint/data paths for reproducible runs.
4. Stop rather than guessing when credentials, dataset accounts, external services, or cluster resources are required.
