---
name: installation-and-configuration
description: "Routes tf-faster-rcnn install, build, CUDA, TensorFlow, Cython
  NMS, and config-preset questions, including safe environment checks and common
  failure recovery."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Installation and Configuration

Use this sub-skill when a tf-faster-rcnn checkout will not install, build, or import cleanly, or when you need to verify CUDA/TensorFlow/protobuf compatibility, Cython NMS extension readiness, or config preset behavior.

## Covered tasks
- set up a legacy Python environment for source inspection or runtime prep
- understand the repo's TensorFlow 1.x / protobuf compatibility window
- build or diagnose `lib/setup.py` and `lib/Makefile`
- choose between GPU NMS, CPU NMS, and pure Python inspection
- read and override `lib/model/config.py` plus `experiments/cfgs/*.yml`
- run a safe smoke check without downloading data or training

## Route elsewhere
- dataset layout, cache, and asset placement -> [dataset-and-assets](../dataset-and-assets/SKILL.md)
- demo image inference and checkpoint use -> [inference-and-demo](../inference-and-demo/SKILL.md)
- training, testing, re-evaluation, and TensorBoard -> [training-and-evaluation](../training-and-evaluation/SKILL.md)
- backbone and graph internals -> [api-and-architecture](../api-and-architecture/SKILL.md)

## Read first
- [Install/build notes](references/install-build.md)
- [Configuration reference](references/configuration.md)
- [Troubleshooting guide](references/troubleshooting.md)

## Safe check
Run the bundled inspector from any directory:
- `python scripts/check_environment.py --repo-root <tf-faster-rcnn-root>`

The inspector only reads local files and imports. It does not download datasets, fetch checkpoints, or start training.

## Remember
- `cfg.USE_GPU_NMS` defaults to `True`.
- `model.nms_wrapper` imports both compiled NMS modules eagerly, so `cfg.USE_GPU_NMS=False` does not by itself make a missing build safe.
- If the inspector reports missing `nvcc`, `CUDAHOME`, or `model.nms_wrapper`, start with the install/build and troubleshooting references before trying demo or training routes.
