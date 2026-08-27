# AutoML and Hyperopt Workflows

## Initialize a config

```bash
ludwig init_config --dataset dataset.csv --target target_column --output config.yaml
```

Use this when the user has data and a target but no Ludwig config yet.

## Hyperopt config shape

```yaml
hyperopt:
  parameters:
    trainer.learning_rate:
      space: loguniform
      lower: 0.0001
      upper: 0.01
  goal: minimize
  output_feature: label
  validation_metrics: loss
  executor:
    type: ray
    num_samples: 2
  search_alg:
    type: variant_generator
```

The `output_feature` and `validation_metrics` must match model outputs and available metrics. Keep tiny `num_samples` for smoke tests.

## Python AutoML pattern

```python
from ludwig.automl import auto_train, create_auto_config
# Requires optional Ray/Dask dependencies in many installations.
```

If importing `ludwig.automl` fails because Ray or Dask is missing, install the narrow optional dependencies required by the selected backend before running AutoML.

## Safe tuning rules

- Always set a time or sample budget.
- Use small datasets or generated fixtures for smoke tests.
- Avoid distributed executors unless Ray is installed and initialized intentionally.
- Preserve output directories; they contain the chosen config and tuning statistics.
