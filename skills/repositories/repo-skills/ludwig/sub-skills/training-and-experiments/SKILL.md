---
name: training-and-experiments
description: "Guides agents running Ludwig train, experiment, check_install,
  Python LudwigModel training, and multimodal or LLM training workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Training and Experiments

Use this sub-skill when the task is to train or fine-tune a Ludwig model, run a full experiment, use `LudwigModel.train`, resume from checkpoints, understand training artifacts, or plan LLM/VLM/multimodal training.

## Recommended path

1. Make or validate a config and dataset first via [configuration-and-data](../configuration-and-data/SKILL.md).
2. Read [workflows.md](references/workflows.md) for CLI and Python recipes.
3. Read [api-reference.md](references/api-reference.md) when embedding Ludwig in Python.
4. If the task involves LLM, VLM, LoRA/QLoRA, DPO/KTO/ORPO/GRPO, quantization, or large pretrained models, read [llm-and-multimodal.md](references/llm-and-multimodal.md) before running anything.
5. For a safe local fixture:

```bash
python scripts/make_tiny_tabular_project.py --output-dir /tmp/ludwig-train-smoke
python scripts/check_ludwig_install.py --project-dir /tmp/ludwig-train-smoke --dry-run
```

Use `--run-tiny-train` only when the user approves a short training smoke.

## Common commands

```bash
ludwig train --config config.yaml --dataset dataset.csv --output_directory results
ludwig experiment --config config.yaml --dataset dataset.csv --output_directory results
ludwig check_install --help
```

## Decision points

- `train` trains and saves artifacts; `experiment` trains and evaluates against a split.
- Use `--model_resume_path` to resume if a previous run wrote checkpoints.
- Use `--backend local` unless Dask/Ray is explicitly needed.
- Use explicit `--gpus` only after checking CUDA and memory.
- Skip save/log artifacts for smoke tests; keep them for real experiments.

## Route onward

- Prediction/evaluation/forecast after training: [prediction-evaluation-and-inspection](../prediction-evaluation-and-inspection/SKILL.md).
- Hyperparameter search and AutoML: [automl-and-hyperopt](../automl-and-hyperopt/SKILL.md).
- Serving/export/upload: [serving-export-and-deployment](../serving-export-and-deployment/SKILL.md).
