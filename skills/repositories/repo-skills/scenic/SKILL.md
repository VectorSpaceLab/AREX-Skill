---
name: scenic
description: "Use Scenic, Google Research's JAX/Flax computer-vision research
  codebase, for configs, training, datasets, models, layers, baselines, and
  project-specific workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Scenic Repo Skill

Use this skill when a task is about **Scenic** (`google-research/scenic`): JAX/Flax vision research experiments, Scenic config files, app/training runners, dataset registry errors, BaseModel/layer APIs, or choosing/adapting a Scenic baseline or project.

Scenic is both a lightweight shared library (`common_lib`, `dataset_lib`, `model_lib`, `train_lib`) and a large project zoo under `scenic.projects`. It favors project-level forking/copying for research code and keeps reusable patterns in the shared libraries.

## Start here

1. If setting up an environment or checking whether Scenic imports, read [references/installation-and-environment.md](references/installation-and-environment.md) and run [scripts/inspect_scenic_package.py](scripts/inspect_scenic_package.py).
2. If the task names `--config`, `--workdir`, `rng_seed`, `trainer_name`, `model_name`, `dataset_name`, LR schedules, optimizers, checkpoints, or train launches, use [sub-skills/running-and-training/SKILL.md](sub-skills/running-and-training/SKILL.md).
3. If the task is about dataset registration, TFDS, FlexIO, COCO/TFRecord layouts, `DatasetRegistry`, `@add_dataset`, or unknown dataset errors, use [sub-skills/data-pipelines/SKILL.md](sub-skills/data-pipelines/SKILL.md).
4. If the task is about BaseModel contracts, registered model names, Flax modules, attention/layers, matchers, losses, metrics, or tiny model checks, use [sub-skills/modeling-and-layers/SKILL.md](sub-skills/modeling-and-layers/SKILL.md).
5. If the task asks which Scenic baseline/project to use, how a project-specific `main.py`/config/registry works, or which optional dependencies a project needs, use [sub-skills/baselines-and-projects/SKILL.md](sub-skills/baselines-and-projects/SKILL.md).

## Safe core checks

Run these from any environment where Scenic is installed:

```bash
python scripts/inspect_scenic_package.py
python scripts/run_scenic_smoke.py
```

The smoke helper is self-contained: it imports safe modules, checks a tiny JAX calculation, validates LR schedule construction, and lists dataset/model registry names. It does **not** run training, load datasets, download checkpoints, or execute original repository tests.

For optional trainer-registry import diagnostics:

```bash
python scripts/inspect_scenic_package.py --check-trainers
python scripts/run_scenic_smoke.py --check-trainers
```

A trainer import failure can be an optional transfer/BigTransfer/TensorFlow Addons dependency issue rather than a core package failure. Read [references/troubleshooting.md](references/troubleshooting.md) and the `running-and-training` troubleshooting reference before changing package versions.

## Route by user intent

| User intent or signal | Read next |
|---|---|
| "How do I run this config?", `--config`, `--workdir`, `dataset_service_address`, JAX backend flags | `running-and-training` |
| Validate a config without launching a job | `running-and-training` and its `scripts/scenic_config_probe.py` |
| `Unknown dataset`, custom dataset registration, TFDS/FlexIO/COCO/TFRecord data layout | `data-pipelines` |
| `Unrecognized model`, model registry names, BaseModel, metrics/losses, matchers/layers | `modeling-and-layers` |
| Choose ViT/ResNet/DETR/CLIP/BERT/ViViT/MTV/OWL-ViT/UnLoc/Vid2Seq/DenseVOC/PixelLLM/etc. | `baselines-and-projects` |
| Optional dependencies such as DMVR, T5/T5X, CLIP/Torch, COCO/LVIS, pycocotools, TensorFlow Addons, BigVision | `baselines-and-projects` plus root troubleshooting |
| Shared image/video/debug/export helpers | [references/common-utilities.md](references/common-utilities.md) |
| Check whether this generated skill is stale for a checkout | [references/repo-provenance.md](references/repo-provenance.md) |

## Operating rules

- Do not launch full training/evaluation until config, dataset availability, checkpoint paths, backend devices, and project dependencies are all known.
- Treat CPU smoke checks as validation for API/config guidance only. They do not prove GPU/TPU performance or multi-host correctness.
- Do not install every project `requirements.txt`. Pick the project/baseline first, then install the narrow optional dependency set it needs.
- Do not run data-conversion tools unless input data, output paths, credentials, side effects, and dependencies are explicitly approved.
- For project-specific models/trainers/datasets, prefer the project `main.py` and project registry pattern instead of assuming the root `scenic.main` registry knows every project object.
- Keep source-code modification and contribution-policy tasks separate from user-facing Scenic experiment use; if the user is editing Scenic itself, verify with focused tests and current project instructions.

## Provenance and routing metadata

- Read [references/repo-provenance.md](references/repo-provenance.md) before refreshing or trusting this skill for a different Scenic checkout.
- [references/repo-routing-metadata.json](references/repo-routing-metadata.json) is the structured router metadata used by the managed repo-skill importer when import is explicitly requested in a later run.
