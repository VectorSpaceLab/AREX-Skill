# Data-quality troubleshooting

## `IPython.display` missing

`pandas_dq` imports `IPython.display`. Install `ipython` even if the user is not running a notebook.

## pandas 3 compatibility

If `data_cleaning_suggestions` fails with:

```text
AttributeError: 'DataFrame' object has no attribute 'applymap'
```

use pandas 2.x. AutoViz version `0.1.905` can install with newer package metadata, but `pandas_dq` 1.29 still expects `DataFrame.applymap`.

## Duplicate-row warnings

A warning such as `There are N duplicate rows in your dataset` is diagnostic, not automatically fatal. Decide with the user whether duplicate removal is appropriate for the domain.

## Mixed-type columns

AutoViz and `pandas_dq` can flag object columns with multiple Python types. Convert them explicitly before plotting or cleaning when the desired type is known.

## Infinite values

Infinite values in numeric columns can be identified and replaced or removed. `FixDQ` is the reusable transformer path if the same rule must apply to train and test sets.

## Target handling

- Use a string target for single-target supervised data.
- Avoid multi-label lists unless the user accepts that AutoViz visualizes only the first target.
- If the report complains about missing target variables, verify exact column spelling and dtype.

## Dependency cross-check

If data-quality functions fail at import time, run the root install checklist:

```bash
python -m pip check
python - <<'PY'
from autoviz import FixDQ, data_cleaning_suggestions
print("DQ imports OK")
PY
```
