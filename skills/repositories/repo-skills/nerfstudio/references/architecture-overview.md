# Nerfstudio operating map

Read this reference when the task spans more than one route.

## Core object flow

1. A capture or existing dataset is converted to the Nerfstudio format, normally a directory containing images plus `transforms.json`.
2. A dataparser config produces camera poses, intrinsics, image/depth/mask paths, and train/eval splits.
3. A method config combines a datamanager, pipeline, model/field, optimizers, schedulers, and viewer/logging settings.
4. `ns-train <method> ... <dataparser> ...` writes a timestamped run directory containing `config.yml` and checkpoints.
5. A saved `config.yml` is the handoff for `ns-viewer`, `ns-eval`, `ns-render`, and `ns-export`.

Use the focused route for each stage: [data-preparation](../sub-skills/data-preparation/SKILL.md), [training-and-configs](../sub-skills/training-and-configs/SKILL.md), and [visualization-and-export](../sub-skills/visualization-and-export/SKILL.md).

## Public package surfaces

- `nerfstudio.configs.method_configs.method_configs`: built-in training method configurations.
- `nerfstudio.configs.dataparser_configs.dataparsers`: built-in dataparser configurations.
- `nerfstudio.engine.trainer.TrainerConfig`: top-level training configuration.
- `nerfstudio.pipelines.base_pipeline.VanillaPipeline` and pipeline configs: connect data managers to models.
- `nerfstudio.models.*`: model/config pairs such as Nerfacto, Splatfacto, Instant-NGP, Vanilla NeRF, NeuS, and TensoRF.
- `nerfstudio.data.dataparsers.*`: dataset-specific parser implementations.
- `nerfstudio.plugins.*`: method and dataparser registration for external packages.
- `nerfstudio.utils.eval_utils.eval_setup`: checkpoint/config loading used by viewer, evaluation, render, and export commands.

## Backend boundary

CUDA is the production path for fast training, rendering, and Gaussian Splatting. The package includes torch implementations/fallbacks that make reduced CPU checks useful for config, parser, plugin, and tiny training behavior, but a CPU check does not validate production GPU throughput or CUDA extensions. `gsplat` and `nerfacc` are runtime dependencies for selected methods; tiny-cuda-nn is an optional acceleration path and may be absent when the torch implementation is explicitly selected.

## Output handoff

Prefer passing the exact `config.yml` from a completed run to downstream commands. Do not guess a checkpoint or copy only a model directory: the config carries method, dataparser, dataset, pipeline, and viewer settings needed to reconstruct the pipeline.
