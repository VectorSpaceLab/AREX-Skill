# Classic Igel Workflows

Use these recipes for everyday tabular/classic-ML Igel tasks. They do not require the original repository checkout; they assume the `igel` package is installed and importable in the active Python environment.

## 0. Quick route check

Stay in this sub-skill for:

- `igel init`, `fit`, `evaluate`, `predict`, `experiment`, `export`, `models`, `metrics`, `version`, `info`;
- YAML/JSON configs for regression, classification, clustering, multi-output, preprocessing, CV, and hyperparameter search;
- programmatic `from igel import Igel` usage.

Route elsewhere:

- Serving a saved model over FastAPI or using a REST client: [deployment](../../deployment/SKILL.md).
- AutoKeras/image/text/structured Auto-ML or `IgelCNN`: [auto-ml](../../auto-ml/SKILL.md).
- Unclear repo-wide task selection: [root router](../../../SKILL.md).

## 1. Inspect help and package metadata

```bash
igel --help
igel fit --help
igel evaluate --help
igel predict --help
igel export --help
igel init --help
igel version
igel info
```

Verified command surface includes `init`, `fit`, `evaluate`, `predict`, `experiment`, `export`, `models`, `metrics`, `serve`, `gui`, `version`, and `info`. This sub-skill owns all except `serve`, `gui`, and Auto-ML paths.

## 2. Create a starter config

```bash
igel init --model_type classification --model_name RandomForest --target "sick"
# short flags:
igel init -type classification -name RandomForest -tg sick
```

Expected result: `igel.yaml` appears in the current working directory. Edit it before fitting. For multi-output targets, pass a space-separated target string to init or edit the YAML list manually:

```yaml
target:
  - y1
  - y2
```

Older examples may show `-model` or `-target`; use the verified current short flags `-name` and `-tg`.

## 3. Fit/train a model

```bash
igel fit --data_path train.csv --yaml_path igel.yaml
# short flags:
igel fit -dp train.csv -yml igel.yaml
```

Expected artifacts:

```text
model_results/
  model.joblib
  description.json
```

Use [configuration.md](configuration.md) to prepare the config and [data-formats.md](data-formats.md) to confirm the data reader and target columns.

## 4. Evaluate a fitted model

Run from the same working directory used for `fit`, or use the Python API with explicit artifact paths.

```bash
igel evaluate --data_path eval.csv
# short flag:
igel evaluate -dp eval.csv
```

Expected artifact:

```text
model_results/evaluation.json
```

For regression/classification, metrics come from [model-catalog.md](model-catalog.md). For multi-output or clustering, expect estimator-score behavior rather than the full simple metric table.

## 5. Predict with a fitted model

Run from the same working directory used for `fit`.

```bash
igel predict --data_path new_rows.csv
# short flag:
igel predict -dp new_rows.csv
```

Expected artifact:

```text
model_results/predictions.csv
```

Prediction data should contain the feature columns expected by the fitted model. It usually should not include target columns. For categorical one-hot workflows, make sure prediction-time categories produce a compatible feature matrix.

## 6. Combine fit/evaluate/predict with `experiment`

```bash
igel experiment --data_paths "train.csv eval.csv new_rows.csv" --yaml_path igel.yaml
# short flags:
igel experiment -DP "train.csv eval.csv new_rows.csv" -yml igel.yaml
```

The CLI splits `--data_paths` on spaces into exactly three paths: train, evaluation, prediction. Avoid this shortcut when file paths contain spaces; run explicit `fit`, `evaluate`, and `predict` commands instead.

Programmatic note: use three `Igel(...)` calls instead of `Igel(cmd="experiment")`; the current class does not implement an `experiment()` method.

## 7. Export a fitted sklearn model to ONNX

```bash
igel export --model_path model_results/model.joblib
# short flag uses -dp even though the argument is a model path:
igel export -dp model_results/model.joblib
```

Expected artifact:

```text
model_results/model.onnx
```

Export caveats:

- The path exports sklearn models saved by classic `fit`, not AutoKeras models.
- The current export path uses `FloatTensorType([None, 4])`. It is naturally aligned with four-feature examples such as iris, but it can fail or produce unusable ONNX for other feature counts.
- Export requires `skl2onnx` and compatible legacy NumPy/SciPy/sklearn dependencies; see [troubleshooting.md](troubleshooting.md).

## 8. Show supported models and metrics

```bash
igel models
igel models -type classification -name RandomForest
igel models --model_type regression --model_name Ridge
igel metrics
```

Use exact algorithm names in configs. The CLI model table and [model-catalog.md](model-catalog.md) are the safest source for spelling.

## 9. Use Igel from Python

```python
from igel import Igel

Igel(cmd="fit", data_path="train.csv", yaml_path="igel.yaml")
Igel(cmd="evaluate", data_path="eval.csv")
Igel(cmd="predict", data_path="new_rows.csv")
Igel(cmd="export", model_path="model_results/model.joblib")
```

With explicit moved artifacts:

```python
Igel(
    cmd="evaluate",
    data_path="eval.csv",
    model_path="saved/model.joblib",
    description_file="saved/description.json",
)
```

The constructor executes immediately. Do not instantiate it before validating paths/configs if side effects matter.

## 10. Classification with preprocessing

```yaml
dataset:
  split:
    test_size: 0.2
    shuffle: true
  preprocess:
    missing_values: mean
    encoding:
      type: labelEncoding
      column: Species
    scale:
      method: standard
      target: inputs
model:
  type: classification
  algorithm: LogisticRegression
target:
  - Species
```

Then:

```bash
igel fit -dp train.csv -yml igel.yaml
igel evaluate -dp eval.csv
igel predict -dp new_rows.csv
```

## 11. Multi-output regression/classification

```yaml
model:
  type: regression
  algorithm: RandomForest
target:
  - y1
  - y2
  - y3
```

When the target list has more than one entry, Igel automatically wraps the estimator with `MultiOutputRegressor` or `MultiOutputClassifier`. Validate that evaluation and prediction data carry the expected columns and that downstream metric interpretation can use a single estimator score.

## 12. Clustering workflow

```yaml
model:
  type: clustering
  algorithm: KMeans
  arguments:
    n_clusters: 3
    random_state: 0
target:
```

Run:

```bash
igel fit -dp cluster_train.csv -yml igel.yaml
igel predict -dp cluster_new_rows.csv
```

Do not add a target list for clustering. Fit writes model artifacts and clustering results when the estimator exposes labels/centers.

## 13. Cross-validation workflow

Use a CV estimator when the catalog supports one:

```yaml
model:
  type: classification
  algorithm: Ridge
  use_cv_estimator: true
```

Run sklearn `cross_validate` during fit:

```yaml
model:
  type: classification
  algorithm: Ridge
  cross_validate:
    cv: 3
    n_jobs: 1
    verbose: 0
```

Keep CV settings bounded for quick checks. See [configuration.md](configuration.md) for the difference between `use_cv_estimator` and `cross_validate`.

## 14. Hyperparameter search workflow

```yaml
model:
  type: classification
  algorithm: RandomForest
  hyperparameter_search:
    method: random_search
    parameter_grid:
      max_depth: [6, 10]
      n_estimators: [100, 300]
    arguments:
      cv: 3
      n_iter: 2
      refit: true
      verbose: 0
```

Search can be expensive. In user-facing work, first bound `n_iter`, `cv`, and grid size; then inspect `description.json` for the recorded search metadata and sanity-check it before making claims.

## 15. Use the bundled helper

From this sub-skill directory, the helper is at `scripts/run_tabular_cycle.py`; from the root skill directory, it is at `sub-skills/tabular-workflows/scripts/run_tabular_cycle.py`.

Dry-run and validate a fit payload:

```bash
python scripts/run_tabular_cycle.py fit --data-path train.csv --yaml-path igel.yaml
```

Run the fit after validation:

```bash
python scripts/run_tabular_cycle.py fit --data-path train.csv --yaml-path igel.yaml --run
```

Run explicit evaluation/prediction payloads:

```bash
python scripts/run_tabular_cycle.py evaluate --data-path eval.csv --run
python scripts/run_tabular_cycle.py predict --data-path new_rows.csv --run
```

Generate and optionally execute a tiny four-feature iris fit/export demo in a temporary work directory:

```bash
python scripts/run_tabular_cycle.py demo-fit-export
python scripts/run_tabular_cycle.py demo-fit-export --run
```

The helper is dry-run-first and catches common config errors before importing igel or training.
