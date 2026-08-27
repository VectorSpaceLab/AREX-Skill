# PySR API Index

Use this index to choose the nearest sub-skill before giving detailed API advice.

| API or concept | Owner | Notes |
| --- | --- | --- |
| `PySRRegressor(...)` ordinary constructor options (`niterations`, operators, model selection, batching basics) | `sub-skills/fit-and-diagnose/` | Use for standard searches and Pareto-front interpretation. |
| `PySRRegressor.fit(X, y, weights=..., variable_names=..., X_units=..., y_units=...)` | `fit-and-diagnose`, plus `customization-and-constraints` for units | Data shape, names, weights, and fit loop live in fit guidance; unit semantics live in customization. |
| `model.equations_`, `get_best`, `predict(index=...)`, `sympy`, `latex` | `export-and-artifacts` | Fit guidance may mention them, but export owner covers row selection and artifact semantics. |
| `jax`, `pytorch`, `output_jax_format`, `output_torch_format` | `export-and-artifacts` | Optional dependencies and mapping layers are required. |
| `binary_operators`, `unary_operators`, `operators` | `customization-and-constraints` | Includes arity, custom Julia definitions, type stability, and mappings. |
| `elementwise_loss`, `loss_function`, `loss_function_expression`, `loss_scale` | `customization-and-constraints` | Full objective and template-expression objective differences matter. |
| `constraints`, `nested_constraints`, complexity knobs, dimensional constraints | `customization-and-constraints` | Use finite reachable constraints and unit syntax. |
| `TemplateExpressionSpec`, `ExpressionSpec`, template guesses | `structured-expressions` | Includes parameters, vector-valued residual templates, `D`, and export caveats. |
| `TensorBoardLoggerSpec`, output directories, checkpoints, `from_file` | `export-and-artifacts` | Use for persistent run artifacts and logging. |
| `parallelism`, `procs`, `cluster_manager`, `PYTHON_JULIACALL_THREADS`, `input_stream`, deterministic settings | `runtime-and-scaling` | Must often be set before import or before a long run starts. |
| `python -m pysr`, CLI test subsets | `runtime-and-scaling` | CLI is small: deprecated `install` and `test` wrapper. |
| Mutation and plugin configuration objects | `customization-and-constraints` | Advanced tuning objects; do not treat legacy weight knobs as the only path. |
