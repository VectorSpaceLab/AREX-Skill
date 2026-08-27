---
name: fastmri
description: "Use fastMRI for MRI reconstruction data loading, MRI operators,
  reconstruction models, Lightning training, evaluation, and submission
  preparation."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# fastMRI

Use this repo skill when a task involves the `fastmri` Python package, fastMRI HDF5 k-space data, MRI reconstruction baselines, U-Net/VarNet models, PyTorch Lightning training, or fastMRI metric/submission-style outputs.

This skill targets the packaged `fastmri` library and selected self-contained workflows distilled from the repository examples. It assumes the user provides local fastMRI-style HDF5 data, checkpoints, and any optional external tools; it does not download datasets, model weights, or BART automatically.

## Start Here

1. Confirm the active Python can import `fastmri`; for data/model workflows also confirm `torch`, `h5py`, `pytorch_lightning`, `torchmetrics`, and `requests` if `fastmri.data` is imported.
2. Identify the task family from the route table below, then open the matching sub-skill before writing code or commands.
3. Keep original fastMRI data/checkpoints outside the skill; use bundled scripts only as helpers and generate user outputs in user-specified locations.
4. Prefer CPU-safe smoke checks and tiny fixtures before long training, GPU inference, external downloads, or leaderboard packaging.

## Sub-Skill Routes

| User intent | Read |
| --- | --- |
| Inspect `.h5` keys, choose `singlecoil` vs `multicoil`, build `SliceDataset`/`CombinedSliceDataset`, configure masks/transforms, or debug cache/sample-rate issues. | [data-loading](sub-skills/data-loading/SKILL.md) |
| Use complex tensor conventions, centered FFT/IFFT, `rss`, crop/normalization helpers, `SSIMLoss`, or array metric shape checks. | [mri-operators](sub-skills/mri-operators/SKILL.md) |
| Instantiate/debug U-Net, VarNet, NormUnet, AdaptiveVarNet, LOUPE/policy modules, tiny model shape checks, or offline pretrained inference. | [model-architectures](sub-skills/model-architectures/SKILL.md) |
| Build PyTorch Lightning train/test workflows with `FastMriDataModule`, `UnetModule`, `VarNetModule`, checkpoints, CPU fast-dev, DDP, or `combine_train_val`. | [lightning-training](sub-skills/lightning-training/SKILL.md) |
| Save reconstructions, validate prediction HDF5 files, compute MSE/NMSE/PSNR/SSIM, build zero-filled baselines, convert v2 filenames, or prepare submission outputs. | [evaluation-submission](sub-skills/evaluation-submission/SKILL.md) |

## Shared References and Scripts

- [Package overview](references/package-overview.md) summarizes package scope, installed dependency facts, selected examples, and advanced/example-only branches.
- [Troubleshooting](references/troubleshooting.md) covers cross-cutting install/import, optional dependency, data, backend, and workflow failure modes.
- [Repo provenance](references/repo-provenance.md) records the source commit, package version, dirty-state baseline, and evidence paths used to create this skill.
- [Routing metadata](references/repo-routing-metadata.json) provides structured scenario placement for managed `repo-skills-router` import.
- [Environment check script](scripts/check_fastmri_environment.py) prints a JSON import/backend/dependency summary for the active Python environment.

## Common Task Patterns

- Data-to-training: read [data-loading](sub-skills/data-loading/SKILL.md), then [lightning-training](sub-skills/lightning-training/SKILL.md), then [evaluation-submission](sub-skills/evaluation-submission/SKILL.md) for output validation.
- Tensor/operator debugging: read [mri-operators](sub-skills/mri-operators/SKILL.md) first, then route to [model-architectures](sub-skills/model-architectures/SKILL.md) if the error happens inside U-Net/VarNet.
- Pretrained inference: read [model-architectures](sub-skills/model-architectures/SKILL.md) and require a user-supplied local checkpoint unless the user explicitly authorizes network downloads.
- Submission preparation: read [evaluation-submission](sub-skills/evaluation-submission/SKILL.md), validate prediction files before metrics, and treat public leaderboard upload as unavailable unless the user confirms a current destination.

## Important Caveats

- The package metadata declares core dependencies but this checkout's `fastmri.data` also imports `requests`; install `requests` if `ModuleNotFoundError: requests` appears.
- The README notes a historical `h5py`/HDF5 memory leak concern for tensor conversion; if users see memory growth during large HDF5 reads, prefer a conda `h5py` build with an older compatible HDF5 as described in the package docs.
- The repository examples often assume GPU/DDP defaults, repo-local `fastmri_dirs.yaml`, public checkpoint downloads, or separate pinned environments. The skill distills those workflows into explicit-path, offline-safe guidance instead of depending on original example files.
- `banding_removal/`, BART compressed sensing, adaptive VarNet, feature VarNet, RadiologyJohnson2022, notebooks, annotation visualization, external prostate data/code, and raw data manifests are reference or advanced evidence unless a user explicitly asks for those areas and accepts their extra dependencies.
