# Problem Definition Workflows

## Start with a built-in problem smoke

Before debugging a custom optimization stack, prove the algorithm and install on
a known problem:

```python
from pymoo.algorithms.moo.nsga2 import NSGA2
from pymoo.optimize import minimize
from pymoo.problems import get_problem

problem = get_problem("zdt1")
res = minimize(problem, NSGA2(pop_size=20), ("n_gen", 3), seed=1, verbose=False)
assert res.F.shape[1] == 2
```

If this fails, route to install/backends troubleshooting before editing custom
problem code.

## Porting a mathematical problem

1. List decision variables, bounds, objectives, and constraints.
2. Convert every objective to minimization. A maximization objective `maximize f`
   becomes `minimize -f`.
3. Convert inequalities to `G <= 0`. For a source constraint `a(x) >= b`, write
   `b - a(x) <= 0`.
4. Normalize constraints with different scales when violation magnitudes should
   be comparable.
5. Put equality residuals in `H`, not `G`.
6. Validate shapes and signs with `problem.evaluate(...)` before optimizing.

## Vectorized class workflow

Use vectorized `Problem` for NumPy/SciPy-friendly objectives.

```python
import numpy as np
from pymoo.core.problem import Problem

class ConstrainedBiObjective(Problem):
    def __init__(self):
        super().__init__(n_var=2, n_obj=2, n_ieq_constr=2,
                         xl=np.array([-2.0, -2.0]), xu=np.array([2.0, 2.0]))

    def _evaluate(self, X, out, *args, **kwargs):
        f1 = 100.0 * (X[:, 0] ** 2 + X[:, 1] ** 2)
        f2 = (X[:, 0] - 1.0) ** 2 + X[:, 1] ** 2
        g1 = 2.0 * (X[:, 0] - 0.1) * (X[:, 0] - 0.9) / 0.18
        g2 = -20.0 * (X[:, 0] - 0.4) * (X[:, 0] - 0.6) / 4.8
        out["F"] = np.column_stack([f1, f2])
        out["G"] = np.column_stack([g1, g2])
```

Validation:

```python
X = np.array([[0.2, 0.0], [0.5, 0.0], [1.0, 1.0]])
F, G = ConstrainedBiObjective().evaluate(X, return_values_of=["F", "G"])
assert F.shape == (3, 2)
assert G.shape == (3, 2)
```

## Elementwise black-box workflow

Use `ElementwiseProblem` if evaluating one candidate means running a simulation,
calling a solver, querying an external service, or operating on object variables.

```python
import numpy as np
from pymoo.core.problem import ElementwiseProblem

class BlackBoxProblem(ElementwiseProblem):
    def __init__(self):
        super().__init__(n_var=3, n_obj=1, n_ieq_constr=1, xl=-1.0, xu=1.0)

    def _evaluate(self, x, out, *args, **kwargs):
        out["F"] = float(np.sum((x - 0.25) ** 2))
        out["G"] = [float(np.sum(x) - 1.0)]
```

For parallel elementwise evaluation, add `elementwise_runner=...` when
constructing the problem and follow the performance sub-skill.

## Functional workflow

Use `FunctionalProblem` for compact formulas or exploratory notebooks:

```python
import numpy as np
from pymoo.problems.functional import FunctionalProblem

problem = FunctionalProblem(
    2,
    objs=[lambda x: x[0] ** 2 + x[1] ** 2,
          lambda x: (x[0] - 1.0) ** 2 + x[1] ** 2],
    constr_ieq=[lambda x: x[0] + x[1] - 1.0],
    xl=np.array([-2.0, -2.0]),
    xu=np.array([2.0, 2.0]),
)
```

If the task later needs multiprocessing or serialization, convert lambdas to a
module-level class-based problem.

## Equality constraints

For equality `h(x) = 0`, declare `n_eq_constr` and fill `out["H"]`:

```python
class EqualityProblem(Problem):
    def __init__(self):
        super().__init__(n_var=2, n_obj=1, n_eq_constr=1, xl=-1.0, xu=1.0)

    def _evaluate(self, X, out, *args, **kwargs):
        out["F"] = np.sum(X ** 2, axis=1, keepdims=True)
        out["H"] = (X[:, 0] + X[:, 1] - 1.0)[:, None]
```

Evolutionary algorithms may struggle with exact equality feasibility. Consider a
repair operator, a reduced search-space encoding, or an inequality tolerance if
the mathematical task permits it.

## Known optima and Pareto fronts

Implement `_calc_pareto_front` and `_calc_pareto_set` only when you have a real
formula or reliable generator:

```python
class MyZDTLike(Problem):
    def _calc_pareto_front(self, n_pareto_points=100):
        x = np.linspace(0.0, 1.0, n_pareto_points)
        return np.column_stack([x, 1.0 - np.sqrt(x)])
```

Do not fabricate a Pareto front for analysis metrics. If a front is unknown,
use non-dominated filtering, hypervolume with an explicit reference point, or
history-based convergence analysis.

## Constraint-handling routes

- **Feasibility first**: default evolutionary handling often ranks feasible
  solutions ahead of infeasible ones.
- **Penalty**: convert constraint violation into a penalized objective when the
  task needs a single scalar objective and accepts penalty tuning.
- **Constraint violation as objective**: optimize feasibility and original
  objective(s) separately; useful for exploration but changes objective count.
- **Epsilon constraint**: relax feasibility early and tighten over time; useful
  when hard constraints are difficult.
- **Repair**: transform infeasible `X` into a feasible or bounded representation;
  route repair operator implementation to `operators-and-variables`.

## Validation checklist

Before running a nontrivial optimizer:

1. Sample two or more in-bound candidate rows.
2. Run `problem.evaluate(X, return_values_of=["F", "G", "H" as applicable])`.
3. Assert `F.shape[0] == X.shape[0]` and `F.shape[1] == n_obj`.
4. Assert every declared constraint matrix has the correct row count and column
   count.
5. Assert all values are finite or deliberately replaced through
   `replace_nan_values_by`.
6. Manually check one known feasible/infeasible point to confirm the `G <= 0`
   sign convention.
7. Only then run a small optimization smoke.
