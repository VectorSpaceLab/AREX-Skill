---
name: configuration-and-data
description: "Helps agents create, validate, render, and troubleshoot Ludwig
  configs, schemas, feature declarations, datasets, and preprocessing inputs."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Configuration and Data

Use this sub-skill when the task is about Ludwig YAML/config dictionaries, feature declarations, schema export, preprocessing, synthetic data, data formats, config generation, or dataset-column troubleshooting.

## Start here

1. Identify the target workflow: config authoring, config validation/rendering, data preparation, synthetic fixture creation, or LLM-backed config generation.
2. Read [configuration.md](references/configuration.md) for config sections and feature/model-type choices.
3. Read [data-formats.md](references/data-formats.md) for dataset layouts and split-column guidance.
4. For a local fixture, run:

```bash
python scripts/make_tiny_dataset.py --output-dir /tmp/ludwig-tiny
python scripts/validate_ludwig_config.py /tmp/ludwig-tiny/config.yaml
```

5. If validation fails, use [troubleshooting.md](references/troubleshooting.md) before moving to training.

## Commands and APIs

- CLI: `ludwig generate_config`, `ludwig init_config`, `ludwig render_config`, `ludwig export_schema`, `ludwig preprocess`, `ludwig synthesize_dataset`.
- Python: `ludwig.config_generation.generate_config`, `ludwig.config_generation.get_ludwig_schema_context`, `ludwig.automl.init_config`, `LudwigModel.preprocess`.
- Config sections: `model_type`, `input_features`, `output_features`, `combiner`, `trainer`, `backend`, `preprocessing`, `hyperopt`, `adapter`, `quantization`, `prompt`.

## Route onward

- After config/data validation, route training to [training-and-experiments](../training-and-experiments/SKILL.md).
- Route HPO/AutoML search-space work to [automl-and-hyperopt](../automl-and-hyperopt/SKILL.md).
- Route prediction-data fixture work to [prediction-evaluation-and-inspection](../prediction-evaluation-and-inspection/SKILL.md).
- Route serving payload construction to [serving-export-and-deployment](../serving-export-and-deployment/SKILL.md).

## Safety notes

- `generate_config` uses external LLM providers unless mocked or run only with `--help`; verify API keys before real calls.
- Dataset-zoo and Kaggle/Hugging Face flows can use network and cache. Prefer local CSV/Parquet fixtures for smoke checks.
- `preprocess` writes processed data/metadata; choose an explicit scratch output path when applicable.
