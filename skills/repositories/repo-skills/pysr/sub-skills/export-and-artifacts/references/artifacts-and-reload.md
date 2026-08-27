# Artifacts and reload reference

PySR writes two kinds of persisted state during a fit: continuously updated equation CSVs and a checkpoint pickle. Use both when available, but design user workflows so the CSV plus explicit model-construction code remains enough to recover equations.

## Run directory layout

A PySR run is addressed by:

```python
run_directory = Path(model.output_directory_) / model.run_id_
```

Current PySR uses this conceptual layout:

```text
<output_directory>/<run_id>/
  hall_of_fame.csv
  hall_of_fame.csv.bak
  checkpoint.pkl
```

For multi-output fits, the hall-of-fame files are numbered:

```text
<output_directory>/<run_id>/
  hall_of_fame_output1.csv
  hall_of_fame_output1.csv.bak
  hall_of_fame_output2.csv
  hall_of_fame_output2.csv.bak
  checkpoint.pkl
```

PySR often reads the `.bak` CSV first when it exists because the search updates backup files during a run. A missing CSV usually means the search ended before completing its first equation-table write.

## Controlling output paths

Constructor parameters:

```python
model = PySRRegressor(
    output_directory="outputs",  # default when not temporary
    run_id="experiment_001",     # default is generated
    temp_equation_file=False,
)
```

Rules:

- `output_directory` chooses the parent directory for all run artifacts.
- `run_id` chooses the run subdirectory. Supply it when you need reproducible file names across scripts or job restarts.
- If `temp_equation_file=True`, PySR creates a temporary output directory and asserts that `output_directory` is not also set. Use `tempdir` to choose the temporary parent.
- With `warm_start=True`, PySR expects the same `output_directory_` and `run_id_` to remain attached to the in-memory model across repeated fits.
- The deprecated `equation_file_` property and `equation_file=` loading style are not current. Use `output_directory_`, `run_id_`, and `from_file(run_directory=...)`.

## Hall-of-fame CSV contents

The CSV is the easiest artifact to inspect and archive. It stores at least:

| Column | Meaning |
| --- | --- |
| `Complexity` / `complexity` | Expression tree complexity. |
| `Loss` / `loss` | Training loss for the row. |
| `Equation` / `equation` | Equation string in PySR/SymbolicRegression syntax. |

After PySR loads a CSV into a model, it normalizes column names to lowercase and recomputes export columns such as `sympy_format`, `lambda_format`, `score`, `jax_format`, or `torch_format` according to the model parameters.

Use the bundled helper for safe, PySR-free CSV inspection:

```bash
python scripts/inspect_equation_artifacts.py run/hall_of_fame.csv --sort loss --limit 5
python scripts/inspect_equation_artifacts.py run/hall_of_fame.csv --format json
```

The helper reads only the CSV, checks for required equation columns, and summarizes row positions, loss, complexity, score, and equation strings. It does not import PySR, initialize Julia, evaluate equations, or write files.

## Checkpoint pickle contents and limits

`checkpoint.pkl` stores a serialized `PySRRegressor` state. Loading a checkpoint is convenient because the model already knows its feature names, feature-selection mask, operators, output count, and many constructor parameters.

Cautions:

- Checkpoints include a schema version. A checkpoint written by an incompatible PySR version can fail to load with an unsupported schema error.
- JAX and PyTorch export columns are stripped before pickling and are regenerated after loading when requested.
- Lambda-valued mappings such as `extra_sympy_mappings` and `extra_torch_mappings` cannot be pickled reliably and are removed from the serialized instance. Re-supply them at load time.
- Checkpoints from non-default expression specs may depend on dynamic objects and are not as portable as plain CSV plus explicit reconstruction code.
- Treat checkpoints as version-sensitive runtime conveniences, not long-term standalone scientific artifacts.

## Reloading with `PySRRegressor.from_file`

Use:

```python
from pysr import PySRRegressor

model = PySRRegressor.from_file(
    run_directory="outputs/my_run",
    # Optional overrides or mappings:
    extra_sympy_mappings={"op": sympy_op},
)
```

### When `checkpoint.pkl` exists

PySR loads the checkpoint and applies any `**pysr_kwargs` overrides with `set_params`. Do not pass `binary_operators`, `unary_operators`, `operators`, or `n_features_in` in this case; those are already in the checkpoint. If equations are absent, PySR refreshes them from the run directory.

Common checkpoint reload for custom operators:

```python
model = PySRRegressor.from_file(
    run_directory="outputs/my_run",
    extra_sympy_mappings={"safe_log": sympy_safe_log},
)
```

### When only CSV or backup CSV exists

PySR reconstructs a model from `hall_of_fame.csv` or `hall_of_fame.csv.bak`. In this fallback, you must provide enough original model metadata to parse and evaluate equations:

```python
model = PySRRegressor.from_file(
    run_directory="outputs/my_run",
    n_features_in=5,
    feature_names_in=["f0", "f1", "f2", "f3", "f4"],
    binary_operators=["+", "*", "/", "-", "^"],
    unary_operators=["cos"],
    # or use operators={1: [...], 2: [...]}
)
```

CSV fallback requirements:

- Provide `operators` or legacy `binary_operators`/`unary_operators`.
- Provide `n_features_in`.
- Provide `feature_names_in` if the equation strings use named variables beyond the default `x0`, `x1`, ... names.
- Provide `selection_mask` if feature selection was used.
- Provide `nout` for multi-output runs.
- Re-supply `extra_sympy_mappings` for custom operators before prediction or symbolic export.

### Refreshing after reload

Use `model.refresh(run_directory=...)` to re-read artifacts and rebuild export columns after changing mappings or optional export settings:

```python
model.set_params(extra_sympy_mappings={"op": sympy_op})
model.refresh(run_directory="outputs/my_run")
```

## Partial runs

For long-running jobs, the CSV may be useful before the final checkpoint is updated. Safe partial-run pattern:

1. Inspect the current `hall_of_fame.csv` or `.bak` with the bundled helper.
2. If you need PySR export/evaluation, call `from_file(run_directory=...)` with full operator and feature metadata when no checkpoint exists.
3. Use explicit row indices for any selected equation so later table updates do not silently change which row is evaluated.
4. Archive the CSV and the model-construction code together.

Do not assume a partially written row is valid if a CSV read fails or required fields are blank.

## TensorBoard logging

PySR exposes TensorBoard logging through `TensorBoardLoggerSpec`:

```python
from pysr import PySRRegressor, TensorBoardLoggerSpec

logger_spec = TensorBoardLoggerSpec(
    log_dir="logs/run",
    log_interval=10,
    overwrite=False,
)

model = PySRRegressor(
    binary_operators=["+", "*", "-", "/"],
    logger_spec=logger_spec,
)
model.fit(X, y)
```

Fields:

| Field | Meaning |
| --- | --- |
| `log_dir` | Base TensorBoard event directory. If `overwrite=False`, new numbered directories may be used instead of overwriting. |
| `log_interval` | Search-step interval for writing logs. |
| `overwrite` | Whether to overwrite an existing log directory. |

PySR logs hyperparameters and search summaries such as Pareto volume and minimum loss. Viewing logs requires a TensorBoard reader, for example:

```bash
tensorboard --logdir logs/
```

Logging caveats:

- TensorBoard support requires optional logging packages on the Python/Julia side.
- Very short searches or a large `log_interval` may produce few or no events.
- With `warm_start=True`, repeated fits can reuse the same logger; without warm start, later fits may create separate event files.
- Use a writable, non-sensitive log directory. Logs are experiment artifacts and may include parameter strings.
