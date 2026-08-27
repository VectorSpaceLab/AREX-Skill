# Installation and Environment

## Purpose

Read this when setting up Scenic for repository use, checking whether an environment is healthy, or deciding which optional project dependencies/backends are needed.

## Core install

Scenic is a Python 3.9+ JAX/Flax research codebase. From a Scenic checkout or release source, the documented quickstart is:

```bash
python -m pip install .
python - <<'PY'
import scenic
import scenic.app
from scenic.dataset_lib import datasets
from scenic.model_lib import models
print('Scenic import OK')
print('lazy datasets:', sorted(datasets._IMPORT_TABLE)[:5], '...')
print('registered models:', sorted(models.ALL_MODELS)[:5], '...')
PY
```

Use an isolated environment. Do not install broad project requirements until the selected project needs them.

## Minimum inspection/runtime stack

The core package metadata names these runtime families:

- `absl-py`, `ml-collections`, and `clu` for app flags, configs, logging, metric writers, and platform artifacts.
- `jax`/`jaxlib`, `flax`, `numpy`, and `optax` for model, optimizer, and training-loop APIs.
- `tensorflow` and `tensorflow-datasets` for input pipelines and TFDS-backed datasets.
- `immutabledict` for config/utility objects.

For smoke checks that do not launch training, run the bundled helpers:

```bash
python scripts/inspect_scenic_package.py
python scripts/run_scenic_smoke.py
```

`run_scenic_smoke.py` checks imports, JAX tiny CPU math, LR schedules, and registry names. It does not run repository tests, download datasets, or start training.

## Backend selection

Scenic is designed for large-scale multi-device and multi-host research, but many API/config checks work on CPU. Treat backends as follows:

| Task | Backend requirement | Notes |
|---|---|---|
| Config inspection, registry lookup, LR schedule/optimizer construction, small model/layer API checks | CPU is sufficient | Use smoke helpers first. |
| Real training or evaluation on ImageNet, COCO, video, audio, multimodal, or large project data | GPU/TPU usually required for practical runtime | Also requires dataset access, checkpoint paths, and project-specific dependencies. |
| JAX GPU execution | CUDA/ROCm/MPS-specific JAX/JAXLIB build | A visible GPU is not enough; `jax.devices()` must show the accelerator. |
| TensorFlow input pipelines on GPU hosts | Usually hide TensorFlow GPUs before JAX training | `scenic.app` hides TensorFlow GPU devices to avoid TF reserving memory needed by JAX. |

If a smoke helper reports that JAX falls back to CPU while a GPU exists, that is acceptable for config/API checks but not proof of accelerator training readiness.

## Optional project dependency groups

Do not install every project requirement file by default. Select the group tied to the project or baseline:

- Video/multimodal projects (`vivit`, `mtv`, `polyvit`, `objectvivit`, `mbt`) commonly need `dmvr` and sometimes `seaborn` or project-specific data pipelines.
- Text/video captioning projects (`vid2seq`, `streaming_dvc`) can require `dmvr`, `t5`, `t5x`, `gin-config`, and caption-eval packages.
- Detection/captioning projects (`detr`, `deformable_detr`, `centernet`, `densevoc`, `pixel_llm`, `owl_vit`) can require `pycocotools`, `pycocoevalcap`, COCO/LVIS APIs, CLIP/Torch, or old CUDA/JAX pins.
- Transfer/pretraining and BigTransfer paths can require `big_vision` source access and TensorFlow Addons. TensorFlow Addons 0.23 is not compatible with modern TensorFlow/Keras 3 stacks; pin TensorFlow/Keras/TFA together if that path is required.
- Some historical requirement files pin old JAX/TensorFlow versions. Use a separate project-specific environment rather than downgrading a working core environment unless the selected workflow requires it.

## Safe setup sequence

1. Create an isolated environment with a Python version supported by the selected Scenic checkout.
2. Install core Scenic first and run `scripts/inspect_scenic_package.py`.
3. Pick one project/baseline and read `sub-skills/baselines-and-projects/references/optional-dependencies.md` before installing its requirements.
4. For full training, verify JAX sees the intended backend and that dataset/checkpoint locations are accessible.
5. Run a no-training config preflight with `sub-skills/running-and-training/scripts/scenic_config_probe.py` before launching expensive work.
