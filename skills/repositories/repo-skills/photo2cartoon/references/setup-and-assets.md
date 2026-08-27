# Setup and Assets

## Purpose

Read this before installing dependencies, looking for model files, or deciding whether a Photo2Cartoon run can be executed. The repo is a source-script project with legacy ML dependencies and external model/data downloads; treat setup as asset-gated rather than a normal `pip install` package.

## Repository Shape

There is no `pyproject.toml`, `setup.py`, `setup.cfg`, `requirements.txt`, or package metadata. Public behavior comes from source modules and scripts:

- `test.py`: PyTorch `.pt` inference flow.
- `test_onnx.py`: ONNX inference flow.
- `predict.py` and `cog.yaml`: Cog/Replicate-style prediction wrapper and dependency snapshot.
- `data_process.py`: batch preprocessing for training photos.
- `train.py`: GAN training CLI.
- `models/`: generator, discriminator, training object, Face ID model code.
- `utils/`: preprocessing, face detection, segmentation, and tensor/image helpers.

Use a target checkout path explicitly with bundled scripts; do not rely on the current working directory.

## External Assets

| Asset | Expected location in source-compatible checkout | Needed for |
|---|---|---|
| `photo2cartoon_weights.pt` | `models/photo2cartoon_weights.pt` | PyTorch portrait inference and pretrained training start. |
| `photo2cartoon_weights.onnx` | `models/photo2cartoon_weights.onnx` | ONNX inference. |
| `seg_model_384.pb` | `utils/seg_model_384.pb` | Face segmentation for preprocessing, PyTorch inference, ONNX inference, and batch data processing. |
| `model_mobilefacenet.pth` | `models/model_mobilefacenet.pth` | Face ID loss during GAN training. |
| cartoon data | `dataset/photo2cartoon/trainB`, `dataset/photo2cartoon/testB` | Domain B training/test data. |
| user photos | `dataset/photo2cartoon/trainA`, `dataset/photo2cartoon/testA` after preprocessing | Domain A training/test data. |

The published README points to cloud-drive downloads for these assets. This skill does not include them and the generated helpers do not download them.

## Dependency Snapshots

The README lists an older research stack:

- Python 3.6
- PyTorch 1.4
- TensorFlow GPU 1.14
- `face-alignment`
- `dlib`
- `onnxruntime`

The Cog config records a different deployment-era stack:

- Python 3.8
- `torch==1.8.0`, `torchvision==0.9.0`
- `numpy==1.19.2`
- `opencv-python==4.3.0.38`
- `face-alignment==1.3.4`
- `tensorflow-gpu==2.5.0`
- `dlib` installed before Python packages
- system `libgl1-mesa-glx` and `libglib2.0-0`

These snapshots are evidence, not universal install commands. Modern Python, TensorFlow, dlib, CUDA, and torch wheels may not match. Use a private environment or container for execution and do not mutate a shared user environment to satisfy this legacy stack.

## Minimal Checks

For source/asset validation:

```bash
python scripts/check_repository_assets.py --root /path/to/photo2cartoon-checkout
```

For inference asset validation:

```bash
python sub-skills/portrait-inference/scripts/check_photo2cartoon_assets.py --repo-root /path/to/photo2cartoon-checkout --mode pytorch
python sub-skills/portrait-inference/scripts/check_photo2cartoon_assets.py --repo-root /path/to/photo2cartoon-checkout --mode onnx
```

For source model inspection without external weights:

```bash
python sub-skills/model-internals/scripts/model_forward_smoke.py --repo-root /path/to/photo2cartoon-checkout
```

For dataset layout validation before training:

```bash
python sub-skills/data-and-training/scripts/validate_dataset_layout.py --dataset-root /path/to/dataset/photo2cartoon
```

## Backend Strategy

- CPU is enough for static source inspection, asset checks, dataset validation, ONNX CPU provider planning, and synthetic model-forward checks.
- CUDA is useful for training and faster PyTorch inference, but full training is expensive and was not required for this skill's construction.
- Do not claim GPU verification from a CPU-only import. If a user explicitly requires GPU execution, verify torch CUDA or ONNX provider availability in that user's target environment.

## Safe Environment Strategy

1. Choose the needed workflow first: preprocessing, PyTorch inference, ONNX inference, Cog deployment, or training.
2. Install only that workflow's dependency group in a private env/container.
3. Validate files before importing heavy frameworks.
4. Run bundled safe checkers before asset-gated prediction or training.
5. Stop and ask for missing assets instead of attempting network downloads inside an agent session unless the user explicitly authorizes that.
