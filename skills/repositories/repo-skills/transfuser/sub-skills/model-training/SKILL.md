---
name: model-training
description: "Guides TransFuser imitation-model training, dataset and
  configuration validation, backbone and PointPillars selection, single-GPU or
  torchrun DDP launch, loss interpretation, and checkpoint recovery."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# TransFuser Model Training

Use this sub-skill when a task involves training or resuming a TransFuser-family model, choosing a fusion backbone, validating training data, preparing a single-GPU or DDP command, interpreting losses and logs, or diagnosing a checkpoint.

## Non-negotiable runtime boundary

- Training requires an NVIDIA CUDA runtime. The repository training path unconditionally selects a CUDA device; there is **no CPU training substitute**.
- Preserve the legacy package family unless deliberately porting and revalidating it: Python 3.7, PyTorch 1.12.1+cu113, `mmcv-full` 1.6.0, `mmdet` 2.25.0, `mmsegmentation` 0.25.0, `mmcls` 0.25.0, `torch-scatter` 2.1.0, and `timm` 0.6.7. This combination passed imports and `pip check` with CUDA visible on an NVIDIA A100 during skill construction.
- Do not treat a successful CPU import, `pip check`, or CLI parser run as proof that training works. Require `torch.cuda.is_available()`, a CUDA allocation, and matching compiled extensions.
- Model construction can ask `timm` for pretrained image weights. Prepare an approved local cache or explicitly authorize network access before constructing a fresh model in a network-restricted environment.

## Route the task

1. **Prepare a new or resumed run:** read [training-workflow.md](references/training-workflow.md). It contains every `train.py` flag/default, single-GPU and `torchrun` recipes, logging, losses, caching, debug behavior, and resume semantics.
2. **Validate data or diagnose a shape/key failure:** read [data-format.md](references/data-format.md), then run [validate_training_setup.py](scripts/validate_training_setup.py). The helper only inspects paths, metadata, environment variables, and optional imports; it never trains or downloads.
3. **Choose a backbone, architecture, config override, or PointPillars:** read [api-reference.md](references/api-reference.md). It covers `GlobalConfig`, `CARLA_Data`, `LidarCenterNet`, all four fusion backbones, tensor contracts, and the PointPillars path.
4. **Resume, compare, or diagnose weights:** first read the checkpoint section in [training-workflow.md](references/training-workflow.md), then run [inspect_checkpoint.py](scripts/inspect_checkpoint.py). Its default mode does not unpickle the checkpoint; only use `--unsafe-load` for a trusted file.
5. **Recover from a failure:** read [troubleshooting.md](references/troubleshooting.md) for missing paths, DDP rank variables, invalid backbones, checkpoint incompatibility, cache/debug failures, and missing OpenMMLab or `torch-scatter` components.

## Safe first pass

From any directory, validate the intended run before launching it:

```bash
python <this-sub-skill>/scripts/validate_training_setup.py \
  --repo-root <transfuser-checkout> \
  --dataset-root <dataset-root> \
  --setting 02_05_withheld \
  --backbone transFuser \
  --parallel-training 0
```

Add `--check-runtime` only in the environment intended for training. It imports the compatibility stack and repository training modules and requires working CUDA, but it does not instantiate a model or start training.

## Boundaries and handoffs

- Dataset acquisition, CARLA route/scenario generation, and 210-GB collection are owned by [data-and-routes](../data-and-routes/SKILL.md).
- Loading a trained model into `HybridAgent`, handling `args.txt` at inference time, and CARLA control are owned by [sensor-agent](../sensor-agent/SKILL.md).
- Longest6 execution and result parsing are owned by [carla-evaluation](../carla-evaluation/SKILL.md).
- Full training, model-weight downloads, CARLA simulation, Docker builds, and cloud submission are intentionally not performed by bundled helpers.

## Completion criteria

Before launching training, require all of the following:

- the dataset split selects at least one train route and, for `02_05_withheld`, at least one withheld validation route;
- required modality files and future labels exist for eligible samples;
- the exact backbone string and architecture choices are compatible;
- CUDA and compiled dependency probes pass;
- single-GPU runs set `--parallel_training 0`, while DDP runs are launched by `torchrun` with `RANK`, `LOCAL_RANK`, and `WORLD_SIZE` populated;
- resume runs have both `model_<epoch>.pth` and the derived `optimizer_<epoch>.pth`, a deliberate `--start_epoch`, and matching architecture/config provenance;
- the output resolves to `<logdir>/<id>` and has sufficient storage for checkpoints, TensorBoard events, optional visualizations, and any disk cache.
