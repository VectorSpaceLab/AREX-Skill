---
name: raster-vision
description: "Routes Raster Vision geospatial computer vision tasks involving
  rastervision CLI pipelines, GeoTIFF/GeoJSON data configs, PyTorch chip
  classification, semantic segmentation, object detection, model bundles, AWS
  runners, Docker, and S3/GDAL filesystems."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Raster Vision

Use this repo skill when a task involves Raster Vision as a library or low-code framework for deep learning on satellite, aerial, or other large geospatial imagery.

## When to use

Read this skill for requests about:

- `rastervision run`, `run_command`, `predict`, or `predict_scene`
- `ClassConfig`, `SceneConfig`, `DatasetConfig`, `RasterioSourceConfig`, `GeoJSONVectorSourceConfig`, label sources/stores, AOIs, analyzers, evaluators, or model bundles
- PyTorch-backed chip classification, semantic segmentation, object detection, GeoDataset, Learner, backbones, solvers, and task examples
- Docker, AWS Batch, AWS SageMaker, S3, requester-pays/unsigned S3, optional GDAL VSI, CloudFormation, or remote Raster Vision job setup
- troubleshooting geospatial data, config validation, backend selection, and model-bundle prediction failures

Do not use this skill for generic computer vision frameworks unless Raster Vision's geospatial pipeline/config/file-system layer is part of the task.

## Install and smoke check

Typical release install:

```bash
pip install rastervision
```

For realistic GPU training or geospatial dependency parity, prefer a Raster Vision PyTorch Docker image. After installation, run the bundled checker:

```bash
python scripts/check_rastervision_install.py
```

Read [installation and package map](references/installation-and-package-map.md) for package splits, optional plugins, GPU notes, and configuration locations. Read [repository provenance](references/repo-provenance.md) before deciding whether this skill is stale for a checkout.

## Route map

| Task | Read |
| --- | --- |
| CLI syntax, config modules, runners, `--arg`, `--splits`, `run_command`, `predict`, `predict_scene`, or model-bundle CLI prediction | [pipeline-cli](sub-skills/pipeline-cli/SKILL.md) |
| Programmatic geospatial APIs: scenes, class configs, raster/vector sources, label sources/stores, AOIs, GeoDataset, Learner, Predictor, ScenePredictor | [data-and-models](sub-skills/data-and-models/SKILL.md) |
| PyTorch chip classification, semantic segmentation, object detection, example recipes, task backends, solvers, backbones, model zoo, transfer learning | [pytorch-workflows](sub-skills/pytorch-workflows/SKILL.md) |
| Docker, AWS Batch, AWS SageMaker, S3, requester-pays/unsigned S3, GDAL VSI, CloudFormation templates, bootstrap setup | [cloud-and-filesystems](sub-skills/cloud-and-filesystems/SKILL.md) |

## Core concepts

Raster Vision can be used in two modes:

1. **Library mode**: assemble geospatial data sources, labels, PyTorch datasets, learners, predictors, and label stores directly in Python.
2. **Framework mode**: write a Python config module with `get_config(runner, **kwargs)` or `get_configs(...)`, then run the pipeline with the `rastervision` CLI.

Standard pipeline stages are `analyze`, `chip`, `train`, `predict`, `eval`, and `bundle`. The final bundle contains model weights plus config needed for later prediction on new imagery.

## Decision checklist

Before giving operational guidance, identify:

- Task family: chip classification, semantic segmentation, object detection, direct library API use, or cloud execution.
- Data form: raw geospatial scenes, AOI-delimited scenes, prechipped image data, model bundle, or remote URI set.
- Execution mode: `inprocess` for debugging, `local` for host Makefile execution, `batch` for AWS Batch, or `sagemaker` for SageMaker.
- Backend needs: CPU inspection/smoke, CUDA throughput, Docker parity, AWS credentials, S3 access, or optional GDAL VSI.
- Output expectations: `train/`, `predict/`, `eval/`, `bundle/model-bundle.zip`, GeoTIFF labels, vector outputs, or JSON metrics.

## Bundled helpers

- [scripts/check_rastervision_install.py](scripts/check_rastervision_install.py): verify required package imports, CLI help, optional plugins, and torch CUDA visibility without training or submitting cloud jobs.
- [pipeline config summarizer](sub-skills/pipeline-cli/scripts/summarize_pipeline_config.py): inspect a config module or JSON without executing pipeline commands.
- [scene config checker](sub-skills/data-and-models/scripts/check_scene_config.py): validate or minimally build a serialized `SceneConfig`.
- [example command printer](sub-skills/pytorch-workflows/scripts/list_example_commands.py): render safe example commands without running them.
- [Docker command renderer](sub-skills/cloud-and-filesystems/scripts/render_docker_run_command.py): render a `docker run` command without executing Docker.

## Troubleshooting entry points

Start with [cross-cutting troubleshooting](references/troubleshooting.md), then drill into the nearest sub-skill:

- CLI/config failures: `pipeline-cli/references/troubleshooting.md`
- data/label/model API failures: `data-and-models/references/troubleshooting.md`
- PyTorch/example/backend failures: `pytorch-workflows/references/troubleshooting.md`
- Docker/AWS/S3/GDAL failures: `cloud-and-filesystems/references/troubleshooting.md`

## Safety boundaries

- Do not run full training, download external datasets, submit AWS jobs, or create CloudFormation stacks unless the user explicitly approves cost, time, credentials, and write targets.
- Prefer helpers that render or validate commands before executing them.
- Keep remote-run data in S3 or another remote filesystem; AWS Batch and SageMaker jobs cannot read arbitrary local paths.
- When GPU behavior matters, verify PyTorch CUDA visibility instead of assuming GPU support from hardware alone.
