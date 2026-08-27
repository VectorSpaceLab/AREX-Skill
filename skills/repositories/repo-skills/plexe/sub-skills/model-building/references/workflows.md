# Plexe model-building workflows

This reference turns the main Plexe workflow into concrete user-facing recipes.
It covers new builds, resume flows, retraining, evaluation, and the final model package.

## 1. New model build

### CLI shape

```bash
python -m plexe.main \
  --train-dataset-uri data.parquet \
  --intent "predict churn" \
  --user-id user123 \
  --experiment-id churn_v1 \
  --spark-mode local \
  --max-iterations 5
```

### Python API shape

```python
from pathlib import Path
from plexe.main import main

best_solution, final_metrics, evaluation_report = main(
    intent="predict churn",
    train_dataset_uri="data.parquet",
    work_dir=Path("./workdir"),
)
```

### What happens

1. Load configuration from CLI arguments, environment variables, and optional YAML.
2. Start logging, LiteLLM routing, and OpenTelemetry if enabled.
3. Prepare or restore the experiment workspace.
4. Normalize the training dataset to Parquet.
5. Run the 6-phase workflow.
6. Package the best solution into `work_dir/model/` and `work_dir/model.tar.gz`.

## 2. Phase map

Plexe uses these phase names in checkpoints:

| Phase | Constant | Main output |
| --- | --- | --- |
| Data understanding | `01_analyze_data` | layout, stats, task analysis, metric selection |
| Data preparation | `02_prepare_data` | train/val/test splits and samples |
| Baselines | `03_build_baselines` | heuristic baseline |
| Model search | `04_search_models` | search journal and best solution |
| Final evaluation | `05_evaluate_final` | evaluation report and final metrics |
| Package final model | `06_package_final_model` | packaged model tree and archive |

The saved reports live under `work_dir/.build/reports/` and are named with a two-digit prefix.

## 3. Resume flow

Plexe resumes by loading the most recent checkpoint it can find, then continuing from
`phase_num + 1`.

Important behaviors:

- If a later checkpoint exists, Plexe skips earlier phases.
- If `allowed_model_types` is set on resume, it filters the checkpoint's viable model types.
- If a pause checkpoint contains `user_feedback`, the feedback is injected back into the context.
- If Phase 4 has no successful solution when resuming, Plexe falls back to the heuristic baseline.

### Resume-related triggers

- `auto_mode=False` pauses after Phase 1 for user feedback.
- `user_feedback={...}` is read by the agents when resuming.
- `allowed_model_types=[...]` can narrow the resumed search space.

## 4. Retraining flow

Retraining uses the same top-level entry point, but switches into `--is-retrain` mode.

### CLI shape

```bash
python -m plexe.main \
  --train-dataset-uri new_data.parquet \
  --intent "retrain the previous churn model" \
  --is-retrain \
  --original-model-uri ./old/model.tar.gz \
  --experiment-id churn_retrain_v1
```

### Requirements

- `--original-model-uri` or `--original-experiment-id` must be supplied.
- The original package must contain `artifacts/metadata.json`.
- The original package must contain `src/trainer.py` and `src/pipeline.py`.

### What retraining does

1. Extract the original package.
2. Load the pipeline and refit it on the new data.
3. Recreate the original model architecture.
4. Train the recreated model on the new train/validation split.
5. Save a fresh package with the retrained artifacts.

## 5. Evaluation flow

Final evaluation is optional unless `--test-dataset-uri` is supplied.
When enabled, Plexe computes the final metrics on the held-out test split.

Behavior to remember:

- If test data is provided, final evaluation is auto-enabled.
- If evaluation fails, Plexe falls back to validation performance.
- If the primary solution fails evaluation, Plexe may try the next-best valid solution.

## 6. Artifact tree

The final package is written to `work_dir/model/` and archived as `model.tar.gz`.

```text
model/
  artifacts/
    model.pkl | model.cbm | model.keras | model.pt
    pipeline.pkl
    label_encoder.pkl        # when classification labels are encoded
    metadata.json
    history.json             # PyTorch / Keras history when applicable
  src/
    pipeline.py
    predictor.py
    trainer.py               # retraining support
  schemas/
    input.json
    output.json
  config/
    hyperparameters.json
  evaluation/
    ...
  model.yaml
  README.md
```

The exact model artifact name depends on the model family:

- XGBoost: `artifacts/model.pkl`
- CatBoost: `artifacts/model.cbm`
- LightGBM: `artifacts/model.pkl`
- Keras: `artifacts/model.keras`
- PyTorch: `artifacts/model.pt` plus `artifacts/model_class.pkl`

## 7. Model families and training templates

Plexe supports these model families in the tabular workflow:

- `xgboost`
- `catboost`
- `lightgbm`
- `keras`
- `pytorch`

Training templates live under `plexe/templates/training/` and are executed in a subprocess
by `LocalProcessRunner`.

### Template-specific notes

- XGBoost, CatBoost, and LightGBM train from transformed parquet data.
- Keras streams parquet data through `tf.data.Dataset`.
- PyTorch streams parquet data through an iterable dataset and can use DDP.

## 8. Search policy notes

- `TreeSearchPolicy` is the default policy used by Plexe.
- `EvolutionarySearchPolicy` exists but is not the default in the current workflow.
- Search decisions are driven by the current journal, not by raw random sampling alone.

## 9. Common command patterns

### Constrain model families

```bash
python -m plexe.main \
  --train-dataset-uri data.parquet \
  --intent "predict churn" \
  --allowed-model-types xgboost lightgbm
```

### Force final evaluation

```bash
python -m plexe.main \
  --train-dataset-uri data.parquet \
  --test-dataset-uri test.parquet \
  --intent "predict churn"
```

### Use Databricks Connect

```bash
python -m plexe.main \
  --train-dataset-uri data.parquet \
  --spark-mode databricks
```

### Use custom CSV parsing

```bash
python -m plexe.main \
  --train-dataset-uri data.csv \
  --csv-delimiter tab \
  --csv-header true
```

## 10. Where to go next

- Use `configuration.md` when the request is about flags, env vars, or YAML settings.
- Use `api-reference.md` when the request is about signatures or object shapes.
- Use `data-formats.md` when the request is about inputs, splits, or packaged outputs.
- Use `troubleshooting.md` when the request is about failures or missing dependencies.

