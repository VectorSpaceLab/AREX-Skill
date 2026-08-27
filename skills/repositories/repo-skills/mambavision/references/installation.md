# MambaVision installation and smoke checks

This repo skill was verified against `mambavision==1.2.0`. The base package is small, but it depends on a version-matched PyTorch stack and several pinned runtime libraries. The downstream OpenMMLab workflows need an additional set of framework packages.

## Baseline package installation

Start from a fresh Python 3.11+ environment, then install a matching PyTorch / torchvision pair for your hardware before installing MambaVision itself.

Example for a CUDA 12.4 wheel set using the published package:

```bash
python -m pip install --upgrade pip
python -m pip install torch==2.6.0+cu124 torchvision==0.21.0+cu124 --index-url https://download.pytorch.org/whl/cu124
python -m pip install mambavision==1.2.0 tensorboardX==2.6.2.2
python -m pip check
```

If the user is intentionally working from a source checkout, replace the published-package install line with `python -m pip install -e .` from that checkout.

The package dependencies pinned by the repo are:

- `timm==1.0.15`
- `transformers==4.50.0`
- `mamba-ssm==2.2.4`
- `einops==0.8.1`
- `requests==2.32.3`
- `Pillow==11.1.0`
- `tensorboardX==2.6.2.2`

## `mamba-ssm` build note

If `mamba-ssm` needs a local build, make sure a compatible CUDA compiler is present before the install step. In practice that means one of:

- a prebuilt wheel that matches your platform, or
- a CUDA toolkit / `nvcc` installation that matches the active PyTorch wheel.

A missing compiler usually surfaces as a build-isolation failure when installing `mamba-ssm`.

## Optional OpenMMLab stack

Install the OpenMMLab packages only when you need the object-detection or semantic-segmentation workflows:

```bash
python -m pip install mmengine==0.10.1 mmcv==2.1.0 mmdet==3.3.0 mmsegmentation==1.2.2 mmpretrain==1.2.0 opencv-python-headless
python -m pip check
```

If `mmcv` is built from source, keep it aligned with the same PyTorch and CUDA pair you use at runtime.

## Verification commands

Run the bundled checker after installation:

```bash
python scripts/check_mambavision_env.py --help
python scripts/check_mambavision_env.py
python scripts/check_mambavision_env.py --smoke
```

Add `--include-openmmlab` when you want to verify the downstream adapter stack too:

```bash
python scripts/check_mambavision_env.py --include-openmmlab
```

## What the smoke check covers

The checker reports:

- Python and platform information
- `torch` and CUDA availability
- the `mambavision` package version and `create_model` signature
- the number of registered MambaVision factories
- import status for the base classification dependencies
- optional OpenMMLab import status when requested
- an opt-in no-download forward pass for `mamba_vision_T`

If the smoke check fails, read `references/troubleshooting.md` before changing multiple variables at once.
