# Pytorch-UNet package overview

Pytorch-UNet is a compact PyTorch implementation of the U-Net architecture for semantic segmentation, originally oriented around Kaggle's Carvana Image Masking Challenge but adaptable to custom binary, multiclass, portrait, and medical segmentation data.

## Main capability map

| User goal | Skill route | Key runtime files |
| --- | --- | --- |
| Build or adapt a `UNet` model, choose channels/classes/bilinear, load checkpoint weights, use torch.hub, or run a forward smoke check | `sub-skills/model-api/` | model API reference and `scripts/model_smoke.py` |
| Prepare image/mask folders, validate mask naming, construct training commands, understand W&B/checkpoints/CUDA/AMP | `sub-skills/data-training/` | data/training references and `scripts/validate_dataset_layout.py` |
| Run prediction, save masks, convert palettes, compute Dice, or debug `predict.py`/evaluation behavior | `sub-skills/prediction-evaluation/` | prediction/evaluation references and `scripts/prediction_smoke.py` |

## Public surfaces

- Python import: `from unet import UNet`.
- Model blocks: `DoubleConv`, `Down`, `Up`, `OutConv` from `unet.unet_parts` when architecture internals are needed.
- Training CLI surface: underlying `train.py` in a user checkout, previewed or executed through bundled `data-training/scripts/training_cli_wrapper.py`.
- Prediction CLI surface: underlying `predict.py` in a user checkout, previewed or executed through bundled `prediction-evaluation/scripts/prediction_cli_wrapper.py`.
- Torch Hub helper: `unet_carvana(pretrained=False, scale=0.5)` through `hubconf.py`.
- Dataset utilities: `BasicDataset`, `CarvanaDataset`, `BasicDataset.preprocess`.
- Metrics/evaluation: `evaluate`, `dice_coeff`, `multiclass_dice_coeff`, `dice_loss`.

## Dependency notes

The repository documents PyTorch 1.13+ and Python 3.6+ historically. Current inspection used Python 3.11 with a CUDA-capable PyTorch 2.5.1 environment. Runtime dependencies include Pillow, NumPy, matplotlib, tqdm, and W&B. The repository itself has no packaging metadata (`pyproject.toml` or `setup.py`), so future agents usually run from a checkout root or add the checkout root to `PYTHONPATH` unless they package it separately.

## Backend notes

CUDA is recommended by the README for practical training and AMP acceleration, but the model, dataset validation, prediction smoke checks, and small CPU forward passes are functional on CPU. Treat CUDA and AMP as accelerators except when a user specifically requires GPU training evidence.

## Data and network notes

The Carvana data helper is not a safe default runtime script. It prompts for Kaggle credentials, installs or upgrades `kaggle`, downloads large archives, unzips them, and writes into the data folders. Use the generated dataset validator for safe local checks, and ask for explicit approval before credentialed/network downloads.
