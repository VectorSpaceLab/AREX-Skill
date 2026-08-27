# Generated Artifact Troubleshooting

This guide covers the most common ways a generated automl-gs artifact folder
fails after the search run has already produced it.

## Fast symptom-to-fix table

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `FileNotFoundError` for `encoders/...json` | `train` has not been run, the folder is incomplete, or the working directory is wrong. | `cd` into the generated folder and rerun `python model.py -d <csv> -m train`. |
| `FileNotFoundError` for `metadata/results.csv` | Training never completed or the script was run outside the generated folder. | Rerun `train` from inside the folder and confirm `metadata/results.csv` appears. |
| `FileNotFoundError` for `model.bin` | XGBoost predict was attempted before train, or the folder is not an XGBoost artifact. | Train first in the same folder. If the artifact is TensorFlow-based, look for `model_weights.hdf5` instead. |
| `FileNotFoundError` for `model_weights.hdf5` | TensorFlow predict was attempted before train, or the runtime does not match the artifact. | Use the matching TensorFlow-generated folder and a compatible legacy TensorFlow runtime. |
| No `predictions.csv` or `predictions.json` after `predict` | `--mode` or `--type` was invalid, or the process had no write permission. | Use `-m predict` and `-t csv` or `-t json`; the generated script has no fallback branch for unsupported values. |
| Prediction columns look wrong | The output format is problem-type dependent. | Regression writes the target field, binary classification writes `probability`, and multiclass writes one column per class label. |
| CSV loading fails with dtype or parse errors | The new CSV does not match the frozen schema in `model.py`. | Inspect the embedded `cols` and `dtypes` values in the generated script and fix the source CSV headers or value types. |
| `ValueError: could not convert string to float` during XGBoost train | The frozen target or another numeric field is stored as text, and XGBoost receives the raw target column as a label. | Make the generated XGBoost artifact use a numeric-compatible target column, or regenerate the artifact with a schema that marks the target numeric; string labels are not safe for this XGBoost path. |
| `predict` or `train` appears to do nothing | `--mode` was omitted or misspelled. | Re-run with the exact `train` or `predict` string; there is no else branch for invalid values. |
| Relative paths cannot be found | The command was run from the parent search directory or another folder. | Run all generated commands from inside the timestamped artifact folder. |
| Import/runtime errors for `xgboost` or `tensorflow` | The runtime does not match the generated framework. | Install from the generated `requirements.txt` and use the artifact framework that was actually generated. |

## Missing encoder files

If a generated folder has `encoders/` but the directory is empty or missing the
expected JSON files:

1. Confirm `train` actually finished.
2. Make sure the CSV passed to `train` contains the frozen column set.
3. Re-run `train` from inside the generated folder so the JSON files are written
   to the correct relative path.

Remember that encoder filenames are derived from normalized internal names, not
from the raw CSV headers.

## Wrong working directory

The generated `model.py` and `pipeline.py` use relative paths such as
`encoders/`, `metadata/`, `model.bin`, `model_weights.hdf5`, and
`predictions.*`.

If you are one directory too high, the script may still start but read or write
files in the wrong place. Always `cd` into the generated folder before running
`train` or `predict`.

## Mode errors

The generated `model.py` only branches on:

- `train`
- `predict`

It also only recognizes `csv` and `json` for `-t/--type`.

If another value is supplied, the script can finish without producing the files
that you expected. Re-run with the exact supported value.

## Framework or runtime mismatch

### XGBoost artifact

- The generated model loads `model.bin` through `xgb.Booster()`.
- If the model file is missing, rerun `train` in the XGBoost artifact folder.
- If `xgboost` itself is missing, install from the generated requirements file.
- Newer xgboost versions may warn that `model.bin` is being guessed as UBJSON
  and that `silent` is unused; that warning is noisy but not fatal when the
  file actually loads.

### TensorFlow artifact

- The generated model loads `model_weights.hdf5` and rebuilds the Keras model.
- The TensorFlow template is legacy and was not verified in this environment.
- If the runtime uses a modern TensorFlow stack that does not match the legacy
  APIs, prefer the XGBoost artifact or confirm a compatible TensorFlow 1.x-era
  environment first.

## Malformed generated CSV dtypes

The generated loader freezes both the column selection and the dtype map.
Common problems are:

- A column that the artifact expects to be numeric is stored as text.
- A column the artifact expects to be text or datetime contains values that
  cannot be parsed.
- A raw column header changed after the artifact was created.

Recovery steps:

1. Open the generated `model.py` and inspect the embedded `cols` and `dtypes`.
2. Fix the input CSV so the original raw headers match those frozen names.
3. Make sure numeric values are actually parseable as numbers.
4. Make sure datetime strings are parseable by `pd.to_datetime`.

## Predict before train

A generated folder can exist before it has been trained, but `predict` needs the
saved model artifact.

- XGBoost needs `model.bin`.
- TensorFlow needs `model_weights.hdf5`.

If those files are missing, train first in the same folder.

## Folder validation helper

Run `scripts/check_generated_folder.py` when you want a quick summary of the
expected files and modes without opening the original repository checkout.
It reports the detected framework, the generated mode contract, and the files
that should be present for train or predict.
