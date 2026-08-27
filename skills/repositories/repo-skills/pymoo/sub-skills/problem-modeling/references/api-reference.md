# Problem Modeling API Reference

pymoo problem objects define metadata and fill output arrays. Algorithms consume
these objects; they do not know whether your objective is algebra, simulation, or
another package.

## Core constructors

Verified constructor signatures in this version include:

```python
from pymoo.core.problem import Problem, ElementwiseProblem
from pymoo.problems.functional import FunctionalProblem

Problem(n_var=-1, n_obj=1, n_ieq_constr=0, n_eq_constr=0,
        xl=None, xu=None, vtype=None, vars=None, elementwise=False,
        elementwise_runner=..., requires_kwargs=False,
        replace_nan_values_by=None, strict=True, **kwargs)

ElementwiseProblem(elementwise=True, **kwargs)

FunctionalProblem(n_var, objs, constr_ieq=None, constr_eq=None,
                  func_pf=..., func_ps=..., **kwargs)
```

| Parameter | Meaning | Operational notes |
| --- | --- | --- |
| `n_var` | Number of decision variables. | Must match candidate vector width for ordinary numeric problems. If `vars` is provided, `n_var` is derived from the variable dict. |
| `n_obj` | Number of objectives. | Every objective column is minimized. |
| `n_ieq_constr` | Number of inequality constraints. | Feasible values satisfy `G <= 0`. |
| `n_eq_constr` | Number of equality constraints. | Output `H`; feasible values should be close to zero under task tolerance. |
| `xl`, `xu` | Lower/upper bounds. | Scalars expand to all variables; arrays should have length `n_var`; invalid lengths or `xl > xu` warn. |
| `vtype` | Type hint for variables. | For robust mixed variables, use explicit `vars` and the operators sub-skill. |
| `vars` | Dict of variable objects (`Real`, `Integer`, `Choice`, etc.). | Use with `MixedVariableGA` or matching operators. |
| `elementwise` | Whether evaluation receives one candidate at a time. | `ElementwiseProblem` sets it `True`; vectorized `Problem` keeps it `False`. |
| `elementwise_runner` | Runner for elementwise calls. | Use with starmap/joblib/dask/ray patterns in performance guidance. |
| `replace_nan_values_by` | Substitute value for NaNs in outputs. | Use only as an explicit recovery strategy; better to fix invalid objective code. |
| `strict` | Shape checking. | Keep `True` while developing to catch mistakes early. |

`n_constr` is deprecated in new code. If encountered, map it to
`n_ieq_constr` only after confirming all constraints are inequalities.

## Vectorized `Problem` output contract

```python
import numpy as np
from pymoo.core.problem import Problem

class MyVectorProblem(Problem):
    def __init__(self):
        super().__init__(n_var=2, n_obj=2, n_ieq_constr=1, xl=-2.0, xu=2.0)

    def _evaluate(self, X, out, *args, **kwargs):
        # X shape: (n_candidates, 2)
        f1 = X[:, 0] ** 2 + X[:, 1] ** 2
        f2 = (X[:, 0] - 1.0) ** 2 + X[:, 1] ** 2
        g1 = X[:, 0] + X[:, 1] - 1.0       # <= 0 is feasible
        out["F"] = np.column_stack([f1, f2])
        out["G"] = g1[:, None]
```

Output shape rules:

| Output | Required rows | Columns | Notes |
| --- | --- | --- | --- |
| `out["F"]` | one per candidate | `n_obj` | Use `np.column_stack` for multi-objective vectorized outputs. |
| `out["G"]` | one per candidate | `n_ieq_constr` | Values `<= 0` are feasible. |
| `out["H"]` | one per candidate | `n_eq_constr` | Values near zero are feasible. |
| `out["dF"]`, `out["dG"]` | optional derivative arrays | derivative-dependent | Only needed by gradient-aware utilities/indicators. |

For a single objective, pymoo often accepts a one-dimensional vector. Use a
2-D `(n, 1)` matrix in generated guidance when clarity is more important than
brevity.

## Elementwise `Problem` output contract

```python
from pymoo.core.problem import ElementwiseProblem

class MyElementwiseProblem(ElementwiseProblem):
    def __init__(self):
        super().__init__(n_var=2, n_obj=2, n_ieq_constr=1, xl=-2.0, xu=2.0)

    def _evaluate(self, x, out, *args, **kwargs):
        # x shape: (2,)
        out["F"] = [x[0] ** 2, (x[0] - 1.0) ** 2 + x[1] ** 2]
        out["G"] = [x[0] + x[1] - 1.0]
```

Use elementwise style when one candidate triggers one expensive simulation or
external call. For parallel elementwise evaluation, pass `elementwise_runner` in
the constructor and follow the performance sub-skill.

## FunctionalProblem

```python
import numpy as np
from pymoo.problems.functional import FunctionalProblem

problem = FunctionalProblem(
    3,
    objs=[lambda x: np.sum(x ** 2), lambda x: np.sum((x - 1) ** 2)],
    constr_ieq=[lambda x: x[0] + x[1] - 1.0],
    xl=np.zeros(3),
    xu=np.ones(3),
)
```

Functional problems are concise for small mathematical definitions. They can be
harder to serialize/parallelize if lambdas capture state; use class-based
problems for complex or production workflows.

## `evaluate`

```python
F = problem.evaluate(X)
F, G = problem.evaluate(X, return_values_of=["F", "G"])
out = problem.evaluate(X, return_as_dictionary=True)
```

Validation tips:

- Use a tiny `X` with known bounds before running an algorithm.
- Request every output you declared (`F`, `G`, `H`, derivatives when needed).
- Assert finite numeric values and expected shapes.
- For elementwise object variables, test a small list/dict sample that matches
  the algorithm/operator encoding.

## Built-in problem factory

```python
from pymoo.problems import get_problem

zdt1 = get_problem("zdt1")
dtlz2 = get_problem("dtlz2", n_obj=3)
sphere = get_problem("sphere", n_var=10)
```

Representative built-in families:

| Family | Names/signals | Fit |
| --- | --- | --- |
| Single-objective | `sphere`, `ackley`, `rastrigin`, `rosenbrock`, `griewank`, `zakharov`, `g1`-`g24` | Algorithm smoke tests, constrained single-objective benchmarks. |
| Multi-objective | `zdt1`-`zdt6`, `bnh`, `osy`, `srn`, `tnk`, `welded_beam`, `truss2d`, `mw1`-`mw14`, `dascmop1`-`dascmop9` | Multi-objective and constrained MOO baselines. |
| Many-objective | `dtlz1`-`dtlz7`, `wfg1`-`wfg9`, `zcat1`-`zcat20` | Reference-direction algorithm and many-objective experiments. |
| Dynamic | `df1`-`df14` | Dynamic optimization algorithm testing. |

If `get_problem` raises `Problem not found`, lowercase the name and check the
family spelling.

## Pareto front/set methods

Built-in and custom problems may implement:

```python
pf = problem.pareto_front()
ps = problem.pareto_set()
```

A known Pareto front is useful for analysis metrics such as GD/IGD. If a custom
problem does not know its front, leave `_calc_pareto_front` undefined and use
hypervolume/history or non-dominated filtering instead of inventing a front.
