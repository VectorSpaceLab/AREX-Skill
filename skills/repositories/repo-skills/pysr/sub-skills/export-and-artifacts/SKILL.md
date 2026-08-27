---
name: export-and-artifacts
description: "Export PySR equations, inspect hall-of-fame artifacts, reload
  saved runs, and configure optional logging."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# PySR export and artifacts

Use this sub-skill when the user already has, or is about to persist, fitted PySR equations and needs to choose rows, export equations, inspect run artifacts, reload a run, or configure search logging.

## Route here for

- Reading `model.equations_`, `model.get_best()`, selected rows, and `model_selection` behavior.
- Calling `predict(index=...)`, `sympy(index=...)`, `latex(index=...)`, `latex_table(...)`, `jax(index=...)`, or `pytorch(index=...)`.
- Explaining `lambda_format`, `sympy_format`, optional `jax_format`/`torch_format`, and custom export mappings.
- Finding or inspecting `hall_of_fame.csv`, `hall_of_fame_output*.csv`, backup CSVs, and `checkpoint.pkl` under a PySR run directory.
- Reloading with `PySRRegressor.from_file(run_directory=...)` from checkpoint or CSV.
- Choosing `output_directory`, `run_id`, `temp_equation_file`, or `TensorBoardLoggerSpec` settings.

## Route away from here

- If the user has not fit a model yet, start with `../fit-and-diagnose/` for fitting, operator basics, and search-quality diagnosis.
- If export fails because a custom Julia operator has no Python/SymPy/JAX/Torch equivalent, use this sub-skill for the export mapping and `../customization-and-constraints/` for the operator/loss design.
- If the model uses `TemplateExpressionSpec`, use this sub-skill for artifact/reload mechanics but read `../structured-expressions/` before promising SymPy, LaTeX, JAX, or PyTorch export.
- If the issue is Julia startup, parallelism, Slurm, Docker/Apptainer, or installation, route to `../runtime-and-scaling/`.

## Required references

1. Read `references/export-reference.md` for API behavior, row selection, and backend export mappings.
2. Read `references/artifacts-and-reload.md` before giving file-layout, checkpoint, partial-run, `from_file`, `temp_equation_file`, or TensorBoard advice.
3. Read `references/troubleshooting.md` when an export, prediction, reload, or artifact lookup fails.
4. Use `scripts/inspect_equation_artifacts.py --help` to inspect a hall-of-fame CSV without importing PySR.

## Safe operating pattern

1. Identify whether the user has an in-memory fitted model, a run directory, a CSV, or only printed equations.
2. If in memory, inspect `model.equations_` first. For single-output models it is a DataFrame; for multi-output models it is a list of DataFrames.
3. Select rows deliberately. Use `model.get_best()` for the current `model_selection`, or pass `index=` to `get_best`, `predict`, `sympy`, `latex`, `jax`, and `pytorch` when the user wants a specific Pareto-front row.
4. For custom operators, make sure `extra_sympy_mappings` exists before NumPy/SymPy/LaTeX/prediction, and add `extra_jax_mappings` or `extra_torch_mappings` before those optional backends.
5. For persisted runs, prefer `PySRRegressor.from_file(run_directory=...)`. Treat the CSV plus the model-construction code as the durable artifact; treat the pickle checkpoint as convenient but version-sensitive.
6. Do not assume optional dependencies are installed. JAX, PyTorch, TensorBoard, and template-expression exports require separate capability checks.
