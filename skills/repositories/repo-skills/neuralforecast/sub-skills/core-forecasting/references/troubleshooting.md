# Core Forecasting Troubleshooting

## Purpose

Read this when `fit`, `predict`, `cross_validation`, `predict_insample`,
`simulate`, `explain`, `save`, or `load` fails.

## Common failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `Set val_size>0 or provide a val_df if early stopping is enabled.` | Early stopping was requested without a validation window. | Add `val_size` or `val_df`. |
| `requires at least` in a short-series error | `input_size` plus horizon is larger than the available training history. | Reduce `input_size`, shorten the horizon, or enable the model's start-padding path when valid. |
| `There are missing combinations` | The future dataframe does not include every required series/date pair. | Rebuild `futr_df` for all required horizon rows. |
| `Dropped ... unused rows` | `futr_df` has extra rows. | Trim the future dataframe to the exact needed combinations. |
| Save/load path errors | Existing directory, wrong permissions, or stale bundle. | Use a writable path and pass `overwrite=True` only when replacement is intended. |
| Empty or odd `predict_insample` output | The model was not fitted the way the insample helper expects. | Refit, then rerun `predict_insample`. |
| Simulation or explanation error | Unsupported model family or bad data layout. | Switch to a supported model and recheck the panel schema. |

## Next checks

1. Confirm the panel schema with `../../scripts/validate_panel.py`.
2. Confirm the core workflow with `../../scripts/core_smoke.py`.
3. Confirm portability with `../../scripts/check_serialization.py`.

## When to stop

If the failure is really about missing future exogenous variables, categorical
cardinality, or data layout, route back to `data-and-exogenous`. If it is about
loss choice or interval construction, route to `probabilistic-losses`.
