# Troubleshooting

## Purpose

Read this when NeuralForecast import, install, validation, tuning, or
serialization fails and you need the fastest next check.

## First response checklist

1. Run `python -m pip check` in the prepared environment.
2. Run `python -I -c "import neuralforecast; print(neuralforecast.__version__)"`.
3. If the issue is a panel/data problem, run `scripts/validate_panel.py`.
4. If the issue is a workflow smoke, run `scripts/core_smoke.py`.
5. If the issue is loss selection, run `scripts/check_losses.py`.
6. If the issue is Auto* configuration, run `scripts/check_auto_config.py`.

## Cross-cutting failure surfaces

| Symptom | Likely cause | Next action |
| --- | --- | --- |
| `ModuleNotFoundError: neuralforecast` | Package not installed in the target environment | Reinstall with `pip install neuralforecast` or `pip install -e .` from the checkout. |
| `pip check` fails | Dependency mismatch after install | Fix the environment before trusting any import. |
| `TimeLLM` or `xLSTM` import but feature flags are off | Optional extras missing | Install the optional packages only if the user really needs those models. |
| `torch.cuda.is_available() == False` on a GPU host | CPU-only torch wheel or incompatible CUDA runtime | Use the correct torch/CUDA combination or stay on the CPU path. |
| `Found missing values in [...]` | Nulls in target, static, or exogenous columns | Clean the dataframe and rerun `scripts/validate_panel.py`. |
| `There are missing combinations` | `futr_df` does not cover all needed series/date pairs | Rebuild the future frame with every required row. |
| `Set val_size>0 or provide a val_df if early stopping is enabled.` | Early stopping without a validation window | Add `val_size` or `val_df`. |
| `input_size` missing in Auto* config | Search config did not define a required key | Fix the search space and rerun `scripts/check_auto_config.py`. |
| Ray/GPU oversubscription or DDP crashes | Too many GPUs per trial or inconsistent resource hints | Use a conservative `RayOptions` config and keep trials small. |
| Spark path errors or scaling errors in distributed mode | Unsupported local/static scaling or bad `partitions_path` | Recheck distributed constraints and writable storage. |
| Save/load path exists unexpectedly | Reused output directory without overwrite | Pass `overwrite=True` only when replacement is intended. |

## Data and exogenous errors

- Missing `unique_id`, `ds`, or `y` means the panel schema is wrong.
- Missing future features usually means the `futr_df` frame is incomplete.
- Categorical errors usually mean the declared cardinalities are too small.
- Negative `sample_weight` values are invalid.
- Unsorted rows usually mean the input should be sorted before fit or should
  pass through `scripts/validate_panel.py`.

## Model-selection errors

- `n_series` missing on a multivariate model means the model family was chosen
  before the data shape was known.
- Exogenous lists on unsupported families usually mean the wrong model was
  chosen for the task.
- Optional-dependency models (`TimeLLM`, `xLSTM`) should be treated as optional
  until their extra packages are installed and the feature flags are true.

## Loss and interval errors

- Duplicate quantile or level warnings are usually harmless, but they point to a
  duplicated configuration.
- Mismatched `loss` / `valid_loss` families should be corrected before training.
- Distribution losses paired with point-loss validation usually need a point
  `valid_loss`.

## Deployment and extension errors

- Load failures after a version bump often indicate a stale serialized artifact.
- ONNX and MLflow failures are usually optional-dependency issues, not core
  NeuralForecast failures.
- Docs-generation scripts are maintainer-only; do not use them as runtime smoke
  checks.

## When to stop

Stop and ask for a new environment, backend, or optional dependency when the
user's requested workflow truly depends on hardware or packages that are not
present. Do not silently downgrade a required capability to a CPU-only or
optional path without saying so.
