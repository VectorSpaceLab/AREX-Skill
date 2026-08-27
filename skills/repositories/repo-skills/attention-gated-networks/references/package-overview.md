# Package Overview

## Purpose

Read this for repository-wide facts that apply to both classification and
segmentation routes.

## What this repository provides

Attention-Gated Networks is a legacy PyTorch implementation of attention gates
for medical imaging models. It contains two main workflow families:

- ultrasound scan-plane classification with Sononet, Sononet2, Sononet Grid
  Attention, and aggregation/deep-supervision wrappers;
- 2D/3D medical image segmentation with U-Net, non-local U-Net, CT deep
  supervision, and attention-gated U-Net variants.

The Python distribution name is `AttentionGatedNetworks` version `1.0`. The
importable top-level packages are `models`, `dataio`, and `utils`.

## Installation guidance

The source README uses editable install syntax. For a fresh environment, prefer
a CUDA-capable PyTorch stack plus the legacy dependencies before installing the
repository:

```bash
# Example only: choose torch wheels compatible with the host driver/GPU.
python -m pip install torch torchvision --index-url https://download.pytorch.org/whl/cu117
python -m pip install numpy scipy matplotlib scikit-image h5py pandas tqdm visdom nibabel scikit-learn opencv-python-headless dominate SimpleITK
python -m pip install git+https://github.com/ozan-oktay/torchsample.git@master
python -m pip install git+https://github.com/ozan-oktay/Attention-Gated-Networks.git
```

When working inside a checkout, editable install is also supported:

```bash
python -m pip install -e .
```

The bundled helpers can use an installed distribution, but `--repo-root` is
required when running against a local checkout or resolving relative config
paths. The checkout/package and legacy dependencies are runtime prerequisites;
the skill does not include a substitute package.
The repository is old enough that dependency versions matter. PyTorch 1.x often
requires `numpy<2`; modern scientific packages may prefer NumPy 2. If PyTorch
reports NumPy ABI warnings or `RuntimeError: Numpy is not available`, rebuild
the environment with a compatible NumPy/scientific stack rather than forcing a
single package in isolation.

## Environment validation

Run the bundled environment checker after installation:

```bash
python scripts/check_env.py --repo-root /path/to/Attention-Gated-Networks --mode all
```

If the package is already installed and importable, `--repo-root` may point to a
checkout only for local development. The expected successful signals include:

- `imports-ok`;
- CUDA availability and a tiny tensor allocation;
- `classification-output=(2, 14)` and an attention-classifier output shape;
- `segmentation-output=(1, 4, 16, 16, 16)`;
- `check-env-ok`.

## Configuration families

| Config family | Workflow | Main fields |
| --- | --- | --- |
| `config_sononet_8.json` | ultrasound classification baseline | `arch_type='us'`, `model_type='sononet2'`, `type='classifier'`, `output_nc=14` |
| `config_sononet_grid_att_8*.json` | ultrasound grid-attention classification | `model_type='sononet_grid_attention'`, `type='aggregated_classifier'`, `aggregation_mode` variants |
| `config_unet_ct_dsv.json` | CT 3D deep-supervision segmentation | `arch_type='acdc_sax'`, `model_type='unet_ct_dsv'`, `criterion='dice_loss'` |
| `config_unet_ct_multi_att_dsv.json` | CT 3D multi-attention segmentation | `model_type='unet_ct_multi_att_dsv'`, attention gates plus deep supervision |

All shipped configs contain machine-specific dataset paths that must be
replaced before real runs. Datasets, model weights, and checkpoints are
external resources and are not bundled. In particular, never assume the
historical `/vol/...` paths exist: copy the config and override `data_path.*`,
checkpoint, and writable output locations first.

## Generated helper scripts

| Helper | Purpose |
| --- | --- |
| `scripts/check_env.py` | Repo-wide import, CUDA, classification, and segmentation smoke checks. |
| `sub-skills/classification/scripts/run_classifier.py` | Skill-owned training/testing replacement for classification entry points. |
| `sub-skills/classification/scripts/export_attention_overlay.py` | Safe attention overlay export for Sononet Grid Attention. |
| `sub-skills/segmentation/scripts/run_segmentation.py` | Skill-owned segmentation training replacement. |
| `sub-skills/segmentation/scripts/validate_and_export_maps.py` | Validation-style metric checks and NIfTI feature/attention map export. |

These helpers are intentionally parameterized and avoid the private paths and
long-running defaults found in the source scripts.

## Backend policy

The selected public workflows are CUDA-required for unmodified source modules.
The wrappers move models and tensors to CUDA directly, and timing/attention
paths use CUDA tensors. CPU-only use is possible only after source edits that
are outside this generated skill's default contract.
