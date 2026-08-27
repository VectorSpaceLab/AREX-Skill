---
name: "3d-resnets-pytorch"
description: "Routes 3D ResNets PyTorch video action-recognition workflows
  across training, inference, and data preparation."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# 3D ResNets PyTorch

Use this root skill when the user asks about the 3D ResNets PyTorch repository, its CLI flags, its dataset layouts, or its video action-recognition workflows.

## Read first

- `references/cli-reference.md`
- `references/troubleshooting.md`
- `references/repo-provenance.md`
- `scripts/check_imports.py`
- `scripts/check_main_help.py`

## What this skill covers

- Training, validation, inference, and fine-tuning for video action recognition.
- Dataset preparation from raw videos into JPEG frame trees, RGB HDF5 files, and annotation JSONs.
- Checkpoint handling, model-family selection, and result evaluation.
- Common data-layout and runtime compatibility pitfalls.

## Route to a sub-skill

### `training-and-inference`
Use this route for:

- Fresh training runs, resume flows, and pretrained fine-tuning.
- Validation-only runs and sliding-window inference.
- Result scoring and DataParallel checkpoint cleanup.
- Questions about model families, class counts, `ft_begin_module`, or `resume_path` / `pretrain_path` behavior.

Read:

- `sub-skills/training-and-inference/SKILL.md`
- `sub-skills/training-and-inference/references/workflows.md`
- `sub-skills/training-and-inference/references/model-catalog.md`
- `sub-skills/training-and-inference/references/troubleshooting.md`
- `sub-skills/training-and-inference/scripts/evaluate_results.py`
- `sub-skills/training-and-inference/scripts/strip_dataparallel.py`

### `data-preparation`
Use this route for:

- Extracting JPEG frames or RGB HDF5 files from raw videos.
- Building Kinetics, UCF101, HMDB51, MIT, or ActivityNet JSON metadata.
- Adding ActivityNet `fps` fields.
- Questions about class directories, split files, HDF5 manifests, or `jpg` versus `hdf5` layout.

Read:

- `sub-skills/data-preparation/SKILL.md`
- `sub-skills/data-preparation/references/workflows.md`
- `sub-skills/data-preparation/references/data-formats.md`
- `sub-skills/data-preparation/references/troubleshooting.md`
- `sub-skills/data-preparation/scripts/extract_video_frames.py`
- `sub-skills/data-preparation/scripts/extract_video_hdf5.py`
- `sub-skills/data-preparation/scripts/build_annotation_json.py`

## Quick runtime helpers

- `scripts/check_imports.py` verifies that the core source modules import from a checkout and applies the temporary legacy `Scale` alias when needed.
- `scripts/check_main_help.py` prints the full `main.py` CLI help through the same compatibility shim.
- `scripts/run_main.py` forwards into the repository CLI after preparing the checkout and compatibility shim.

## Shared environment facts

This repo expects a Python environment with PyTorch, torchvision, pandas, h5py, scikit-learn, joblib, and FFmpeg/FFprobe available on PATH.

A modern torchvision wheel may not expose `torchvision.transforms.Scale`. If that happens, use the compatibility shim in `scripts/_torchvision_compat.py` or a legacy torchvision release that still ships `Scale`.

## Route selection guidance

- If the user already has prepared videos and annotation JSONs, start with `training-and-inference`.
- If the user still needs frames, HDF5 files, or split JSONs, start with `data-preparation`.
- If the request mentions both, do data preparation first unless the videos and labels are already ready.
- If the user only wants command discovery or environment checks, use the root helpers and the sub-skill references rather than reopening the source repo.

## Common handoff sequence

1. Prepare or verify the dataset layout with `data-preparation`.
2. Verify the environment with `scripts/check_imports.py`.
3. Inspect the CLI with `scripts/check_main_help.py`.
4. Run the desired training or inference command with `scripts/run_main.py`.
5. Score or clean outputs with the training-and-inference helpers.

## Don’t do this

- Do not point future agents back to the original checkout paths.
- Do not use `flow` with JPEG inputs.
- Do not assume resume checkpoints can change architecture.
- Do not score `--inference_no_average` JSON with the result evaluator before aggregating segment outputs.
