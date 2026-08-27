# LimiX installation and environment guide

## When to read

Read this when a LimiX task fails at import, dependency installation, CUDA/flash-attn setup, checkpoint loading, or because the project is not installed as a conventional Python package.

## Project shape

LimiX is a source-checkout project. The public modules used by the runtime workflows are top-level import roots such as `inference`, `model`, `utils`, and `retrieval_extension`; there is no `pyproject.toml`, `setup.py`, or `setup.cfg` packaging metadata in the inspected snapshot.

Practical import options for users:

- run code from the active LimiX checkout root; or
- add the active checkout root to `PYTHONPATH`; or
- create a small local wrapper/project environment that places the checkout root on `sys.path` before importing LimiX modules.

Do not present `pip install limix` as the repository's install path unless a newer checkout adds packaging metadata and the skill has been refreshed.

## Dependency families

The repository's setup evidence points to Python 3.12.7 and PyTorch 2.7.1 with CUDA 12-era wheels. The selected workflows use these dependencies:

| Dependency | Why it matters |
| --- | --- |
| `torch` | model construction, checkpoint loading, CUDA/DDP, tensors, attention paths |
| `numpy`, `pandas`, `scipy` | tabular arrays/dataframes, preprocessing, metrics |
| `scikit-learn` | dataset examples, metrics, encoders, scalers, train/test split, validation |
| `einops` | model post-processing for reconstructed features |
| `huggingface-hub` | optional checkpoint/dataset downloads when users choose network workflows |
| `tqdm` | benchmark/progress loops |
| `typing_extensions` | preprocessing override annotations |
| `kditransform` | KDI preprocessing transforms used by sampled configs |
| `hyperopt` | `sample_inferece_params` search-space sampling helper |
| `optuna` | retrieval hyperparameter search API |
| `flash-attn` | optional CUDA acceleration; source imports without it but flash-attn paths are unavailable |

The Docker/environment guidance also mentions `torchvision`, `torchaudio`, `matplotlib`, `networkx`, and `xgboost`; they are not central to the selected operating workflows unless a user task or newer source requires them.

## Manual setup pattern

A minimal user environment for source-checkout operation usually looks like:

```bash
# Create a Python 3.12 environment with your preferred manager, then install runtime deps.
python -m pip install \
  torch numpy pandas scipy scikit-learn einops tqdm typing_extensions \
  huggingface-hub kditransform hyperopt optuna

# If working outside the checkout root, point Python at the LimiX source checkout.
export PYTHONPATH="/path/to/LimiX:${PYTHONPATH}"
```

For CUDA, install a PyTorch wheel compatible with the host driver and GPU. For flash-attn acceleration, use a wheel or build that matches Python, PyTorch, CUDA, C++ ABI, and platform. If flash-attn is missing, `model.layer.HAVE_FLASH_ATTN` is false; many paths can still fall back to PyTorch scaled-dot-product attention, but flash-attn-specific acceleration is not available.

## Docker setup shape

The repository's Dockerfile uses an NVIDIA CUDA base image, creates a conda environment, installs PyTorch 2.7.1, installs a pre-downloaded flash-attn wheel, then installs scientific Python dependencies. Use Docker when reproducing the repository's CUDA/flash-attn stack matters more than a lightweight local inspection environment.

Important Docker caveats:

- The flash-attn wheel must be available to the Docker build context before the Dockerfile installs it.
- The CUDA base image, PyTorch wheel, driver, and GPU architecture must be compatible.
- The Docker image still needs model checkpoints and datasets mounted or downloaded at runtime.

## Checkpoints and model weights

LimiX workflows require local checkpoint files for actual inference. Public docs reference `LimiX-16M.ckpt` and `LimiX-2M.ckpt` from the Stable AI Hugging Face/ModelScope organization. Checkpoint downloads can be large, network-dependent, and subject to model-license terms. Keep checkpoint paths explicit in commands and do not claim inference was verified unless a local checkpoint was actually loaded.

## Safe diagnostic

From the generated skill root, run:

```bash
python scripts/check_limix_environment.py --config path/to/config.json
```

Add `--expect-cuda` only when CUDA evidence is required for the current task. The diagnostic checks imports, config structure, retrieval/CPU compatibility signals, and torch CUDA availability. It does not download checkpoints or run full model inference.
