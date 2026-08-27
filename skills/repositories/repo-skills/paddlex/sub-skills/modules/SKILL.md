---
name: modules
description: "Use PaddleX module-level APIs and config-driven custom development
  for create_model, dataset checking, training, evaluation, export, prediction,
  pdparams2safetensors, and distributed training."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# PaddleX modules

Use this sub-skill when the user is working with **single-model or custom-development workflows** rather than a ready-made pipeline. Typical requests mention `create_model`, a module config YAML, dataset checking, training, evaluation, export, prediction, `pdparams2safetensors`, checkpoints, or distributed training.

Route away from this sub-skill when the task is:

- quick pre-trained pipeline inference or pipeline config export — use `../pipelines/`.
- high-performance inference, serving, Paddle2ONNX, GenAI server/client setup, or deployment plugin installation — use `../deployment/`.

## Start here

1. Determine the module family and model name: e.g. image classification, object detection, OCR text recognition, table structure recognition, time-series forecasting, speech recognition, video classification, or document VLM.
2. Decide whether the user wants API-level prediction (`create_model`) or config-driven development (`check_dataset`, `train`, `evaluate`, `export`, `predict`, `pdparams2safetensors`).
3. Before training, run dataset checking and fix data-format issues.
4. Treat official pretrained weights, local inference model directories, and training checkpoints as different objects.

Read `references/module-overview.md` for workflow order and config patterns. Read `references/data-formats.md` for dataset-family notes. Read `references/module-troubleshooting.md` when config, data, dependency, checkpoint, or distributed-training issues appear.

## Minimal model API pattern

```python
from paddlex import create_model

model = create_model("PP-LCNet_x1_0", model_dir="optional/inference/model")
for result in model.predict("demo.jpg", batch_size=1):
    result.print()
```

Verified installed signature for PaddleX 3.7.2:

```text
create_model(model_name, model_dir=None, *args, **kwargs)
```

`model_name` selects a supported PaddleX module model. `model_dir` is for a local model directory; omit it when using official/pretrained resolution if the environment can download the model.

## Config-driven workflow

PaddleX module work is typically driven by YAML configs and `Global.mode`-like modes. Use the bundled helper to keep the module-engine path self-contained:

```bash
python scripts/run_module_smoke.py --config module_config.yaml --mode check_dataset --override Dataset.dataset_dir=./data
python scripts/run_module_smoke.py --config module_config.yaml --mode train --override Global.output=./output
python scripts/run_module_smoke.py --config module_config.yaml --mode evaluate --override Evaluate.model_dir=./output/best_model
python scripts/run_module_smoke.py --config module_config.yaml --mode export --override Export.weight_path=./output/best_model/model.pdparams
python scripts/run_module_smoke.py --config module_config.yaml --mode predict --override Predict.model_dir=./output/inference
```

The installed package also exposes builders for advanced programmatic use:

```text
build_dataset_checker(config: paddlex.utils.config.AttrDict) -> BaseDatasetChecker
build_exportor(config: paddlex.utils.config.AttrDict) -> BaseExportor
build_trainer(config: paddlex.utils.config.AttrDict) -> BaseTrainer
build_evaluator(config: paddlex.utils.config.AttrDict) -> BaseEvaluator
build_weight_converter(config: paddlex.utils.config.AttrDict) -> WeightConverter
```

## Bundled helper

Use `scripts/run_module_smoke.py` for safe checks and delegated module-engine commands. Use `scripts/inspect_module_api.py --help` when you only need a signature probe.

```bash
python scripts/run_module_smoke.py --dry-run
python scripts/run_module_smoke.py --show-engine-modes
python scripts/run_module_smoke.py --config module_config.yaml --mode check_dataset --override Dataset.dataset_dir=./data
```

The helpers do not depend on the original checkout. Real training/evaluation/export commands can be long-running and may download weights, so only run them when the user has supplied data, runtime budget, and a prepared backend.

## High-value checks before answering a user

- Is the YAML a module config rather than a pipeline config?
- Has `check_dataset` passed for the selected module family?
- Is the requested model listed in the module family or support list?
- Does the environment include the extra dependencies for that family (`cv`, `ocr`, `ts`, `speech`, `video`, `multimodal`, or deployment plugins)?
- Is the user trying to deploy/export an already trained model? Route deployment-specific backends to `../deployment/` after the module export step.
