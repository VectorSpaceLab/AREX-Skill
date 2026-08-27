---
name: paddlex
description: "Operate PaddleX 3.7.2 for low-code AI pipelines, module custom
  development, deployment, installation, and troubleshooting."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# PaddleX operating skill

Use this skill when a task involves **PaddleX**, the PaddlePaddle low-code toolkit for pre-trained pipelines, model/module development, and deployment.

This skill is self-contained. Do not rely on the original PaddleX repository checkout while using it; use the bundled references and scripts here.

## Route by user intent

| User intent | Read |
| --- | --- |
| install PaddleX, verify imports, choose extras, or fix package setup | `references/installation.md`, `references/troubleshooting.md`, `scripts/check_paddlex_install.py` |
| run a ready-made AI pipeline through Python or CLI | `sub-skills/pipelines/` |
| export/get/edit a pipeline config, set devices/engines, save pipeline outputs | `sub-skills/pipelines/` |
| use `create_model`, validate a dataset, train, evaluate, export, predict, or convert module weights | `sub-skills/modules/` |
| deploy or accelerate a pipeline/model with HPI, serving, Paddle2ONNX, GenAI client/server, or hardware-specific runtimes | `sub-skills/deployment/` |
| decide whether this skill is stale for a new checkout | `references/repo-provenance.md` |

## Core public entry points

Installed PaddleX 3.7.2 exports these high-value APIs:

```python
from paddlex import create_pipeline, create_predictor, create_model
from paddlex import build_dataset_checker, build_trainer, build_evaluator
```

Verified signatures during construction:

```text
create_pipeline(pipeline=None, *, config=None, device=None, engine=None,
                engine_config=None, pp_option=None, use_hpip=None,
                hpi_config=None, **kwargs)
create_predictor(model_name, *, model_dir=None, device=None, engine=None,
                 engine_config=None, batch_size=1, pp_option=None,
                 use_hpip=False, hpi_config=None, genai_config=None, **kwargs)
create_model(model_name, model_dir=None, *args, **kwargs)
```

Installed CLI entry points:

```bash
paddlex --help
paddlex --pipeline image_classification --input demo.jpg --save_path output --device cpu
paddlex --get_pipeline_config image_classification
paddlex --serve --pipeline image_classification --host 0.0.0.0 --port 8080
paddlex --paddle2onnx --paddle_model_dir ./inference_model --onnx_model_dir ./onnx
paddlex_genai_server --help
```

## Baseline install check

After installing PaddlePaddle and PaddleX, run:

```bash
python scripts/check_paddlex_install.py
```

A healthy baseline shows PaddleX importable, a PaddlePaddle version, CLI entry points, and whether Paddle is CPU-only or GPU-enabled.

## Common decision rules

- Use **pipelines** for pre-trained pipeline inference and pipeline YAML orchestration.
- Use **modules** for custom datasets, model configs, training/evaluation/export, and `create_model`.
- Use **deployment** only after the user asks for serving, acceleration, conversion, GenAI hosting, or hardware packaging.
- CPU import success is not proof of GPU/HPI/accelerator readiness. Verify the specific PaddlePaddle wheel, plugin, and backend.
- Avoid full training, model downloads, server starts, or plugin installs until the user supplies data, runtime budget, and backend constraints.

## Bundled references

- `references/installation.md` — install order, extras, PaddlePaddle wheel choice, plugins.
- `references/troubleshooting.md` — cross-cutting package/CLI/data/backend problems.
- `references/pipeline-catalog.md` — root summary of pipeline capabilities.
- `references/module-overview.md` — root summary of module capabilities.
- `references/deployment-overview.md` — root summary of deployment capabilities.
- `references/repo-provenance.md` — source commit/evidence/staleness information.
- `references/repo-routing-metadata.json` — router metadata for managed import.
