# Classic Igel API Reference

Read this when using Igel from Python, translating CLI commands into `Igel(**kwargs)`, or debugging the artifacts written by a classic tabular run. These facts target the verified Igel 0.7.0 package surface.

## Public import surface

```python
from igel import Igel, models_dict, metrics_dict
```

- `Igel` is initialized as `Igel(**cli_args)`. The verified callable signature is `(**cli_args)`.
- `models_dict` and `metrics_dict` expose the classic sklearn-backed model and metric registries used by the CLI.
- Construction of `Igel(...)` immediately executes the requested command by dispatching on `cmd`; it is not a lazy object builder.

## `Igel(**cli_args)` payloads

| Payload | Required keys | Optional keys | Behavior |
| --- | --- | --- | --- |
| `cmd="fit"` | `data_path`, `yaml_path` | sklearn model kwargs through code calling `Igel(..., **kwargs)` are not typical; put model args in config instead | Reads YAML/JSON config, reads/preprocesses data, fits the selected model, writes `model_results/model.joblib` and `model_results/description.json`. |
| `cmd="evaluate"` | `data_path` | `model_path`, `description_file` | Loads the saved sklearn model and training description, evaluates on the supplied dataset, writes `model_results/evaluation.json`. |
| `cmd="predict"` | `data_path` | `model_path`, `description_file`, `prediction_file` | Loads the saved sklearn model and training description, predicts on the supplied dataset, writes `model_results/predictions.csv` unless `prediction_file` is supplied programmatically. |
| `cmd="export"` | `model_path` | none | Loads a fitted sklearn model and writes `model_results/model.onnx` using a fixed ONNX input shape assumption. |

Important programmatic caveat: the CLI has an `experiment` command, but the current `Igel` class does not implement a separate `experiment()` method. For Python usage, run `fit`, `evaluate`, and `predict` payloads sequentially instead of calling `Igel(cmd="experiment", ...)`.

## CLI-to-Python examples

```python
from igel import Igel

Igel(cmd="fit", data_path="train.csv", yaml_path="igel.yaml")
Igel(cmd="evaluate", data_path="eval.csv")
Igel(cmd="predict", data_path="new_rows.csv")
Igel(cmd="export", model_path="model_results/model.joblib")
```

If model artifacts were moved, keep `model.joblib` and `description.json` aligned and pass explicit paths programmatically:

```python
Igel(
    cmd="predict",
    data_path="new_rows.csv",
    model_path="saved/model.joblib",
    description_file="saved/description.json",
    prediction_file="saved/predictions.csv",
)
```

## Output artifacts

Classic runs use a working-directory-relative artifact convention:

| Artifact | Created by | Meaning |
| --- | --- | --- |
| `igel.yaml` | `igel init` / `Igel.create_init_mock_file(...)` | Starter config generated in the current working directory. |
| `model_results/model.joblib` | `fit` | Serialized sklearn estimator, or a sklearn multi-output wrapper when multiple targets were requested. |
| `model_results/description.json` | `fit` | Training metadata: model class/name/type, dataset props, model props, data path, train/test shapes, target list, split/CV/search results when available. |
| `model_results/evaluation.json` | `evaluate` | Metric results or model score for the supplied evaluation data. |
| `model_results/predictions.csv` | `predict` | Prediction columns named from the saved target list; clustering falls back to `result` when no target exists. |
| `model_results/model.onnx` | `export` | ONNX conversion of the fitted sklearn model. |

Run `fit`, `evaluate`, and `predict` from the same working directory unless you pass explicit programmatic artifact paths. The current defaults are computed from the process working directory used by the Python import/run.

## Config and init helpers

`Igel.create_init_mock_file(model_type=None, model_name=None, target=None)` writes a starter `igel.yaml`. The CLI wrapper exposes it as:

```bash
igel init --model_type classification --model_name RandomForest --target "sick"
# short flags:
igel init -type classification -name RandomForest -tg sick
```

The target argument is split on spaces into a YAML list, so `--target "y1 y2"` creates two targets.

Config files are read as YAML only when the extension is `.yaml`; otherwise the current implementation routes to JSON reading. Prefer `.yaml` or `.json`, not `.yml`.

## Data and preprocessing helpers

These helper signatures were verified from the installed package:

| Helper | Signature | Practical use |
| --- | --- | --- |
| `read_data_to_df` | `read_data_to_df(data_path, **read_data_options)` | Chooses a pandas reader from file extension and passes `read_data_options` through. |
| `handle_missing_values` | `handle_missing_values(df, fill_value=nan, strategy="mean")` | Uses `drop` or sklearn `SimpleImputer` strategies such as `mean`, `median`, `most_frequent`, and `constant`. |
| `encode` | `encode(df, encoding_type="onehotencoding", column=None)` | `onehotencoding` calls pandas `get_dummies`; `labelencoding` requires a `column` and records a class map in fit metadata. |
| `normalize` | `normalize(x, y=None, method="standard")` | Uses `standard` or `minmax` scaling. Config controls whether inputs, outputs, or all arrays are scaled. |

## Fit/evaluate behavior to know

- Non-clustering configs must provide `target` as a non-empty list. Multiple targets automatically wrap the selected estimator in `MultiOutputClassifier` or `MultiOutputRegressor`.
- Clustering configs can omit or leave `target` empty. Fit records cluster centers and labels when the estimator exposes them.
- If no `dataset.split` is configured, `fit` trains and scores on the full training data. If a split is configured, it uses `train_test_split` and evaluates on the split test portion.
- `model.cross_validate` passes directly to `sklearn.model_selection.cross_validate` when present.
- `model.use_cv_estimator: true` selects a registered sklearn `*CV` class only for algorithms that define one in Igel's model registry.
- `model.hyperparameter_search.method` must be `grid_search` or `random_search`; search arguments are passed to `GridSearchCV` or `RandomizedSearchCV`.
- `evaluate` uses regression/classification metric functions when shapes are simple. Multi-target evaluation falls back to the model score.
- `export` uses `skl2onnx.convert_sklearn` and a fixed `FloatTensorType([None, 4])` input shape. Verify feature count before relying on ONNX output.
