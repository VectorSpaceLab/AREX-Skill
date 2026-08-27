# Training Workflows

## CLI training

```bash
ludwig train \
  --config config.yaml \
  --dataset dataset.csv \
  --output_directory results \
  --experiment_name demo \
  --model_name run
```

Use `--training_set`, `--validation_set`, and `--test_set` when data is already split. Otherwise `--dataset` may use a split column or random split behavior.

## Experiment workflow

```bash
ludwig experiment --config config.yaml --dataset dataset.csv --output_directory results
```

`experiment` combines training and evaluation. It is the best default when the user wants model performance rather than just trained weights.

## Python API workflow

```python
from ludwig.api import LudwigModel

model = LudwigModel(config)
train_results = model.train(dataset="dataset.csv", output_directory="results")
eval_stats, predictions, output_dir = model.evaluate(dataset="dataset.csv")
```

Use DataFrames for in-memory workflows and file paths for reproducible CLI parity.

## Output artifacts

Typical output directories include model weights, model hyperparameters/config metadata, training-set metadata, training statistics, progress/checkpoints, TensorBoard logs, prediction/evaluation outputs, and reports. Exact paths depend on experiment/model names.

## Resume and reproducibility

- Set `--random_seed` for reproducible splits/initialization where deterministic kernels permit it.
- Use `--model_resume_path` to continue from a previous run directory.
- Use skip-save flags only for smoke tests; they can remove artifacts needed for reload/prediction.
