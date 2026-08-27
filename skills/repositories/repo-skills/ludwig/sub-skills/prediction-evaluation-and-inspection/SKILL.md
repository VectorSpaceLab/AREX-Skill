---
name: prediction-evaluation-and-inspection
description: "Guides agents using Ludwig model loading, prediction, evaluation,
  forecasting, generation, visualization, and model inspection workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Prediction, Evaluation, and Inspection

Use this sub-skill when the task starts from a trained Ludwig model or asks for prediction, evaluation, forecasting, generation, model inspection, weights/activations collection, or output interpretation.

## Workflow

1. Confirm the model directory has saved weights, hyperparameters/config, and training-set metadata.
2. Confirm the dataset has input columns for prediction and output columns for evaluation.
3. Read [workflows.md](references/workflows.md) for CLI and Python recipes.
4. Read [api-reference.md](references/api-reference.md) for signatures and return shapes.
5. Use the bundled fixture/script for safe data shape work:

```bash
python scripts/build_prediction_dataset.py --output /tmp/ludwig-predict.csv
python scripts/inspect_model_artifact.py --model-dir results/experiment_run/model
```

## Command routes

- `ludwig predict --model_path MODEL --dataset DATA --output_directory OUT`
- `ludwig evaluate --model_path MODEL --dataset DATA --output_directory OUT`
- `ludwig forecast --model_path MODEL --dataset DATA --horizon N`
- `ludwig inspect --model_path MODEL --json`
- `ludwig collect_summary`, `collect_weights`, `collect_activations`

## Route elsewhere

- Need to train or resume a model first: [training-and-experiments](../training-and-experiments/SKILL.md).
- Need to create/validate the config or dataset: [configuration-and-data](../configuration-and-data/SKILL.md).
- Need a long-running REST endpoint: [serving-export-and-deployment](../serving-export-and-deployment/SKILL.md).
