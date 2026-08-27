# Classic Igel Data Formats

Use this reference before preparing `data_path` files for `fit`, `evaluate`, `predict`, `experiment`, or the bundled tabular helper.

## Reader selection

Igel selects the pandas reader from the file extension of `data_path`:

| Extension | Reader path | Notes |
| --- | --- | --- |
| `.csv` | `pandas.read_csv` | Recommended default for reproducible tabular workflows. |
| `.txt` | `pandas.read_csv` | Use `read_data_options.sep` or `delimiter` for non-comma text files. |
| `.xlsx` | `pandas.read_excel` | Requires a pandas-compatible Excel engine in the environment. Use `sheet_name` in `read_data_options` when needed. |
| `.json` | `pandas.read_json` | Set options such as `orient`, `lines`, or `dtype` when the default reader is insufficient. |
| `.html` | `pandas.read_html` | Best for simple single-table exports. For complex or multi-table pages, pre-extract the intended table to CSV/JSON before fitting. |

`dataset.type` in the config is not the dispatch key; the filename extension is.

## `read_data_options`

`read_data_options` is passed as keyword arguments to the selected pandas reader. It must be a mapping.

Common CSV/TXT pattern:

```yaml
dataset:
  read_data_options:
    sep: ";"
    header: 0
    usecols: [feature_a, feature_b, label]
    na_values: ["", "NA", "null"]
```

Common JSON-lines pattern:

```yaml
dataset:
  read_data_options:
    lines: true
```

Common Excel pattern:

```yaml
dataset:
  read_data_options:
    sheet_name: Sheet1
```

Do not use `read_data_options: default`; omit the key when no options are required.

## Train/evaluate/predict column expectations

For regression/classification:

1. Training and evaluation data must include every column listed in `target`.
2. Igel removes target columns from the feature matrix before fitting/evaluating.
3. Prediction data should contain only the feature columns expected by the fitted model, with the same order/encoding/scaling assumptions as training.
4. If preprocessing adds dummy columns during training, make sure prediction-time categorical values produce a compatible feature set. The current package does not persist a one-hot column schema reconciler.

For clustering:

1. No target column is required.
2. Fit and predict use all columns as features after preprocessing.
3. Prediction output uses a `result` column when no target list exists.

## Missing values

Configured through `dataset.preprocess.missing_values`:

| Value | Behavior |
| --- | --- |
| `drop` | Drops rows with missing values. |
| `mean` | Imputes numeric columns with the mean. |
| `median` | Imputes numeric columns with the median. |
| `most_frequent` | Imputes with the most frequent value. |
| `constant` | Uses sklearn `SimpleImputer` constant behavior; set a compatible fill value only through code if needed. |

If columns contain strings and you use numeric strategies such as `mean`, imputation can fail. Encode or clean categorical columns first, or use `most_frequent`.

## Encoding

```yaml
dataset:
  preprocess:
    encoding:
      type: labelEncoding
      column: Species
```

- `oneHotEncoding` uses pandas `get_dummies` on the whole frame. Use it when categorical input columns need expansion.
- `labelEncoding` transforms exactly one named column and stores a class map in the fit description.
- Label encoding requires `column`. If the column does not exist, the current preprocessing path does not perform encoding, so validate names before fitting.
- For prediction, ensure incoming categorical values map to the same columns/classes as training. Igel does not store and reapply a full encoder pipeline.

## Scaling

```yaml
dataset:
  preprocess:
    scale:
      method: standard
      target: inputs
```

- `method: standard` uses standard scaling.
- `method: minmax` uses min-max scaling.
- `target: inputs` scales feature matrix only.
- `target: outputs` scales target matrix only.
- `target: all` scales both inputs and outputs.

## Splits

```yaml
dataset:
  split:
    test_size: 0.2
    shuffle: true
    stratify: default
```

- When `split` is present, Igel uses `train_test_split`; fit metrics are calculated on the split test portion.
- When `split` is absent, Igel fits on all rows and reports the model score on the training data.
- Keep test sizes and shuffle choices explicit in reproducibility-sensitive runs.

## Practical data-shape checks

Before fitting, check:

- The input file extension is one Igel reads.
- The file opens with the intended pandas reader and options.
- Non-clustering configs list targets as a list and those columns exist.
- Prediction files do not include target columns unless the fitted model and preprocessing can tolerate them.
- Categorical columns are handled consistently between fit and predict.
- A planned ONNX export uses a model trained on exactly four feature columns unless you have patched or verified a newer export path.

Use the bundled helper in dry-run/check mode for config validation:

```bash
python scripts/run_tabular_cycle.py check-config --yaml-path igel.yaml --data-path train.csv
```
