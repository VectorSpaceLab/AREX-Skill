# Generated Artifact Reference

This reference describes the timestamped folder that `automl_grid_search`
writes after a search run and how to use the generated code without reopening
the original repository.

It is distilled from the package templates, the public README and design notes,
and a rendered XGBoost artifact inspected during setup.

## 1) Timestamped folder lifecycle

The search loop writes a temporary training folder during trials, then copies
its winning contents into a timestamped folder named like:

```text
<model_name>_<framework>_<YYYYMMDD>_<HHMMSS>/
```

The generated folder is the self-contained runtime artifact. The separate
search-level `automl_results.csv` lives beside the search run, not inside the
timestamped folder.

## 2) Canonical generated folder layout

```text
<generated-folder>/
  model.py
  pipeline.py
  requirements.txt
  encoders/
    *.json
  metadata/
    results.csv
  model.bin                  # XGBoost only, after train
  model_weights.hdf5         # TensorFlow only, after train
  predictions.csv            # written by predict when -t csv
  predictions.json           # written by predict when -t json
```

Notes:

- `model.bin` and `model_weights.hdf5` are framework-specific and only appear
  after a successful `train` run.
- `predictions.csv` / `predictions.json` are created only after `predict`.
- `encoders/` and `metadata/` should exist even when the folder is first
  created; their contents may be empty until training finishes.
- Run the generated scripts from inside the folder so all relative paths resolve
  correctly.

## 3) Generated `model.py` contract

The generated script expects a CSV plus a mode:

| Flag | Meaning | Notes |
| --- | --- | --- |
| `-d`, `--data` | Input CSV path | Read with the schema frozen into the artifact. |
| `-m`, `--mode` | `train` or `predict` | Any other value falls through without a train/predict branch. |
| `-s`, `--split` | Train/validation split | Used during `train`. |
| `-e`, `--epochs` | Training epochs | Used during `train`. |
| `-c`, `--context` | Search-loop context | `automl-gs` is for the parent search loop; `standalone` is the default. |
| `-t`, `--type` | Prediction file format | `csv` or `json` only. |

The script loads the CSV with the exact column list and dtype map embedded in
that generated file, then calls the shared helpers in `pipeline.py`.

### Target label handling

- TensorFlow generated artifacts encode the target inside `process_data()` and
  can work with label strings that the encoder understands.
- XGBoost generated artifacts pass the raw target column into `xgb.DMatrix`
  during train. In practice, the target must already be numeric or otherwise
  float-compatible in the generated `dtypes` map; string labels will fail
  during training even though the artifact still writes `target_encoder.json`
  for metrics and prediction headers.
- For multiclass XGBoost, the target should be integer class ids.

## 4) CSV loading expectations

The generated script uses `pd.read_csv(..., usecols=cols, dtype=dtypes,
parse_dates=True)` with the column names frozen at generation time.

Implications:

- The CSV must contain the raw column headers listed in the generated
  `model.py`.
- Extra columns are ignored because `usecols` selects only the frozen schema.
- Columns that the artifact marked numeric must parse as numbers.
- Datetime columns are still parsed from CSV text by `pd.to_datetime` later in
  the pipeline.
- Column names with spaces or punctuation are acceptable in the CSV, but the
  generated Python variables are normalized internally to safe identifiers.
- Do not rename CSV headers to the normalized Python names; the generated
  loader still reads the original raw headers.

## 5) Pipeline helpers

The generated `pipeline.py` exposes the runtime helpers that make the artifact
self-contained:

| Function | Role |
| --- | --- |
| `build_encoders(df)` | Fit the encoder state and serialize it into `encoders/`. |
| `load_encoders()` | Rebuild the in-memory encoders from JSON files. |
| `process_data(df, encoders, process_target=True)` | Transform the CSV into model-ready arrays. |
| `model_predict(df, model, encoders)` | Run inference and return a prediction `DataFrame`. |
| `model_train(df, encoders, args, model=None)` | Train the framework model, write metrics, and save the framework artifact. |

The helper names are stable across generated folders, even though the concrete
encoder files depend on the inferred field types.

## 6) Encoder inventory

The exact encoder files depend on the training schema.

| Field type | Typical files | Notes |
| --- | --- | --- |
| Categorical | `<field>_encoder.json` | Stores `LabelBinarizer.classes_`. |
| Numeric with minmax/standard | `<field>_encoder.json` | Stores scaler parameters. |
| Numeric with quantiles/percentiles | `<field>_bins.json` | Stores bin edges; the encoder itself is rebuilt in code. |
| Datetime | `dayofweeks_encoder` and `hour_encoder` in code | These are fixed classes, not serialized. Optional month/year branches may add more files. |
| Text | `model_vocab.json` | Shared vocabulary for all text fields; TensorFlow and non-TensorFlow text paths differ. |
| Target classification | `target_encoder.json` | Not written for regression. |

The filenames are based on normalized field identifiers inside the generated
code, not on the raw CSV headers.

## 7) Metadata and prediction outputs

### `metadata/results.csv`

This file records per-epoch metrics and timestamps. The first columns are
always `epoch` and `time_completed`, followed by the problem-specific metrics.

Typical metric groups:

- Regression: `mse`, `mae`, `r_2`.
- Binary classification: `log_loss`, `accuracy`, `auc`, `precision`,
  `recall`, `f1`.
- Multiclass classification: `log_loss`, `accuracy`, `precision`, `recall`,
  `f1`.

### `predictions.csv` / `predictions.json`

The output format is chosen by `-t/--type` during `predict`.

| Problem type | Prediction columns |
| --- | --- |
| Regression | One column named after the target field. |
| Binary classification | One column named `probability`. |
| Multiclass classification | One column per target class label. |

`csv` writes a tabular file with headers. `json` writes records orient JSON,
one object per predicted row.

## 8) Requirements file

The generated `requirements.txt` is the runtime list for the artifact itself.
It is intentionally small.

| Framework | Generated requirements |
| --- | --- |
| Shared base | `scikit-learn`, `pandas` |
| XGBoost | `xgboost` |
| TensorFlow | `tensorflow>=1.12`, `hdf5` |

Use this file to recreate the generated runtime, not the package search loop.

## 9) XGBoost vs TensorFlow generated artifacts

### XGBoost

- Uses `xgb.Booster` and `model.bin` for the saved model.
- `pipeline.py` converts processed feature arrays into an `xgb.DMatrix`.
- Predict mode loads `model.bin` and writes `predictions.csv` or
  `predictions.json`.
- Newer xgboost releases may warn that `model.bin` is being interpreted as
  UBJSON and that `silent` is unused; the artifact still round-trips.
- The verified inspection artifact in this workspace was XGBoost-based.

### TensorFlow

- Builds a Keras model in `pipeline.py` and saves `model_weights.hdf5`.
- Training metrics come from a Keras callback rather than the XGBoost loop.
- The template still uses legacy TensorFlow 1.x-era APIs, so treat this path as
  compatibility-sensitive unless you have confirmed runtime support.
- This environment did not verify a TensorFlow-generated artifact.

## 10) Practical reading order

1. Check the folder structure with `scripts/check_generated_folder.py`.
2. Read `model.py` only for the frozen schema, mode flags, and output format.
3. Read `pipeline.py` for helper behavior and encoder expectations.
4. Consult the troubleshooting guide when a runtime file, working directory, or
   framework mismatch blocks training or prediction.
