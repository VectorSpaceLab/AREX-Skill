# Data-quality workflows

## Report-only workflow

Use `data_cleaning_suggestions` when the user wants a diagnostic report but not a transformer:

```python
import pandas as pd
from autoviz import data_cleaning_suggestions

report = data_cleaning_suggestions(df, target="target")
```

Use `target=""` or `target=None` when there is no supervised target.

## Transformer workflow

Use `FixDQ` when the user wants a reusable fit/transform cleaning step:

```python
from autoviz import FixDQ

fixer = FixDQ(
    quantile=0.87,
    cat_fill_value="missing",
    num_fill_value=9999,
    rare_threshold=0.01,
    correlation_threshold=0.9,
)
clean_train = fixer.fit_transform(train_df, target="target")
clean_test = fixer.transform(test_df)
```

The exact methods come from `pandas_dq.Fix_DQ`; inspect the installed object when writing executable code in a target environment.

## Issues AutoViz highlights

The AutoViz `FixDQ` docstring describes checks for:

- ID columns
- zero-variance columns
- rare categories
- infinite values
- mixed data types
- outliers
- high cardinality features
- highly correlated features
- duplicate rows
- duplicate columns
- skewed distributions
- imbalanced classes
- target leakage

## Integration with EDA

`AutoViz_Class.AutoViz_Main` calls `data_cleaning_suggestions` before plotting. If a user asks why no plots appear, first check whether the data-quality report failed.

After using `FixDQ`, rerun AutoViz on the cleaned DataFrame with `filename=""` and `dfte=clean_df`.
