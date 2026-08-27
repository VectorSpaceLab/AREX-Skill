# Installation and Runtime Readiness

Read this before running repository workflows or deciding which checks are safe. This repository is a source-script PyTorch project rather than a packaged library with `pyproject.toml` or `setup.py`.

## Dependency surface

The repository requirement file lists:

- `torch>=1.6` and `torchvision` for model, transforms, and dataset processing;
- `numpy`, `pandas`, `tqdm`, `opencv-python`, and `pillow` for metrics, images, and progress;
- `lmdb` for LMDB datasets and the optional LMDB preparation mode;
- `tensorboardX` for TensorBoard logging;
- `wandb` for optional Weights & Biases logging.

Prefer an environment whose PyTorch build matches the user's CUDA driver and GPU needs. Avoid reinstalling a working PyTorch stack just to satisfy optional W&B logging.

## Install pattern

For a fresh target checkout, use an isolated Python environment and install the repository requirements:

```bash
python -m pip install -r requirement.txt
```

If the user only needs config inspection, dataset-layout checks, or result-pair evaluation, the bundled helper scripts in this skill avoid importing the repository and need only lightweight packages such as Pillow or NumPy depending on the helper.

## Source layout expectations

The repository scripts import top-level packages named `core`, `data`, and `model`. Run the source scripts from the checkout root or configure `PYTHONPATH` so those packages resolve. The bundled helpers accept explicit paths and do not rely on being inside the checkout.

## CUDA and CPU expectations

Stock configs contain `gpu_ids`, and the model wrapper chooses `cuda` when `gpu_ids` is not `None`. A normal training/inference run therefore needs:

- a CUDA-capable PyTorch build;
- visible GPUs selected with `-gpu/--gpu_ids` or config `gpu_ids`;
- enough GPU memory for the selected image size, batch size, U-Net channels, and 2000-step reverse diffusion.

CPU-only execution is not a standard documented workflow. If a user asks for CPU-only smoke tests, use the bundled helpers and tiny config/model checks; do not claim that full stock training/inference was validated on CPU.

## External prerequisites

Do not silently fetch or assume these resources:

- face datasets such as FFHQ or CelebaHQ;
- preprocessed LR/HR/SR image roots or LMDB stores;
- pretrained checkpoint stems and their `_gen.pth` / `_opt.pth` files;
- W&B credentials or logged-in state;
- large result directories for evaluation.

Surface the missing resource, then ask before network downloads, credentialed operations, or long GPU runs.

## Smoke checks

Use the root environment checker for a target checkout:

```bash
python scripts/check_environment.py --repo-root /path/to/checkout --config /path/to/checkout/config/sr_sr3_16_128.json --cuda
```

Use sub-skill helpers for narrower checks:

- dataset image-layout validation: `sub-skills/data-preparation/scripts/validate_dataset_layout.py`;
- config parsing: `sub-skills/model-configuration/scripts/inspect_config.py`;
- command construction: training and inference/sampling command builders;
- metrics: `sub-skills/evaluation-and-logging/scripts/evaluate_result_pairs.py`.

These helpers are safe preflight tools; they do not train, infer, download, log to W&B, or mutate checkpoints.
