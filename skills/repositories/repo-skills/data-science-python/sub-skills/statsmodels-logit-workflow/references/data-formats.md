# Data formats

## Bundled input fixtures

### `admissions_train.csv`

| Column | Type | Required | Notes |
| --- | --- | --- | --- |
| `admit` | binary integer | yes | Target column for the logistic regression fit. Expected values are `0` and `1`. |
| `gre` | numeric | yes | GRE score used as a model feature. |
| `gpa` | numeric | yes | GPA used as a model feature. |
| `prestige` | categorical string | yes | Undergraduate institution prestige label. |

### `admissions_test.csv`

| Column | Type | Required | Notes |
| --- | --- | --- | --- |
| `gre` | numeric | yes | GRE score used for prediction. |
| `gpa` | numeric | yes | GPA used for prediction. |
| `prestige` | categorical string | yes | Prestige label used for dummy encoding. |

## Prestige categories in the bundled fixtures

The copied fixtures contain these labels:

- `best`
- `good`
- `ok`
- `veryGood`

The helper uses `best` as the reference category when it is present. The fitted design matrix then contains these dummy columns:

- `prestige_good`
- `prestige_ok`
- `prestige_veryGood`

The intercept is added internally and is not written to the output CSV.

## Output CSV

The helper writes a prediction CSV that keeps the original test columns and appends two fields:

| Column | Type | Notes |
| --- | --- | --- |
| original test columns | same as input | `gre`, `gpa`, `prestige`, and any extra columns you may have added are preserved in row order. |
| `admit_pred` | float | Predicted admission probability in `[0, 1]`. |
| `admit_yn` | string | Thresholded label, `yes` when `admit_pred >= --threshold`, otherwise `no`. |

If you pass a test CSV with extra columns, the helper ignores them for modeling and preserves them in the output.
