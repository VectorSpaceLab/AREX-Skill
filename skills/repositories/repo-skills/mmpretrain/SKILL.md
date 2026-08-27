---
name: mmpretrain
description: "Operate MMPreTrain model-zoo inference, config-driven training and
  evaluation, dataset/customization, analysis utilities, checkpoint conversion,
  and serving workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# MMPreTrain repo skill

Use this skill when a task involves MMPreTrain / OpenMMLab Model Pretraining Toolbox as a package or framework: model-zoo discovery, inference, feature extraction, config-driven training/testing, dataset preparation, registry customization, analysis tools, checkpoint conversion, or serving packaging.

## First checks

- Read `references/package-overview.md` for the package surfaces and optional capability map.
- Read `references/installation-and-troubleshooting.md` when installation, import, ModelHub, optional dependencies, or backend readiness are uncertain.
- Run `scripts/check_mmpretrain_env.py` for a no-download package smoke check before relying on model-zoo APIs or backend-specific behavior.
- Read `references/repo-provenance.md` before deciding whether this skill is stale for a different checkout or package version.

## Route by task

| User task | Read |
| --- | --- |
| List available models, choose a checkpoint policy, use `get_model`, run image classification, retrieval, captioning, VQA, visual grounding, NLVR, or extract features | `sub-skills/model-zoo-inference/SKILL.md` |
| Inspect or modify configs, plan `mim train mmpretrain` / `mim test mmpretrain`, choose CPU/GPU/distributed/Slurm launch, use resume/AMP/auto-scale-lr/TTA/output dumps, or plan K-fold | `sub-skills/training-and-evaluation/SKILL.md` |
| Prepare `CustomDataset`, ImageNet, or OpenMMLab 2.0 annotations; inspect dataloader fields; build transform pipelines; register custom datasets/models/metrics/hooks/optimizers | `sub-skills/datasets-and-customization/SKILL.md` |
| Analyze JSON logs/results, compute metrics/confusion matrices/FLOPs, visualize CAM/t-SNE/schedulers/datasets, publish/convert checkpoints, reparameterize, or package TorchServe artifacts | `sub-skills/tools-analysis-and-deployment/SKILL.md` |

## Install baseline

Typical package install:

```bash
pip install -U openmim
mim install "mmpretrain>=1.0.0rc8"
```

Development/package-tool install:

```bash
pip install -U openmim
mim install -e .
```

Multi-modal workflows need the optional dependency group:

```bash
mim install "mmpretrain[multimodal]>=1.0.0rc8"
```

MMPreTrain expects Python 3.7+, PyTorch 1.8+, `mmcv>=2.0.0,<2.4.0`, and `mmengine>=0.8.3,<1.0.0`. Select a CUDA-capable PyTorch/MMCV build only when the task requires GPU or distributed behavior.

## Safe operating defaults

1. For offline or architecture-only model work, use `get_model(..., pretrained=False)` or inferencer `pretrained=False`; inferencer classes otherwise try default weights.
2. For CPU-only train/test planning, use MIM package commands with `--gpus 0` and/or `CUDA_VISIBLE_DEVICES=-1`.
3. Inspect a merged config and dataset fields before long runs; route config work to `training-and-evaluation` and dataset schema work to `datasets-and-customization`.
4. Treat checkpoint downloads, dataset downloads, TorchServe startup, Slurm jobs, and GPU training as resource-requiring actions. Confirm resources before launching them.
5. Use bundled helpers and references here; do not depend on the original repository checkout being present.

## Common failure routing

- `File ... .mim/model-index.yml does not exist`, incompatible `mmcv` / `mmengine`, NumPy ABI warnings, or CUDA backend mismatch: `references/installation-and-troubleshooting.md`.
- Invalid model name, checkpoint download/cache error, device mismatch, or missing multimodal extras during inference: `sub-skills/model-zoo-inference/references/troubleshooting.md`.
- Bad `_base_` inheritance, `--cfg-options` quoting, `load_from` versus `resume`, AMP/TTA, or distributed launch hangs: `sub-skills/training-and-evaluation/references/troubleshooting.md`.
- Bad annotation paths/labels, missing `LoadImageFromFile`, unreadable images, or registry `KeyError`: `sub-skills/datasets-and-customization/references/troubleshooting.md`.
- Plotting/headless errors, optional Grad-CAM/t-SNE deps, checkpoint format mismatch, EMA publishing, or TorchServe service errors: `sub-skills/tools-analysis-and-deployment/references/troubleshooting.md`.
