# Focused API reference: ordinary fitting and diagnosis

This reference lists the PySR APIs most often needed for plain fitting. It is not a full constructor reference; route advanced customization, export/reload, and runtime scaling to sibling sub-skills.

## `PySRRegressor(...)` starter parameters

| Parameter | Typical use | Fit-and-diagnose guidance |
| --- | --- | --- |
| `binary_operators` | Binary operators searched by evolution. | Start small: `['+', '-', '*']` for many baselines. Add `/` or other operators only with a domain reason. |
| `unary_operators` | Unary operators such as `sin`, `cos`, `exp`. | Keep empty unless the target family plausibly needs them. Custom Julia operator strings route to `customization-and-constraints`. |
| `operators` | Generic operator dictionary by arity. | Advanced/n-ary operator control; route to `customization-and-constraints` unless the task is already using the modern API knowingly. |
| `niterations` | Number of outer search iterations. | Short run for setup; longer run once data/operators are validated. |
| `timeout_in_seconds` | Wall-clock bound for the search. | Useful for agents and notebooks. A timeout can still return a partial front. |
| `max_evals` | Bound on total expression evaluations. | Use for compute-matched comparisons; do not approximate it as `niterations * populations * population_size`. |
| `maxsize` | Maximum expression complexity/node count. | Increase when true equations require many terms or variables. Too small yields constants or underfit rows. |
| `maxdepth` | Maximum expression depth. | Optional stricter guard; can exclude valid nested forms if too small. |
| `warmup_maxsize_by` | Fraction of training over which maxsize ramps up. | Useful when early complex expressions dominate; leave off for simple baselines. |
| `model_selection` | Default row selection for `predict`, `sympy`, and `latex`. | Use `best` for balanced reports, `accuracy` for minimum loss, `score` for the sharpest score heuristic. |
| `denoise` | Gaussian-process denoising before search. | Try for noisy low/medium-dimensional tabular data; validate on original or held-out data. |
| `select_k_features` | Python feature selection before the Julia search. | Use for high-dimensional tabular data when domain feature engineering is unavailable. |
| `batching`, `batch_size` | Mini-batch evaluation during mutations. | Mention for large/noisy data, but detailed runtime trade-offs belong in `runtime-and-scaling`. |
| `random_state`, `deterministic`, `parallelism` | Reproducibility controls. | Full deterministic runs require `deterministic=True`, a fixed `random_state`, and `parallelism='serial'`; otherwise expect stochastic variation. |
| `input_stream` | Julia-side input monitoring. | Use `input_stream='devnull'` if stdin handling causes hangs in embedded environments. |
| `output_directory`, `run_id`, `temp_equation_file` | Where equation/checkpoint artifacts are written. | For artifact inspection, route to `export-and-artifacts`. For quick smoke checks, `temp_equation_file=True` avoids persistent hall-of-fame files. |

## `fit` signature and behavior

Focused signature:

```python
model.fit(
    X,
    y,
    *,
    Xresampled=None,
    weights=None,
    variable_names=None,
    complexity_of_variables=None,
    X_units=None,
    y_units=None,
)
```

Key behavior:

- `X`: array-like or pandas DataFrame, shape `(n_samples, n_features)`.
- `y`: array-like or pandas object, shape `(n_samples,)` or `(n_samples, n_outputs)`.
- `Xresampled`: optional resampled feature matrix used when denoising should produce denoised targets on a different grid.
- `weights`: same shape as `y`; each entry weights that target value for built-in losses.
- `variable_names`: feature names for array inputs. DataFrame columns take precedence.
- `complexity_of_variables`: can be supplied at construction or `fit`, not both.
- `X_units`/`y_units`: dimensional constraints route to `customization-and-constraints`.
- After fitting, `model.equations_` is populated and the model can be printed.

Validation notes:

- Spaces in feature names are normalized to underscores with a warning. Safer names avoid spaces and special characters from the start.
- Bad symbolic names can fail parsing. If the task contains names such as `Tr(Tij)` or `f{c}`, rename columns before fitting.
- If `select_k_features` is active, PySR stores a selection mask and updates feature names to the selected subset.
- If `warm_start=False`, a new `fit` resets previous equations. If `warm_start=True`, compatibility is required between runs.

## Pareto-front objects

`model.equations_` is a pandas DataFrame for one output or a list of DataFrames for multiple outputs. Common columns include:

| Column | Meaning |
| --- | --- |
| `equation` | Human-readable equation string from the backend. |
| `complexity` | Node/complexity count used for the Pareto front. |
| `loss` | Training loss for the row. |
| `score` | Heuristic improvement score; approximately the negative derivative of log loss with respect to complexity. |
| `sympy_format` | SymPy expression for rows that support SymPy export. |
| `lambda_format` | Callable form used by `predict`. |
| optional export columns | JAX/Torch or other export forms if requested and supported. Route details to `export-and-artifacts`. |

Treat this table as the primary diagnostic view. Rows with slightly higher loss and much lower complexity are often better scientific candidates than the lowest-loss row.

## Row-selection helpers

```python
row = model.get_best()          # selected by model.model_selection
row_i = model.get_best(index=i) # explicit row
```

Selection strategies:

- `accuracy`: row with the smallest `loss`.
- `score`: row with the largest `score`.
- `best`: row with the largest score among equations whose loss is close to the most accurate row; this is the default balance of simplicity and accuracy.

`model_selection` can be changed after fitting, for example:

```python
model.set_params(model_selection="accuracy")
print(model.sympy())
```

## Prediction and symbolic views

```python
y_pred = model.predict(X_new)          # default selected row
alt_pred = model.predict(X_new, index=i)
expr = model.sympy(index=i)
tex = model.latex(index=i, precision=4)
```

Important details:

- `predict` expects the same feature schema as `fit`. With DataFrames, PySR reorders by stored feature names where possible.
- For multi-output models, explicit `index` should be a list of row indices, one per output.
- If `predict` or `sympy` fails after custom operators, the usual cause is missing or wrong `extra_sympy_mappings`; route to `customization-and-constraints`.
- Template expression export support is limited; route template workflows to `structured-expressions`.

## Denoising and feature-selection API

```python
model = PySRRegressor(
    denoise=True,
    select_k_features=5,
    binary_operators=["+", "-", "*"],
)
model.fit(X, y, Xresampled=X_resampled)
```

- `denoise=True` preprocesses targets using a Gaussian-process denoising step. It can help with observational noise but adds cost and assumptions.
- `Xresampled` is only relevant to denoising; it controls where denoised targets are generated.
- `select_k_features=k` chooses a subset of input features before the symbolic regression backend starts. It is useful for high-dimensional tabular tasks but should be validated against domain knowledge and held-out data.
- When both are active, feature selection occurs before denoising in the fit preprocessing pipeline.

## Basic failure-safe configuration for agents

For short agent-run smoke tests, prefer a configuration like:

```python
model = PySRRegressor(
    binary_operators=["+", "-", "*"],
    unary_operators=[],
    niterations=1,
    populations=4,
    population_size=12,
    ncycles_per_iteration=10,
    maxsize=6,
    timeout_in_seconds=20,
    parallelism="serial",
    deterministic=True,
    random_state=0,
    progress=False,
    verbosity=0,
    input_stream="devnull",
    temp_equation_file=True,
)
```

This is for import/runtime smoke validation only. It is too small for real model discovery on most user data.
