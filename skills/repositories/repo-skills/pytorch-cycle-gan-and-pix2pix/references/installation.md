# Installation and runtime setup

This repository is a checkout-oriented Python project rather than a pip-installable package. There is no `pyproject.toml`, `setup.py`, or console-entry-point metadata. Future agents should prepare dependencies, keep the target checkout on Python's import path by running commands from the checkout root, and use the public entry scripts `train.py` and `test.py`.

## Documented dependency baseline

The repository's `environment.yml` documents:

- Python 3.11
- PyTorch 2.4.0
- TorchVision 0.19.0
- CUDA runtime package `pytorch-cuda=12.1` for NVIDIA GPU environments
- NumPy 1.24.3
- scikit-image
- Pillow 10+
- dominate 2.8+
- W&B 0.16+

A CPU-only environment is valid for command construction, dataset validation, API inspection, and tiny smoke tests. Full training is much faster on CUDA, and single-machine DDP requires a compatible CUDA/PyTorch stack.

## Conda setup choices

For a GPU-oriented setup, create an isolated environment with the documented dependency baseline when the host driver supports the CUDA variant:

```bash
conda create -n pytorch-img2img -c pytorch -c nvidia -c conda-forge \
  python=3.11 pytorch=2.4.0 torchvision=0.19.0 pytorch-cuda=12.1 \
  numpy=1.24.3 scikit-image pip
# In the isolated environment you created, install the remaining runtime dependencies:
python -m pip install "Pillow>=10.0.0" "dominate>=2.8.0" "wandb>=0.16.0" beautifulsoup4 lxml
python scripts/check_env.py --repo-root .
```

For a CPU-only inspection/smoke setup, install a CPU PyTorch build plus the runtime dependencies:

```bash
python -m pip install --index-url https://download.pytorch.org/whl/cpu torch==2.4.0 torchvision==0.19.0
python -m pip install numpy==1.24.3 scikit-image "Pillow>=10.0.0" "dominate>=2.8.0" "wandb>=0.16.0" beautifulsoup4 lxml
python scripts/check_env.py --repo-root .
```

Use an isolated environment. Do not install or repair these dependencies in a user's base environment without explicit approval.

## Runtime import checks

Run the bundled check from the generated skill tree, pointing it at a target checkout when needed:

```bash
python scripts/check_env.py --repo-root TARGET_CHECKOUT
```

Add `--require-cuda` only when the task truly needs CUDA verification. A host with visible GPUs is not enough; the target Python must import a CUDA-capable PyTorch build and allocate a tiny CUDA tensor.

## Optional and external surfaces

- W&B is imported by the current visualizer module, so install `wandb` even when not logging to W&B. Use `--use_wandb` only when network access and credentials are available.
- The legacy prose mentions visdom, but current source inspection found no active `visdom` import or `--display_id` option in the main train/test code.
- Cityscapes FCN evaluation and HED edge extraction require external Caffe/pycaffe assets, pretrained model downloads, and in the HED path a MATLAB postprocess. They are documented as reference-only in the data-preparation sub-skill and are not part of the required CPU environment.

## When setup is not enough

Successful imports do not prove that a particular dataset, checkpoint, or GPU workflow is valid. Before a real run:

1. validate the data layout with `data-preparation/scripts/validate_layout.py`,
2. confirm checkpoint architecture flags in `translation-workflows/references/cli-reference.md`,
3. run a small `--num_test 1` or tiny training smoke before a long job,
4. treat CUDA/DDP as unverified unless `scripts/check_env.py --require-cuda` and a task-specific smoke pass.
