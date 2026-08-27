---
name: automl-and-hyperopt
description: "Guides agents using Ludwig AutoML, init_config, hyperopt search
  spaces, Ray or Optuna executors, and tuning dependency troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# AutoML and Hyperopt

Use this sub-skill when the task asks for Ludwig AutoML, `init_config`, `auto_train`, `create_auto_config`, `ludwig hyperopt`, search spaces, executors, Ray/Optuna dependencies, or tuning failures.

## Start here

1. Validate the base dataset/config through [configuration-and-data](../configuration-and-data/SKILL.md).
2. Read [workflows.md](references/workflows.md) for AutoML and HPO patterns.
3. Read [api-reference.md](references/api-reference.md) for API/CLI surfaces.
4. Check prerequisites before running a search:

```bash
python scripts/check_hyperopt_prereqs.py
ludwig hyperopt --help
```

## Key decision points

- `init_config` helps infer a starting config from a dataset and target.
- `auto_train` can create and train an AutoML-selected config within a time budget.
- `hyperopt` requires a config with a `hyperopt` section and an executor/search algorithm.
- Ray and Optuna paths are optional; missing imports should produce dependency guidance, not silent fallback.

## Route elsewhere

- Ordinary one-run training: [training-and-experiments](../training-and-experiments/SKILL.md).
- Serving/export of tuned models: [serving-export-and-deployment](../serving-export-and-deployment/SKILL.md).
