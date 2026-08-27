---
name: pymoo
description: "Use pymoo for single-, multi-, and many-objective optimization,
  custom problems, evolutionary operators, performance tuning, and Pareto
  analysis."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# pymoo

Use this repo skill when a task involves pymoo, evolutionary computation,
single-objective optimization, multi-objective or many-objective optimization,
Pareto fronts, custom optimization problems, genetic operators, reference
directions, constraint handling, performance indicators, or pymoo visualization.

pymoo is a Python package for optimization workflows. It minimizes all
objectives, represents inequality constraints as `G <= 0`, and centers common
usage around a `Problem`, an `Algorithm`, a termination criterion, and
`pymoo.optimize.minimize`.

## Quick install and smoke

Public install path:

```bash
python -m pip install -U pymoo
```

Minimal import/runtime check:

```bash
python - <<'PY'
from pymoo.algorithms.moo.nsga2 import NSGA2
from pymoo.optimize import minimize
from pymoo.problems import get_problem

res = minimize(get_problem("zdt1"), NSGA2(pop_size=20), ("n_gen", 3), seed=1, verbose=False)
print(res.F.shape, res.algorithm.evaluator.n_eval)
PY
```

For a bundled self-check after installing pymoo, run
[scripts/pymoo_quickstart_smoke.py](scripts/pymoo_quickstart_smoke.py).

## Route by task

| User task signal | Read |
| --- | --- |
| Run NSGA-II/NSGA-III/GA/DE/PSO/MOEA/D, choose an algorithm, set termination, use `minimize`, inspect `Result`, callbacks, history, ask-and-tell, external evaluation loop | [optimization-workflows](sub-skills/optimization-workflows/SKILL.md) |
| Define a custom problem, choose `Problem` vs `ElementwiseProblem` vs `FunctionalProblem`, use `get_problem`, fix `F`/`G`/`H` shapes, convert maximization or constraints, handle bounds/Pareto fronts | [problem-modeling](sub-skills/problem-modeling/SKILL.md) |
| Configure real/integer/binary/choice variables, mixed-variable search, sampling/crossover/mutation/repair, duplicate elimination, initial populations, custom object/permutation operators, hyperparameter helper APIs | [operators-and-variables](sub-skills/operators-and-variables/SKILL.md) |
| Speed up slow evaluations, vectorize objectives, add thread/process starmap, use optional joblib/dask/ray, check Cython compiled extensions, reason about optional GPU/backend paths, control history/progress overhead | [performance-and-parallelization](sub-skills/performance-and-parallelization/SKILL.md) |
| Compute hypervolume, GD/IGD/epsilon/KKTPM/R-metric, generate reference directions, use decomposition or MCDM, analyze convergence/history, save headless Pareto plots | [analysis-and-visualization](sub-skills/analysis-and-visualization/SKILL.md) |

## Operating rules that prevent common pymoo mistakes

1. **Minimization only**: negate objectives that are originally maximized.
2. **Constraint sign**: inequality constraints are feasible when `out["G"] <= 0`;
   equality residuals belong in `out["H"]` with `n_eq_constr`.
3. **Validate problem shapes first**: check tiny `problem.evaluate(...)` samples
   before tuning algorithms.
4. **Use explicit budgets**: pass termination tuples such as `("n_gen", 50)` or
   `("n_evals", 5000)` for reproducible scripts.
5. **Seed stochastic runs**: pass `seed=...` and control randomness inside custom
   objective code, especially under parallel evaluation.
6. **Match algorithm to search space**: mixed/discrete/permutation variables need
   matching variables/operators or repair, not just a float-coded algorithm.
7. **Keep optional extras explicit**: base pymoo includes matplotlib and core
   numerical dependencies; joblib/dask/ray, Optuna, COMO-CMA-ES, pyrecorder, and
   GPU frameworks are optional task-specific additions.
8. **Use headless plotting in agents**: set a non-interactive Matplotlib backend
   and save figures instead of relying on GUI `show()`.

## Shared references

- [API entrypoints](references/api-entrypoints.md): cross-sub-skill import map,
  version/extras notes, and first checks.
- [Troubleshooting](references/troubleshooting.md): install/import, compiled
  extension, optional dependency, and cross-workflow failure routing.
- [Repo provenance](references/repo-provenance.md): source version and evidence
  baseline for refresh decisions.
- [Repo routing metadata](references/repo-routing-metadata.json): structured
  router metadata consumed during managed import.

## Bundled self-check scripts

- [scripts/pymoo_quickstart_smoke.py](scripts/pymoo_quickstart_smoke.py): base
  import, compiled-extension status, and tiny `NSGA2`/`ZDT1` run.
- Sub-skill scripts cover custom-problem shape validation, mixed-variable search,
  parallel elementwise evaluation, indicator checks, compiled-extension checks,
  and headless scatter plotting.

## Avoid this skill when

- The task is generic mathematical optimization with SciPy and does not use
  pymoo APIs, evolutionary operators, Pareto fronts, or pymoo problem classes.
- The task is hyperparameter optimization with Optuna/Ray Tune alone and no pymoo
  algorithm/problem integration.
- The task requires training deep learning models or GPU tensor code unrelated to
  pymoo's optional vectorized objective pattern.
