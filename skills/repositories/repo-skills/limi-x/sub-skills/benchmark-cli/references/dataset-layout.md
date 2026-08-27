# Dataset layout for LimiX benchmark CLIs

The benchmark CLIs expect a dataset root containing one subfolder per dataset. Each dataset folder name is reused as the CSV filename prefix.

## Folder schema

```text
dataset_root/
  dataset_a/
    dataset_a_train.csv
    dataset_a_test.csv     # optional for classification; recommended/required for current regression scoring
  dataset_b/
    dataset_b_train.csv
```

Rules:

- `dataset_root` may contain multiple dataset folders. Plain files directly under the root are skipped.
- The dataset folder basename must match the CSV prefix exactly: `my_data/my_data_train.csv` and, when present, `my_data/my_data_test.csv`.
- CSVs should include a header row because the CLIs read them with pandas default CSV semantics.
- The last column is always treated as the target. Every preceding column is treated as a feature.
- Each CSV must have at least two columns: one or more features plus one target column.
- If a test CSV is present, its feature columns should match the train CSV feature columns in the same order.

## Test CSV behavior

| Task | If `<dataset>_test.csv` exists | If `<dataset>_test.csv` is absent |
| --- | --- | --- |
| Classification CLI | Uses the file as the test set. | Splits the train CSV into train/test with `test_size=0.5` and `random_state=42`. |
| Regression CLI | Uses the file as the test set. | The current regression CLI attempts to read the missing file, catches/logs the error when not in debug mode, and skips that dataset. In debug mode it raises. Provide a test CSV for reliable regression scoring. |

## Classification dataset details

- The last column is label-encoded as the classification target.
- The benchmark classifier currently supports 2 to 10 training classes. Fewer than 2 or more than 10 classes cause that dataset to be skipped through the CLI's error-handling path.
- Training datasets with `>= 50000` rows are skipped by the classification CLI because of GPU-memory constraints. LimiX usage guidance targets tabular datasets below 50,000 samples and below 10,000 features.
- Object/string feature columns are label-encoded using the training column values. If the test column contains unseen categories and the transform fails, the classification CLI drops that entire feature column for both train and test.
- After categorical handling, features are converted to `float32` and scaled with a MinMax scaler fit on the training split.
- Classification metrics in `all_rst.csv` are AUC, accuracy, F1, log-loss, and ECE.

## Regression dataset details

- The last column is cast to `float` as the regression target. Nonnumeric targets cause dataset failure/skipping.
- The regression CLI normalizes `y_train` and `y_test` by the training target mean/std before computing RMSE and R². A zero-variance training target is invalid for this normalization.
- Feature DataFrames are passed into the predictor, which performs its own numeric/categorical preprocessing. Prefer simple numeric features or categorical values that are consistently represented across train and test.
- Provide a test CSV; without it the current regression CLI does not do the classification-style train/test split.
- Regression prediction CSVs contain original-scale `label` and denormalized `pred`, while `all_rst.csv` RMSE/R² are computed on the normalized target.

## Validating a root before inference

Use the bundled lightweight validator. It reads CSV metadata and rows but does not import LimiX, load a checkpoint, or run model inference.

```bash
python sub-skills/benchmark-cli/scripts/validate_dataset_layout.py DATASET_ROOT --task classification
python sub-skills/benchmark-cli/scripts/validate_dataset_layout.py DATASET_ROOT --task regression
python sub-skills/benchmark-cli/scripts/validate_dataset_layout.py DATASET_ROOT --task auto
```

The validator checks:

- immediate child folders under the dataset root;
- required `<dataset>_train.csv` names;
- optional `<dataset>_test.csv` names and train/test feature-column matches;
- at least two columns and at least one data row;
- row width consistency;
- classification class counts and 2..10 class support;
- regression numeric target summary and zero-variance target risk;
- the 50,000 training-row skip threshold;
- object-like feature columns and unseen test categories for classification.

To create a tiny local fixture outside the runtime skill tree:

```bash
python sub-skills/benchmark-cli/scripts/validate_dataset_layout.py --make-fixture /tmp/limix_fixture --task auto
python sub-skills/benchmark-cli/scripts/validate_dataset_layout.py /tmp/limix_fixture --task auto
```

Do not place generated fixtures or validation reports under `limi-x runtime sub-skill directory`; that directory is reserved for runtime skill files.
