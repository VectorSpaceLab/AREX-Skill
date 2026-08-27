---
name: fit-and-diagnose
description: "Fit ordinary PySR regressors, inspect Pareto fronts, select
  equations, and diagnose slow or poor searches."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# PySR fit-and-diagnose

Use this sub-skill when the task is an ordinary PySR symbolic-regression fit: prepare tabular data, choose a small operator set, run `PySRRegressor.fit`, inspect `model.equations_`, pick equations from the Pareto front, call `predict`/`sympy`/`latex`, or debug a slow or low-quality search.

## Route first

| User need | Use here? | Route |
| --- | --- | --- |
| Plain `PySRRegressor` fit, data shape, feature names, weights, denoising, feature selection, Pareto selection | Yes | Continue below. |
| Custom Julia operators, custom elementwise/full losses, units, operator constraints, required/forbidden structure by loss penalties | No | `../customization-and-constraints/SKILL.md` |
| Known expression templates, parametric expressions, shared/vector-valued templates, guesses for templates | No | `../structured-expressions/SKILL.md` |
| Saved hall-of-fame files, reload/checkpoints, SymPy/LaTeX/JAX/Torch export details, TensorBoard artifacts | No | `../export-and-artifacts/SKILL.md` |
| Installation, first Julia startup, threading, multiprocessing, Slurm, long-run scaling, reproducibility environment | Usually no | `../runtime-and-scaling/SKILL.md` |

## Minimal operating loop

1. **Validate data shape.** Use `X` as `(n_samples, n_features)` and `y` as `(n_samples,)` for one target or `(n_samples, n_outputs)` for independent multi-output fits. Prefer a pandas DataFrame when feature names matter; otherwise pass safe `variable_names` to `fit`.
2. **Start with a small operator set.** Use only operators that are plausible for the domain. For a polynomial-like first pass, start with `binary_operators=["+", "-", "*"]`; add `/`, trig, `exp`, or other operators only when justified.
3. **Bound the first run.** Start short to validate the setup, then run longer. Use `niterations`, `timeout_in_seconds`, or `max_evals` for budget control. Avoid interpreting the first Julia compile as a search failure.
4. **Fit and inspect the whole front.** `model.fit(X, y, weights=..., variable_names=...)` stores a Pareto front in `model.equations_`. Print it and inspect loss versus complexity rather than reporting only the auto-selected row.
5. **Select explicitly when needed.** `model_selection="best"` balances loss and simplicity; `"accuracy"` chooses minimum loss; `"score"` chooses the largest score. Pass `index=` to `predict`, `sympy`, or `latex` to evaluate a specific row.
6. **Iterate scientifically.** If results are trivial or slow, simplify features/operators, adjust `maxsize`, use `select_k_features` for high-dimensional tabular data, consider `denoise=True` or weights for noisy data, and only then add more compute.

See `references/workflows.md` for recipes, `references/api-reference.md` for focused signatures and option semantics, and `references/troubleshooting.md` for failure modes.

## Safe bundled smoke helper

`scripts/pysr_quickstart_smoke.py` is a small, deterministic helper for agents. It is help/dry-run oriented by default and imports PySR only when `--run-fit` is supplied.

```bash
python scripts/pysr_quickstart_smoke.py --help
python scripts/pysr_quickstart_smoke.py --run-fit --niterations 1 --timeout-seconds 20
```

The helper is a smoke check, not a benchmark. A successful run proves that import, a tiny fit, `equations_`, `predict`, `sympy`, and `latex` are usable in the current environment; it does not prove convergence on the user's dataset.
