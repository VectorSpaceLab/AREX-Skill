# Optimization Workflows

## Functional `minimize` quickstart

```python
from pymoo.algorithms.moo.nsga2 import NSGA2
from pymoo.optimize import minimize
from pymoo.problems import get_problem

problem = get_problem("zdt1")
algorithm = NSGA2(pop_size=40, eliminate_duplicates=True)
res = minimize(problem, algorithm, ("n_gen", 25), seed=1, verbose=False)

assert res.F is not None and res.F.shape[1] == 2
print(res.X.shape, res.F.shape, res.algorithm.evaluator.n_eval)
```

Use this pattern for most one-off optimization tasks. It deep-copies the
algorithm by default, so the object passed to `minimize` remains reusable. Inspect
`res.algorithm` for the executed copy.

## Single-objective run

```python
from pymoo.algorithms.soo.nonconvex.de import DE
from pymoo.optimize import minimize
from pymoo.problems.single import Sphere

problem = Sphere(n_var=10)
res = minimize(problem, DE(pop_size=50), ("n_evals", 1000), seed=2, verbose=False)
print(float(res.F), res.X)
```

For single-objective results, `res.X` and `res.F` often describe one best
solution. Still check feasibility (`res.CV`) when constraints exist.

## Many-objective run with reference directions

```python
from pymoo.algorithms.moo.nsga3 import NSGA3
from pymoo.optimize import minimize
from pymoo.problems import get_problem
from pymoo.util.ref_dirs import get_reference_directions

problem = get_problem("dtlz2", n_obj=3)
ref_dirs = get_reference_directions("uniform", 3, n_partitions=12)
algorithm = NSGA3(ref_dirs=ref_dirs)
res = minimize(problem, algorithm, ("n_gen", 40), seed=1, verbose=False)
```

Reference-direction generation and post-run quality analysis are covered by the
analysis sub-skill. Keep reference direction count and population size aligned
with the problem dimensionality.

## Direct algorithm stepping

Use direct stepping when the task needs to inspect or modify the algorithm while
it runs.

```python
from pymoo.algorithms.moo.nsga2 import NSGA2
from pymoo.problems import get_problem

problem = get_problem("zdt1")
algorithm = NSGA2(pop_size=40)
algorithm.setup(problem, termination=("n_gen", 10), seed=1, verbose=False)

while algorithm.has_next():
    algorithm.next()
    print("gen", algorithm.n_gen, "evals", algorithm.evaluator.n_eval)

res = algorithm.result()
```

Unlike `minimize`, this mutates `algorithm` in place.

## Ask-and-tell with pymoo evaluator

Use this when you need to inspect or alter infill candidates before telling the
algorithm the results, but evaluation can still happen through a pymoo problem.

```python
from pymoo.algorithms.moo.nsga2 import NSGA2
from pymoo.problems import get_problem

problem = get_problem("zdt1")
algorithm = NSGA2(pop_size=40)
algorithm.setup(problem, termination=("n_gen", 10), seed=1, verbose=False)

while algorithm.has_next():
    pop = algorithm.ask()
    algorithm.evaluator.eval(problem, pop)  # increments n_eval consistently
    algorithm.tell(infills=pop)

res = algorithm.result()
```

## Ask-and-tell with external evaluation

If candidates must be evaluated by an external simulator/service, keep the
problem metadata in pymoo and attach objective values before `tell`.

```python
import numpy as np
from pymoo.algorithms.moo.nsga2 import NSGA2
from pymoo.core.evaluator import Evaluator
from pymoo.core.problem import Problem
from pymoo.problems.static import StaticProblem

problem = Problem(n_var=30, n_obj=2, xl=np.zeros(30), xu=np.ones(30))
algorithm = NSGA2(pop_size=40)
algorithm.setup(problem, termination=("n_gen", 5), seed=1, verbose=False)

while algorithm.has_next():
    pop = algorithm.ask()
    X = pop.get("X")
    f1 = X[:, 0]
    g = 1 + 9.0 / (problem.n_var - 1) * np.sum(X[:, 1:], axis=1)
    f2 = g * (1 - np.sqrt(f1 / g))
    F = np.column_stack([f1, f2])

    static = StaticProblem(problem, F=F)
    Evaluator().eval(static, pop)      # writes F to pop and counts evaluation
    algorithm.tell(infills=pop)

res = algorithm.result()
```

If evaluation is asynchronous, preserve row order or stable candidate IDs so
objective rows are assigned back to the correct individuals.

## Callback logging pattern

```python
from pymoo.core.callback import Callback

class MetricCallback(Callback):
    def __init__(self):
        super().__init__()
        self.data["n_eval"] = []
        self.data["best_cv"] = []

    def notify(self, algorithm):
        self.data["n_eval"].append(algorithm.evaluator.n_eval)
        cv = algorithm.opt.get("CV") if algorithm.opt is not None else None
        self.data["best_cv"].append(None if cv is None else float(cv.min()))
```

Pass `callback=MetricCallback()` to `minimize`. Keep callback state small and
serializable if you plan to checkpoint results.

## History and convergence

Set `save_history=True` only when a later analysis needs full snapshots:

```python
res = minimize(problem, algorithm, ("n_gen", 50), seed=1,
               verbose=False, save_history=True)
n_evals = [a.evaluator.n_eval for a in res.history]
fronts = [a.opt.get("F") for a in res.history]
```

For long runs or large populations, prefer a callback that stores only the
numbers you need.

## Minimal comparison loop

```python
runs = []
for seed in [1, 2, 3]:
    for make_algorithm in [lambda: NSGA2(pop_size=40), lambda: NSGA2(pop_size=80)]:
        res = minimize(problem, make_algorithm(), ("n_gen", 30), seed=seed, verbose=False)
        runs.append({"seed": seed, "F": res.F, "evals": res.algorithm.evaluator.n_eval})
```

Use analysis metrics consistently across runs. Do not compare algorithms with
different evaluation budgets unless the task explicitly studies budget tradeoffs.
