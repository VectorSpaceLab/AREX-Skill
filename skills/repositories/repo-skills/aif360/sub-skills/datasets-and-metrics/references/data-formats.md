# Data formats and protected-group conventions

AIF360 has two data interfaces. This sub-skill covers the **legacy** interface in `aif360.datasets` and `aif360.metrics`. The newer `aif360.sklearn` interface keeps protected attributes in pandas indexes and is routed to the sibling sklearn sub-skill.

## Legacy dataset object model

| Object | Use it for | Key constraints |
| --- | --- | --- |
| `StructuredDataset` | General tabular data with labels, features, protected attributes, optional weights, and optional scores. | Input is a pandas `DataFrame`; every value must be numeric and NA-free. |
| `BinaryLabelDataset` | Binary classification labels and most legacy dataset/classification metrics. | Extends `StructuredDataset`; labels must be a single column containing only `favorable_label` and `unfavorable_label`. |
| `StandardDataset` | Converting a raw pandas `DataFrame` with categorical columns and domain-specific label/protected-class mappings into a `BinaryLabelDataset`. | Applies optional preprocessing, drops rows with NA, one-hot encodes `categorical_features`, maps privileged protected classes to `1.0`, unprivileged to `0.0`, and maps favorable labels. |
| `RegressionDataset` | Ranked or regression-style protected-group metrics. | Applies optional preprocessing, one-hot encoding, protected-class mapping, and min-max normalization before building a `StructuredDataset`. |

A `StructuredDataset` stores:

- `features`: all non-label, non-score, non-weight columns as `float64`; protected attributes are also retained as feature columns.
- `labels`: the target column(s).
- `scores`: prediction/probability-like scores; defaults to a copy of `labels` when no `scores_names` are supplied.
- `protected_attributes`: the columns named in `protected_attribute_names`.
- `instance_weights`: supplied weight column or all ones.
- `privileged_protected_attributes` and `unprivileged_protected_attributes`: encoded values used by metrics and algorithms.

## In-memory `BinaryLabelDataset` from pandas

Use this pattern for smoke tests, custom data, and reproducible examples. It avoids raw data, network access, and optional dependencies.

```python
import pandas as pd
from aif360.datasets import BinaryLabelDataset

# All values must be numeric and finite. Keep label/protected columns in the df.
df = pd.DataFrame({
    "risk_score": [0.1, 0.4, 0.8, 0.9, 0.3, 0.7],
    "sex":        [0.0, 0.0, 0.0, 1.0, 1.0, 1.0],
    "income_ok":  [1.0, 1.0, 0.0, 1.0, 0.0, 0.0],
})

dataset = BinaryLabelDataset(
    df=df,
    label_names=["income_ok"],
    protected_attribute_names=["sex"],
    favorable_label=1.0,
    unfavorable_label=0.0,
)

privileged_groups = [{"sex": 1.0}]
unprivileged_groups = [{"sex": 0.0}]
```

Validation rules to check before metrics:

- `df.isna().any().any()` must be false.
- Every column must be castable to `float64`. Encode strings before `BinaryLabelDataset`, or use `StandardDataset` for one-hot/mapping behavior.
- `label_names` and `protected_attribute_names` must name existing columns.
- The label column must contain only the two declared binary labels.
- The protected group dictionaries must use the encoded values found in `dataset.protected_attributes`, not the original strings unless the dataset kept numeric strings converted to floats.

## Group dictionary semantics

Metrics accept `privileged_groups` and `unprivileged_groups` as `list[dict]`.

- Keys are protected attribute names, for example `"sex"`, `"race"`, or `"age"`.
- Values are encoded protected attribute values in the dataset, usually `1.0` for privileged and `0.0` for unprivileged after `StandardDataset` mapping.
- Key-value pairs inside one dictionary are combined with **AND**.
- Multiple dictionaries in a list are combined with **OR**.

Example: `[{"sex": 1.0, "age": 1.0}, {"race": 1.0}]` means `(sex == 1 AND age == 1) OR (race == 1)`.

Use the dataset itself as the authority:

```python
print(dataset.protected_attribute_names)
print(dataset.privileged_protected_attributes)
print(dataset.unprivileged_protected_attributes)
print(dataset.convert_to_dataframe()[0].head())
```

## Label and score conventions

- `favorable_label` is the positive or beneficial outcome for the fairness definition. In many examples this is `1.0`, but some built-in datasets invert the human-readable meaning before mapping.
- `unfavorable_label` is the negative or harmful outcome.
- `BinaryLabelDatasetMetric` uses the dataset labels.
- `ClassificationMetric` treats the first dataset as ground truth and the second as predictions. The predicted dataset's `labels` hold hard predictions; its `scores` can hold calibrated probabilities or confidence scores when generalized confusion metrics or postprocessing algorithms need them.
- If you build predictions manually, deep-copy the true dataset first and change only `labels` and `scores`.

## Built-in legacy dataset wrappers

Legacy wrappers load public tabular datasets into `StandardDataset` or `RegressionDataset` subclasses. They are useful for real workflows but are not reliable smoke tests because the raw files are not bundled in a base package installation and some workflows require data-use acceptance or network access.

| Wrapper | Dataset type | Default label / favorable class | Default protected attributes / privileged classes | Raw-data caveat |
| --- | --- | --- | --- | --- |
| `AdultDataset` | `StandardDataset` | `income-per-year`, favorable `>50K` variants | `race=White`, `sex=Male` | Requires Adult train/test/name files in the package raw-data directory; drops missing `?` rows by default and drops `fnlwgt` unless kept as weights/features. |
| `GermanDataset` | `StandardDataset` | `credit`, favorable `1` (good credit) | derived `sex=male`, `age > 25` | Requires German credit files; derives `sex` from personal status and drops `personal_status` by default. |
| `CompasDataset` | `StandardDataset` | `two_year_recid`, favorable `0` (no recidivism) | `sex=Female`, `race=Caucasian` | Requires COMPAS CSV; applies the same default screening filters encoded in the wrapper. |
| `BankDataset` | `StandardDataset` | `y`, favorable `yes` | `age` where `25 <= age < 60` | Requires the Bank Marketing CSV extracted from its archive; treats `unknown` as missing. |
| `MEPSDataset19`, `MEPSDataset20`, `MEPSDataset21` | `StandardDataset` | `UTILIZATION`, favorable `>= 10 visits` | `RACE=White` | Requires converted MEPS CSV files (`h181.csv` for panels 19/20, `h192.csv` for panel 21); the data provider's terms and external conversion process are outside the base package. |
| `LawSchoolGPADataset` | `RegressionDataset` | `zfygpa` regression score | `race=white`, `gender=male` | Reads LSAC data through the package's sklearn dataset helper; network/cache behavior may apply and this was not verified in the base CPU environment. |

If a task only needs AIF360 mechanics, prefer the synthetic in-memory pattern. If a task needs a real built-in dataset, first make the raw-data acquisition and legal/usage assumptions explicit, then instantiate the wrapper and immediately inspect the encoded protected/label values.

## `StandardDataset` for custom raw pandas data

Use `StandardDataset` when the raw DataFrame contains strings/categoricals that should be encoded consistently:

```python
from aif360.datasets import StandardDataset

std = StandardDataset(
    df=raw_df,
    label_name="approved",
    favorable_classes=["yes"],
    protected_attribute_names=["sex"],
    privileged_classes=[["male"]],
    categorical_features=["job", "education"],
    features_to_drop=["record_id"],
)
```

The resulting dataset is a `BinaryLabelDataset`; labels are mapped to favorable/unfavorable binary values and protected attributes are mapped according to `privileged_classes`. Use `metadata` with `label_maps` or `protected_attribute_maps` if later reporting needs human-readable values.

## Splitting, copying, and dataframe export

- `dataset.split([0.7], shuffle=True, seed=...)` returns train/test partitions with features, labels, scores, protected attributes, weights, and instance names partitioned consistently.
- `dataset.copy(True)` makes a deep copy. Use this before mutating labels/scores for prediction datasets.
- `dataset.align_datasets(other)` reorders another dataset's features, labels, scores, and protected attributes to match names when the same schema appears in a different order.
- `dataset.convert_to_dataframe(de_dummy_code=True)` can recover a readable pandas view and attributes dictionary for debugging encoded values.
