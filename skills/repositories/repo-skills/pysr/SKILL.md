---
name: pysr
description: "Use PySR for symbolic regression, interpretable equation
  discovery, equation export, runtime scaling, and PySR troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# PySR repo skill

Use this skill when a task involves PySR, SymbolicRegression.jl from Python, symbolic regression, interpretable equation discovery from numeric data, scaling-law or formula search, or troubleshooting PySR installation/search/export behavior.

PySR exposes a scikit-learn-style `PySRRegressor` front end backed by Julia's SymbolicRegression.jl. It returns a Pareto front of equations that trade loss against complexity. Treat PySR as a stochastic search tool: validate data and operators first, run bounded smoke fits, inspect the full Pareto front, then run longer searches only after the setup is sensible.

## Install and import check

For ordinary use:

```bash
pip install pysr
# or
conda install -c conda-forge pysr
```

Minimal check:

```python
import pysr
from pysr import PySRRegressor
print(pysr.__version__)
```

A fresh `import pysr` can download/resolve Julia packages and the first fit can compile Julia code. Do not misdiagnose that first-run setup cost as a failed search. For runtime/startup details, read `sub-skills/runtime-and-scaling/SKILL.md`.

## Route map

| Task | Read |
| --- | --- |
| Fit ordinary tabular data, choose operators, inspect `model.equations_`, select equations, debug trivial/slow searches | `sub-skills/fit-and-diagnose/SKILL.md` |
| Define custom Julia operators, losses, full objectives, units, constraints, complexity rules, mutations, or plugins | `sub-skills/customization-and-constraints/SKILL.md` |
| Use known expression skeletons, `TemplateExpressionSpec`, category parameters, shared/vector-valued templates, differential operators, or guesses | `sub-skills/structured-expressions/SKILL.md` |
| Export equations to SymPy/LaTeX/NumPy/JAX/PyTorch, inspect hall-of-fame CSVs, reload checkpoints, or configure TensorBoard logging | `sub-skills/export-and-artifacts/SKILL.md` |
| Install, import, manage JuliaCall, choose threads/processes/Slurm, bound long runs, use CLI tests, or diagnose startup/runtime failures | `sub-skills/runtime-and-scaling/SKILL.md` |

## Fast operating pattern

1. **Start with data and objective.** Confirm `X` has shape `(n_samples, n_features)` and `y` is one-dimensional for one target or two-dimensional for multi-output. Decide whether weights, feature names, units, or denoising are needed.
2. **Choose a small search space.** Keep operators minimal. Every unnecessary operator expands the evolutionary search; add custom operators/losses only when domain evidence justifies them.
3. **Bound first runs.** Use low `niterations`, `timeout_in_seconds`, `max_evals`, and `input_stream="devnull"` in scripts/noninteractive contexts.
4. **Inspect the Pareto front.** `model.equations_` is the primary result. Compare loss and complexity, and pass `index=` to `predict`, `sympy`, or `latex` when you want a specific row rather than the default selection.
5. **Escalate deliberately.** For known structure use templates; for domain rules use finite penalties, constraints, units, or custom objectives; for large jobs use batching or Slurm after the simple case works.
6. **Persist durable artifacts.** Save the construction code and hall-of-fame CSV. Pickle checkpoints are useful but version-sensitive.

## Shared references and scripts

- `references/api-index.md` maps common public APIs to the owning sub-skill.
- `references/troubleshooting.md` covers cross-cutting failures and points to the nearest owner.
- `references/repo-provenance.md` records the source snapshot used to create this skill.
- `references/repo-routing-metadata.json` contains structured routing metadata for managed repo-skill import.
- `scripts/check_pysr_environment.py` performs a safe package/CLI/API probe without fitting a model by default.

## Boundaries

This skill is for using PySR as a package. It does not replace SymbolicRegression.jl's Julia-native documentation for deep backend development, and it does not claim optional JAX, PyTorch, TensorBoard, Slurm, or autodiff backends are installed unless the current environment is checked.
