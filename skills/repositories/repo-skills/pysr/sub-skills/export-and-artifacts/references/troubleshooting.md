# Export and artifact troubleshooting

Use this table after reading the export or reload reference that matches the user's workflow.

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `model.equations_` is missing or `None` | The model has not completed a fit, was reset, or was loaded without a valid CSV/checkpoint. | Fit the model, or reload with `PySRRegressor.from_file(run_directory=...)` from a run directory containing a hall-of-fame CSV or checkpoint. |
| The selected equation is not the one the user expected | `model_selection` is choosing the default row; the printed `pick` arrow is a heuristic. | Inspect the full DataFrame and pass `index=` to `get_best`, `predict`, `sympy`, `latex`, `jax`, or `pytorch`. Consider `model_selection="accuracy"` for the minimum-loss row. |
| `model_selection="score"` or `"best"` behaves like accuracy | The `score` column is absent, such as when score calculation is unavailable for the current loss scale. | Use explicit indices or `model_selection="accuracy"`; do not claim score-based selection occurred. |
| `predict` works for one row but not another | The selected row contains an operator that cannot be translated through the current SymPy/NumPy mapping. | Add or correct `extra_sympy_mappings`, call `model.refresh()`, then retry with the same index. |
| `predict`, `sympy`, or `latex` fails after a custom operator fit | The Julia search operator has no Python/SymPy mapping, or the mapping uses NumPy instead of SymPy-compatible functions. | Map the operator name string in `extra_sympy_mappings`. Use SymPy functions or a `sympy.Function` placeholder. Refresh after setting it. |
| `model.jax()` raises a missing function mapping error | A custom SymPy function has no JAX mapping or JAX is not installed. | Install/check JAX if needed, then set `extra_jax_mappings={SymPyFunction: "jnp.func"}` or a JAX-compatible lambda string and refresh. |
| `model.pytorch()` raises a missing function mapping error | A custom SymPy function has no Torch mapping or PyTorch is not installed. | Install/check PyTorch if needed, then set `extra_torch_mappings={SymPyFunction: torch.func}` and refresh. |
| JAX/Torch export uses the wrong input columns | Feature selection or DataFrame column order changed between fit and export. | Use the same feature order as fit. When reloading from CSV, pass `feature_names_in` and `selection_mask` from the original run. |
| `latex_table` output does not compile in a paper | The returned table assumes packages such as `booktabs` and `breqn`, or a long equation needs a display-math environment. | Include the preamble lines from the returned string or adapt the table to the target document style. Use lower precision or selected indices for compact tables. |
| `latex`, `sympy`, `jax`, or `pytorch` reports that the expression spec does not support the export | The model uses a non-default expression spec such as `TemplateExpressionSpec`. | Route to `../structured-expressions/`. Use component strings or Julia expressions; do not promise standard symbolic/backend exports. |
| A custom objective's printed equation does not match the evaluated formula | The objective reinterprets or manipulates the tree outside the standard export path. | Explain that exports describe the raw searched tree. The objective author must provide matching decoding/evaluation logic. |
| `PySRRegressor.from_file(equation_file=...)` fails | The old equation-file loading API is deprecated. | Use `PySRRegressor.from_file(run_directory=...)`, where the directory contains the CSV/checkpoint files. |
| `from_file` says operator configuration is required | No checkpoint is present, so PySR is reconstructing from CSV only. | Provide `operators` or `binary_operators`/`unary_operators`, plus `n_features_in`; also pass feature names, selection mask, output count, and mappings when needed. |
| `from_file` cannot find a hall-of-fame file | The run directory is wrong, the search ended before the first CSV write, or only multi-output numbered files exist. | Use the directory that directly contains `checkpoint.pkl` or `hall_of_fame*.csv`. For multi-output runs, verify `hall_of_fame_output1.csv` and related files exist. |
| Checkpoint load fails with an unsupported schema error | The checkpoint was written by an incompatible PySR version or corrupted. | Prefer loading with the same PySR version that created it. If CSVs are available, reconstruct from CSV with full operator/feature metadata. |
| Reloaded custom-operator model lost mappings | Lambda-valued mappings are not preserved in the checkpoint. | Re-supply `extra_sympy_mappings` and `extra_torch_mappings` at `from_file` time or with `set_params`, then refresh. |
| Reloaded model has no JAX/Torch columns | JAX/Torch export columns are stripped from checkpoints and regenerated on demand. | Call `model.jax()` or `model.pytorch()` after installing optional dependencies and setting custom mappings. |
| Artifacts are not under the expected `outputs/` directory | The model used `output_directory`, `run_id`, `temp_equation_file`, or an in-memory warm-started state. | Inspect `model.output_directory_` and `model.run_id_`; compute the run directory from those attributes. |
| Temporary equation files disappeared from the default output location | `temp_equation_file=True` writes to a temporary output directory instead of the default outputs directory. | Use `model.output_directory_` and `model.run_id_`; set `tempdir` if a stable temporary parent is needed. |
| A partially running job has a stale or unparsable CSV | The CSV was read while being updated, or the first iteration has not finished. | Try the `.bak` file, wait for another iteration, or inspect with `scripts/inspect_equation_artifacts.py` to confirm required fields are present. |
| TensorBoard log directory is empty | Optional logging packages are missing, the run was too short, `log_interval` is too large, or the directory is not writable. | Check optional dependencies, reduce `log_interval`, run enough iterations, and use a writable non-sensitive `log_dir`. |
| TensorBoard creates multiple event files | Repeated fits without warm start can create separate logger instances. | Use `warm_start=True` only when the same search state should continue; otherwise treat each event file as a separate run segment. |

## Minimal diagnosis snippets

Inspect the available equation rows:

```python
print(model.equations_)
print(model.get_best())
```

Force a specific row:

```python
row = 2
print(model.get_best(index=row))
y_hat = model.predict(X_test, index=row)
```

Refresh exports after changing mappings:

```python
model.set_params(extra_sympy_mappings={"op": sympy_op})
model.refresh()
```

Find the run directory from an in-memory model:

```python
from pathlib import Path
run_directory = Path(model.output_directory_) / model.run_id_
print(run_directory)
```

Use CSV inspection before importing PySR or starting Julia:

```bash
python scripts/inspect_equation_artifacts.py run/hall_of_fame.csv --sort loss --limit 10
```
