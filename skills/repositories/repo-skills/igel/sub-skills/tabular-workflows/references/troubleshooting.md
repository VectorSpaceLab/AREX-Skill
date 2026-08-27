# Classic Igel Troubleshooting

Use this when a classic tabular `igel` command, config, import, or export fails. Route serving/client issues to [deployment](../../deployment/SKILL.md) and AutoKeras/`IgelCNN` issues to [auto-ml](../../auto-ml/SKILL.md).

## Install/import failures from the legacy dependency stack

### Pip resolver or metadata errors

Symptoms can include resolver failures for old pinned dependencies, invalid metadata warnings, or a failure mentioning `uvicorn` metadata under modern `pip` releases.

Likely cause: Igel 0.7.0 targets an older Python and dependency stack. Modern package resolvers can reject metadata or upgrade transitive packages into incompatible versions.

Recovery:

1. Use a clean Python environment compatible with the package's Python 3.8-era constraints.
2. Use a pip/resolver version that accepts the legacy metadata, or install from a lock/resolution known to keep the old stack together.
3. Avoid mixing this package with a modern NumPy/SciPy/sklearn stack in a shared environment.
4. Verify with:

```bash
python -c "from igel import Igel; import igel; print(igel.__version__)"
igel --help
igel models
igel metrics
```

### `np.float` / too-new NumPy

Symptom:

```text
AttributeError: module 'numpy' has no attribute 'float'
```

Likely cause: a dependency path expects NumPy aliases removed from newer NumPy releases.

Recovery:

- Use a legacy-compatible NumPy version for the Igel 0.7.0 stack instead of allowing a current NumPy upgrade.
- Reinstall or pin the complete legacy NumPy/SciPy/scikit-learn/skl2onnx set together, then rerun the import/help checks above.

### `pinv2` / too-new SciPy

Symptom:

```text
ImportError: cannot import name 'pinv2' from scipy.linalg
```

Likely cause: older scikit-learn/skl2onnx-era code paths expect SciPy APIs removed from newer SciPy releases.

Recovery:

- Use a SciPy version compatible with the old scikit-learn 0.23-era stack.
- Re-run `python -c "from igel import Igel"`, `igel fit --help`, and `igel export --help` after pinning.

## CLI option mismatches

### `igel init` says no such option

Use the verified flags:

```bash
igel init --model_type classification --model_name RandomForest --target "sick"
igel init -type classification -name RandomForest -tg sick
```

Older snippets may use `-model` or `-target`, but the current Click CLI short flags are `-name` and `-tg`.

### `.yml` config fails as JSON

Symptom: a YAML-looking `.yml` file produces a JSON parse error.

Likely cause: current config dispatch reads YAML only for the `.yaml` extension; other extensions are routed to JSON.

Recovery: rename the file to `.yaml` or convert it to `.json`, then rerun `fit`.

### `experiment` cannot parse paths

`igel experiment -DP "train.csv eval.csv predict.csv" -yml igel.yaml` splits the string on spaces into exactly three paths. If paths contain spaces, run explicit `fit`, `evaluate`, and `predict` commands instead or use the bundled helper with separate arguments.

## Config validation failures

### Missing or scalar target

Symptoms:

```text
provide target(s) as a list in the yaml file
please provide at least a target to predict
```

Recovery for regression/classification:

```yaml
target:
  - target_column
```

Do not write `target: target_column`. Multi-output configs should list each target column separately. For clustering, omit `target` or leave it empty.

### Target column not found

Symptom:

```text
chosen target(s) to predict must exist in the dataset
```

Recovery:

1. Confirm the training/evaluation data file has the exact target column name after applying `read_data_options`.
2. Confirm case, whitespace, and delimiter handling.
3. For prediction files, remove target columns unless the fitted feature pipeline expects them.

Use:

```bash
python scripts/run_tabular_cycle.py check-config --yaml-path igel.yaml --data-path train.csv
```

### `read_data_options` is not a mapping

Symptom: Python fails while unpacking read options, or the reader behaves unexpectedly.

Cause: config uses `read_data_options: default` or another scalar.

Recovery: omit the key or use a mapping:

```yaml
dataset:
  read_data_options: {}
```

### Unsupported model type or algorithm

Symptoms:

```text
model_type and algorithm cannot be None
Model not found in the algorithms list
```

Recovery:

1. Set `model.type` to `regression`, `classification`, or `clustering`.
2. Use an exact `model.algorithm` key from [model-catalog.md](model-catalog.md) or `igel models`.
3. Preserve historical spellings such as `PassiveAgressiveClassifier` when using the current catalog.

### Invalid preprocessing options

Common recoveries:

- Missing-values strategy: use `drop`, `mean`, `median`, `most_frequent`, or `constant`.
- Encoding type: use `oneHotEncoding` or `labelEncoding`; label encoding requires `column`.
- Scale method: use `standard` or `minmax`.
- Scale target: use `inputs`, `outputs`, or `all`.
- For categorical data, validate that fit and predict produce the same one-hot columns; Igel does not persist a feature-column reconciler.

## Artifact-path failures

### `evaluate` or `predict` cannot find `model.joblib` or `description.json`

Likely cause: the command is running from a different working directory than the original `fit`, or artifacts were moved separately.

Recovery:

- Run from the directory containing `model_results/`.
- Keep `model_results/model.joblib` and `model_results/description.json` together.
- With Python, pass explicit `model_path` and `description_file`:

```python
from igel import Igel

Igel(
    cmd="predict",
    data_path="new_rows.csv",
    model_path="saved/model.joblib",
    description_file="saved/description.json",
)
```

### `predictions.csv` missing or empty

Likely causes:

- Prediction preprocessing failed and returned `None` before writing.
- Feature columns differ from fit-time columns.
- Categorical one-hot output has mismatched columns.

Recovery: validate the prediction file with the same reader options and feature schema used during fit; rerun with a tiny known-compatible row before batch prediction.

## ONNX export failures

### Missing `skl2onnx` or dependency import error

Symptoms may include import errors from `skl2onnx`, NumPy, SciPy, or scikit-learn.

Recovery: repair the legacy dependency stack first, then run:

```bash
igel export --model_path model_results/model.joblib
```

### Non-four-feature model fails or yields unusable ONNX

Current export uses a fixed input type equivalent to four float features:

```text
FloatTensorType([None, 4])
```

This matches four-feature examples but is not a general shape inference path.

Recovery:

1. Count the fitted feature columns after preprocessing.
2. If the feature count is not four, do not promise valid ONNX from the stock command.
3. Either patch/override the ONNX initial type in a project script, or keep the sklearn `model.joblib` artifact for prediction/serving.
4. Use a synthetic non-four-feature export case during verification to ensure the skill communicates this limitation.

## HTML and complex data files

Igel routes `.html` through pandas' HTML reader. Complex pages can produce multiple tables or a list-like result that is not a normal training frame. For reliable workflows, pre-extract the intended table to `.csv` or `.json` and then fit from that file.

## When to stop or reroute

- If the user's task is to start a FastAPI server, call `/predict`, use a Python REST client, troubleshoot Docker, or use the GUI, switch to [deployment](../../deployment/SKILL.md).
- If the user's task mentions AutoKeras, image/text/structured Auto-ML, or `IgelCNN`, switch to [auto-ml](../../auto-ml/SKILL.md).
- If package import fails even after a clean legacy dependency stack, stop and report the unresolved environment block before running fit/evaluate/predict.
