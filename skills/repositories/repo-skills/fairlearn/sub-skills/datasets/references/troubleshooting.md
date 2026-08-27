# Dataset troubleshooting

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Loader hangs or fails with network error | Dataset is fetched from an OpenML-style source and is not cached. | Use an approved network/cache, set `data_home`, or avoid download and use synthetic data. |
| Disk fills during dataset loading | Large dataset such as ACSIncome was downloaded to the default cache. | Set `data_home` to a controlled location and remove stale cache files if appropriate. |
| `fetch_acs_income(states=[...])` raises `ValueError` | Invalid state abbreviation. | Use uppercase two-letter abbreviations for states and `PR`; validate state list before downloading. |
| `DataFairnessWarning` from `fetch_boston` | Expected warning about known fairness issues. | Keep the warning in the report; set `warn=False` only if the user explicitly understands and wants suppression. |
| `return_X_y=True` output lacks Bunch fields | Expected behavior: returns `(data, target)` directly. | Use `return_X_y=False` when `DESCR`, `feature_names`, `categories`, or `frame` are needed. |
| `as_frame=False` output dtypes are object arrays | Mixed numeric/categorical/string columns were converted to numpy. | Use `as_frame=True` for preprocessing and sensitive-feature selection. |
| Sensitive-feature column is missing after preprocessing | The user selected/encoded columns before saving the sensitive feature. | Extract `A = X[column]` before dropping/encoding columns, and split `X`, `y`, and `A` together. |

## No-network diagnostic

```bash
python sub-skills/datasets/scripts/preview_dataset_loaders.py
```

## Single-loader download diagnostic

```bash
python sub-skills/datasets/scripts/preview_dataset_loaders.py --download acs-income --states CA --data-home /tmp/fairlearn-data
```

Use a small or cached loader first before attempting ACSIncome across all states.
