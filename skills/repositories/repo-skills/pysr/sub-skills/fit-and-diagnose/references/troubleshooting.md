# Troubleshooting ordinary PySR fits

Use this table when a plain fit is slow, unhelpful, or failing. Route advanced custom-operator/loss/template/export/runtime issues to sibling sub-skills rather than patching them here.

## Search quality and speed

| Symptom | Likely cause | Action |
| --- | --- | --- |
| First import or first fit appears slow before equations print | Julia backend startup and compilation can dominate the first run in a process. | Wait for startup if this is the first run; keep the Python process alive for iterative experiments. For deeper startup diagnostics, use `runtime-and-scaling`. |
| Search runs but only constants appear | True equation may exceed `maxsize`, operators may be missing, target scale may make constants competitive, or data signal may be weak. | Check `X`/`y` alignment, add only missing plausible operators, increase `maxsize`, and inspect held-out loss. Do not simply add many operators at once. |
| Equations are too complex with tiny loss improvement | `model_selection='accuracy'` or over-large search space may be favoring overfit rows. | Inspect `complexity`, `loss`, and `score`; try `model_selection='best'`; report a simpler candidate if loss is similar. |
| Search is very slow on many columns | Too many features create a huge search space. | Use domain feature engineering, subsample columns, or set `select_k_features=k` for tabular data. Increase `maxsize` only if selected features still require many terms. |
| Search is very slow on many rows | Full-data evaluation is expensive, especially with noise. | Start with representative subsamples; use `batching=True` if broad row coverage is needed during evolution. Route detailed scaling to `runtime-and-scaling`. |
| A variable expected by the user is omitted | PySR rewards accuracy versus simplicity; the variable may not improve loss enough. | Validate feature relevance externally, increase budget/`maxsize` if justified, or route to `customization-and-constraints` for structural penalties. |
| Results vary between runs | Evolutionary search is stochastic, and parallelism adds nondeterminism. | Compare fronts across runs. For a deterministic smoke/comparison run, use `deterministic=True`, fixed `random_state`, and `parallelism='serial'`. |
| A search appears stuck after early improvement | Evolution can jump to new expression families late; lack of monotonic visible progress is normal. | If the setup is correct, use a longer bounded run. If setup is uncertain, stop and run a smaller diagnostic front first. |

## Data and validation failures

| Symptom | Likely cause | Action |
| --- | --- | --- |
| Shape error from `fit` | `X` is not 2D, `y` length does not match rows, or `weights` shape does not match `y`. | Ensure `X.shape == (n_samples, n_features)`, `len(y) == n_samples`, and `weights.shape == y.shape`. |
| Bad or surprising variable names in equations | DataFrame columns or `variable_names` contain spaces/special characters, or names were auto-generated as `x0`, `x1`, ... | Rename columns before fitting. Use simple names with letters, numbers, and underscores. Pass `variable_names` for NumPy arrays. |
| Invalid variable-name error | Names like function calls, braces, or symbolic-reserved forms cannot be parsed safely. | Replace names such as `Tr(Tij)` or `f{c}` with simple aliases, and keep a separate mapping for reporting. |
| Predictions use wrong columns | New data does not match the training feature schema, especially after DataFrame reordering or feature selection. | Pass a DataFrame with the same column names, or a NumPy array in the exact training order. If `select_k_features` was used, verify selected feature names on the model. |
| Feature selection picked unexpected columns | Tree-based preselection is heuristic and can be affected by collinearity/noise. | Compare with domain-selected columns, increase/decrease `k`, and evaluate candidate equations on held-out data. |
| Denoising changes the target behavior | Gaussian-process denoising added assumptions or used a resampled grid that changes the effective training problem. | Fit a baseline without denoising, validate on original observations, and report that denoising was used. |

## Prediction, SymPy, and LaTeX basics

| Symptom | Likely cause | Action |
| --- | --- | --- |
| `predict` fails after fitting with custom operators | Missing or incompatible SymPy mapping for the custom operator. | Route to `customization-and-constraints`; then set `extra_sympy_mappings` and refresh/reload equations as appropriate. |
| `sympy`/`latex` not available for an expression specification | Template or custom expression does not support ordinary export. | Route to `structured-expressions` for component inspection and manual reconstruction limits. |
| Chosen equation differs from expected lowest loss | `model_selection='best'` favors a balance of accuracy and simplicity rather than minimum loss. | Use `model_selection='accuracy'` or pass `index=` explicitly when evaluating/reporting a row. |
| `model.equations_` exists but artifact/reload questions arise | Front is in memory, while persisted hall-of-fame/checkpoint handling is a separate workflow. | Route to `export-and-artifacts` for durable files, reload, and export backends. |

## Operator and loss boundary cases

| Symptom | Likely cause | Action |
| --- | --- | --- |
| Domain errors or non-finite candidates dominate | A custom operator is not defined for all real inputs, or an operator creates invalid values on the data. | Prefer built-in protected operators where possible. For custom operators, route to `customization-and-constraints` and return typed NaNs for invalid domains. |
| MSE is dominated by large target values | Target spans orders of magnitude or has outliers. | Consider target transforms, weights, robust losses, or custom losses. Built-in weights are fit-level; custom loss design routes to `customization-and-constraints`. |
| Weighted fit with custom loss errors | Weighted `elementwise_loss` must accept `(prediction, target, weight)`. | Route to `customization-and-constraints` for exact Julia loss signatures. |
| Power/division creates uninterpretable expressions | Search space is too permissive. | Start without those operators, or route to `customization-and-constraints` for constraints and complexity shaping. |

## Warm-start pitfalls

| Symptom | Likely cause | Action |
| --- | --- | --- |
| Repeated `fit` unexpectedly resets the search | `warm_start=False` is the default. | Set `warm_start=True` only when deliberately continuing a compatible search. |
| Warm-start run errors or behaves strangely after parameter changes | Operators, feature shape/order, `maxsize`, expression specification, or precision changed. | Start a fresh model or reset state. Use warm-start only for compatible continuation, not for changing the scientific hypothesis. |
| Agent keeps paying startup cost on every tweak | Each tweak is launched in a fresh Python process. | Keep a long-lived Python process for interactive exploration. Route process/runtime planning to `runtime-and-scaling`. |

## Escalation rules

- **Escalate to `customization-and-constraints`** when the fix requires custom Julia code, custom losses, units, hard structural constraints, or operator-specific complexity/nesting control.
- **Escalate to `structured-expressions`** when the user knows an outer formula, requires shared components, category-specific parameters, vector-valued residual tricks, or template guesses.
- **Escalate to `export-and-artifacts`** when the task is about persisted hall-of-fame files, checkpoints, reload, JAX/Torch, LaTeX tables, or durable equation artifacts.
- **Escalate to `runtime-and-scaling`** when the issue is installation, first-start compilation, threading/processes, Slurm, CLI tests, or large-run resource planning.
