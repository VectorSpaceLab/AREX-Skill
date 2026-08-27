# fastMRI Package Overview

`fastmri` is a PyTorch-focused MRI reconstruction package for fastMRI-style HDF5 k-space data. The generated skill covers the packaged library plus selected safe workflows distilled from repository examples.

## Packaged Library Surface

- `fastmri`: top-level complex math, FFT, coil combine, SSIM loss, and reconstruction utility exports.
- `fastmri.data`: HDF5 datasets, mask functions, data transforms, volume samplers, annotation datasets, and directory helpers.
- `fastmri.models`: U-Net, VarNet, AdaptiveVarNet, sensitivity models, and acquisition policy modules.
- `fastmri.pl_modules`: PyTorch Lightning data/module wrappers for U-Net and VarNet workflows.
- `fastmri.evaluate`: file-based MSE, NMSE, PSNR, and SSIM evaluation utilities.

## Core Dependencies

Package metadata lists `numpy`, `scikit_image`, `torchvision`, `torch`, `runstats`, `pytorch-lightning`, `h5py`, `PyYAML`, `torchmetrics`, and `pandas`. This checkout also imports `requests` from `fastmri.data.mri_data`; install `requests` if `fastmri.data` import fails.

Use the root `scripts/check_fastmri_environment.py` helper to confirm importability before writing longer workflows.

## Selected Example Evidence

The skill distills these example families into bundled references/scripts:

- Zero-filled baseline reconstruction becomes `sub-skills/evaluation-submission/scripts/zero_filled_reconstruction.py`.
- U-Net and VarNet demo training flows become explicit-path training guidance and a command renderer in `sub-skills/lightning-training/`.
- Pretrained U-Net and VarNet inference scripts are represented as offline-safe recipes that require a local `state_dict` unless the user authorizes downloads.
- Tests provide safe native verification candidates for masks, transforms, math, model shapes, data loaders, and Lightning fast-dev wiring.

## Advanced or Reference-Only Areas

- `banding_removal/` contains a separate legacy/research package tree excluded from the packaged `fastmri` distribution.
- BART compressed sensing requires an external BART install plus `TOOLBOX_PATH` and `PYTHONPATH` setup.
- Adaptive VarNet and feature VarNet examples recommend separate pinned environments with different Lightning/torch expectations.
- RadiologyJohnson2022, annotation visualization notebooks, raw data manifests, external prostate data/code, and public dataset downloads are not bundled runtime dependencies.

## Safe Operating Defaults

- Use local user-provided HDF5 data and checkpoints; do not silently download datasets or model weights.
- Use CPU/tiny-fixture smoke checks before GPU, DDP, long training, or large data runs.
- Keep generated output directories explicit and outside the skill tree.
- Validate prediction HDF5 files before computing metrics or preparing submission-style folders.
