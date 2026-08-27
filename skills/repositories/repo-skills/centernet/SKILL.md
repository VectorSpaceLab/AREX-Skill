---
name: centernet
description: "Routes CenterNet object-detection training, evaluation,
  configuration, and setup workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# CenterNet

CenterNet is a COCO-based object-detection repository with two main command-line entry points, `train.py` and `test.py`, plus legacy compiled extensions for NMS, custom pooling, and the COCO Python API.

Use this skill when you need to train a CenterNet model, run evaluation on COCO splits, choose between the `CenterNet-52` and `CenterNet-104` configs, or diagnose the repo's runtime/build prerequisites.

## Start here

1. Read `references/workflows.md` for the end-to-end training and evaluation flow.
2. Read `references/cli-reference.md` for the `train.py` and `test.py` flags and output paths.
3. Read `references/configuration.md` before changing model or dataset settings.
4. Read `references/data-layout.md` before pointing the repo at COCO data or caches.
5. After building the COCO API and custom extensions, run `scripts/check_install.py --repo-root <checkout>` to verify imports, CUDA, and the compiled extensions.
6. Read `references/troubleshooting.md` when an import, build, GPU, or data-path check fails.
7. Read `references/repo-provenance.md` before deciding whether this skill is current for a checkout.

## Installation and setup

- Use a CUDA-capable Python environment. The training and test code call `.cuda()` and expect a working NVIDIA backend.
- Install the runtime stack used by the repo: `torch`, `numpy`, `opencv-python`, `matplotlib`, `tqdm`, `scipy`, `h5py`, `Cython`, and `pycocotools`.
- Build the COCO Python API in `data/coco/PythonAPI` and the custom CenterNet extensions in `external/` and `models/py_utils/_cpools/`.
- If the extension build fails on a modern toolchain, read `references/troubleshooting.md` before retrying with a different version mix.

## Common routes

- Train a detector or resume from a checkpoint: `references/workflows.md`
- Run validation, testing, or multi-scale evaluation: `references/workflows.md`
- Compare `CenterNet-52` and `CenterNet-104`, or review config keys: `references/configuration.md`
- Understand COCO directory layout, cache files, and result output: `references/data-layout.md`
- Diagnose missing compiled modules, CUDA, checkpoints, or COCO paths: `references/troubleshooting.md`

## Quick checks

- `python scripts/check_install.py --repo-root <checkout>` after the compiled extensions are built
- `python train.py --help`
- `python test.py --help`

## Notes

- The repository is not published as a packaged wheel; work from a repository checkout.
- `config.py` defines the runtime defaults that `train.py` and `test.py` load through the selected JSON config.
- The shipped dataset registry currently contains `MSCOCO` only.
