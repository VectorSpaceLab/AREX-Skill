# MambaVision troubleshooting

Use this file for cross-cutting issues that affect several MambaVision workflows. For workflow-specific data layouts and command patterns, read the matching sub-skill troubleshooting reference after this overview.

## `mamba-ssm` import or build failures

Symptoms:

- `ModuleNotFoundError: No module named 'mamba_ssm'`
- build-isolation failure while installing `mamba-ssm`
- missing compiler or `nvcc` during installation
- selective-scan or CUDA extension import errors when the package loads

Likely causes:

- the active PyTorch wheel and the `mamba-ssm` build inputs do not match
- a CUDA compiler is missing when the package is built from source
- the environment mixes multiple incompatible installs

What to do:

1. Reinstall into a clean environment with a matching PyTorch / torchvision pair.
2. If the wheel has to build locally, provide a CUDA compiler that matches the runtime wheel.
3. Re-run `python scripts/check_mambavision_env.py` and `python scripts/check_mambavision_env.py --smoke` after fixing the environment.
4. Use `python -m pip check` to catch conflicts.

## Model factory or checkpoint errors

Symptoms:

- `KeyError` for an unknown model name
- `FileNotFoundError` for a local checkpoint path
- size mismatch after loading a checkpoint
- unexpected download when you only wanted a local file

Likely causes:

- the requested factory name is not one of the published MambaVision variants
- the checkpoint family does not match the requested model family
- `--pretrained` was enabled when a no-download path was intended

What to do:

1. Confirm the model name with `sub-skills/classification/references/model-overview.md` or `scripts/check_mambavision_env.py --smoke`.
2. Keep the checkpoint family aligned with the selected backbone family.
3. Use `checkpoint_path` for a local file load and leave `pretrained=False` for offline smoke tests.
4. If you only need the package imported, skip the pretrained flag entirely.

## OpenMMLab registry or ABI mismatch

Symptoms:

- `MM_mamba_vision is not in the MODELS registry`
- `ImportError` or `undefined symbol` from `mmcv`, `mmdet`, `mmseg`, or `mmpretrain`
- the OpenMMLab workflow fails before the config or dataset is read

Likely causes:

- the OpenMMLab stack was installed against a different torch/CUDA pair
- the adapter module is not importable in the target project
- the framework changed working directories and dropped the adapter from `PYTHONPATH`

What to do:

1. Reinstall the pinned OpenMMLab packages from `references/installation.md`.
2. Make sure the adapter module remains importable before the runner builds the model.
3. If the launcher changes directories, add the adapter directory to `PYTHONPATH` before starting the job.
4. Re-run `python scripts/check_mambavision_env.py --include-openmmlab`.

## Workflow-specific data or metric issues

Symptoms:

- ImageNet/ImageFolder, LMDB, COCO, or ADE20K layout errors
- metrics are far from the published ranges
- a training or evaluation command starts, but the wrong split, crop size, or evaluation metric was used

Likely causes:

- dataset roots and split names do not match the recipe
- the wrong backbone or checkpoint family was paired with the config
- the workflow-specific CLI flags were translated incorrectly

What to do:

- Classification and validation: read `sub-skills/classification/references/troubleshooting.md`
- Training and fine-tuning: read `sub-skills/training/references/troubleshooting.md`
- COCO detection: read `sub-skills/object-detection/references/troubleshooting.md`
- ADE20K segmentation: read `sub-skills/semantic-segmentation/references/troubleshooting.md`

## Safe debug order

When several things are wrong at once, fix them in this order:

1. Environment and import readiness.
2. Base package and checkpoint family.
3. OpenMMLab adapter import and ABI compatibility.
4. Workflow-specific data layout or metric selection.
5. Launcher, distributed, or batch-size tweaks.
