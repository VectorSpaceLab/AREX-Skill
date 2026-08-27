# MambaVision repo provenance

This file records the source snapshot and refresh baseline used to create the generated MambaVision operating skill.

## Source snapshot

| Field | Value |
| --- | --- |
| Repository | MambaVision |
| Public remote | `https://github.com/NVlabs/MambaVision.git` |
| Branch | `main` |
| Source commit | `7860a506b2eb844eaaae676f08461ce8c3c26f43` |
| Exact tag | none |
| Package name | `mambavision` |
| Package version | `1.2.0` |
| Working tree state during finalization | dirty because the generated `skills/` tree was present |
| Generated skill root | `skills/disco/mambavision/` |

The commit above is the refresh baseline. Refresh this skill when the source commit, package version, public APIs, command flags, model catalog, OpenMMLab adapter code, or downstream config families change.

## Evidence used

Primary source and package evidence:

- `README.md` for install, model table, checkpoints, classification, training, detection, and segmentation examples.
- `setup.py`, `setup.cfg`, and `requirements.txt` for package identity, Python support, and pinned dependencies.
- `mambavision/__init__.py`, `mambavision/models/__init__.py`, `mambavision/models/registry.py`, and `mambavision/models/mamba_vision.py` for public factories, checkpoint loading, registry behavior, and model defaults.

Classification and training workflow evidence:

- `mambavision/dummy_test.py` for no-download random-input smoke behavior.
- `mambavision/validate.py`, `mambavision/validate_pip_model.py`, `mambavision/validate.sh`, and `mambavision/validate_pip.sh` for validation flags and pretrained/local-checkpoint behavior.
- `mambavision/train.py`, `mambavision/train.sh`, `mambavision/configs/*.yaml`, `mambavision/scheduler/cosine_lr.py`, and `mambavision/utils/datasets.py` for training presets, data loaders, scheduler behavior, and launch options.
- `mambavision/throughput_measure.py` for throughput intent and unsafe benchmark details that were replaced by a safer bundled helper.

Downstream adapter evidence:

- Detection docs/configs/tools for Cascade Mask R-CNN COCO workflows, `MM_mamba_vision` registration, backbone channel contracts, checkpoint path settings, and metric expectations.
- Segmentation docs/configs/tools for UPerNet ADE20K workflows, tiny/small/base/L3 recipe selection, crop sizes, AMP behavior, channel contracts, and dataset layout.

## Verification snapshot

During construction, the inspection environment verified these facts without recording any private environment paths in the public skill:

- `pip check` passed after installing the package and required dependencies.
- `create_model` exposed the signature `(model_name, pretrained=False, checkpoint_path='', **kwargs)`.
- The registry exposed 11 MambaVision factory names.
- A no-download CUDA forward smoke for `mamba_vision_T` on a `1 x 3 x 64 x 64` tensor returned finite `1 x 1000` logits.
- Downstream OpenMMLab guidance was treated as optional workflow coverage; long training/evaluation jobs and dataset-bound native runs were not executed during production.
