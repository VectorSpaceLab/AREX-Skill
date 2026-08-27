# Optimization API Reference

This reference focuses on execution APIs. Problem definitions and postprocessing
are covered in sibling sub-skills.

## `minimize`

```python
from pymoo.optimize import minimize
res = minimize(problem, algorithm, termination=None, copy_algorithm=True,
               copy_termination=True, seed=None, verbose=False, **kwargs)
```

Verified core signature:

```python
minimize(problem, algorithm, termination=None, copy_algorithm=True,
         copy_termination=True, **kwargs)
```

Common keyword arguments are forwarded to `algorithm.setup(...)` and include:

| Argument | Use | Notes |
| --- | --- | --- |
| `problem` | A `Problem`, `ElementwiseProblem`, `FunctionalProblem`, or compatible object. | Confirm minimization convention and output shapes first. |
| `algorithm` | Algorithm instance such as `NSGA2(pop_size=100)` or `GA(pop_size=100)`. | Deep-copied by default; inspect `res.algorithm` after the run. |
| `termination` | Tuple, termination object, or `None`. | Prefer explicit budgets for reproducible checks. |
| `seed` | Integer random seed. | Gives reproducible pymoo randomness when objective code is also deterministic. |
| `verbose` | Progress/display output. | Disable for scripts and timing. |
| `callback` | `Callback` object or callable hook. | Use for lightweight per-generation data collection. |
| `display` / `output` | Custom display/output objects. | Use only when terminal progress columns are part of the task. |
| `save_history` | Store algorithm snapshots in `res.history`. | Useful for convergence curves but memory-intensive. |
| `return_least_infeasible` | Return best infeasible solution when no feasible point exists. | Still report that the returned solution is infeasible. |

## Termination factory

```python
from pymoo.termination import get_termination
termination = get_termination("n_gen", 50)
```

Supported aliases in this version:

| Alias | Meaning | Typical call |
| --- | --- | --- |
| `"n_eval"`, `"n_evals"` | Maximum function evaluations | `("n_evals", 2000)` |
| `"n_gen"`, `"n_iter"` | Maximum generations/iterations | `("n_gen", 100)` |
| `"fmin"` | Minimum function value | `get_termination("fmin", 1e-6)` |
| `"time"` | Wall-clock time | `("time", "00:10:00")` or seconds-style value accepted by the object |
| `"soo"` | Default single-objective tolerance bundle | `get_termination("soo")` |
| `"moo"` | Default multi-objective tolerance bundle | `get_termination("moo")` |

If a tuple fails with `Termination not found`, check spelling and use the exact
aliases above.

## Representative algorithms and signatures

| Class | Import | Minimal verified signature | Notes |
| --- | --- | --- | --- |
| `NSGA2` | `from pymoo.algorithms.moo.nsga2 import NSGA2` | `NSGA2(pop_size=100, sampling=..., crossover=..., mutation=..., survival=..., output=..., **kwargs)` | Default starting point for many two-objective constrained/unconstrained tasks. |
| `NSGA3` | `from pymoo.algorithms.moo.nsga3 import NSGA3` | `NSGA3(ref_dirs, pop_size=None, ..., **kwargs)` | Requires reference directions; use for many objectives. |
| `UNSGA3` | `from pymoo.algorithms.moo.unsga3 import UNSGA3` | Similar to NSGA-III with reference directions. | Generalized NSGA-III route for single/bi/many-objective cases. |
| `MOEAD` | `from pymoo.algorithms.moo.moead import MOEAD` | `MOEAD(ref_dirs=None, n_neighbors=20, decomposition=None, prob_neighbor_mating=0.9, ..., **kwargs)` | Decomposition-based, usually needs reference directions/weights. |
| `RVEA` | `from pymoo.algorithms.moo.rvea import RVEA` | `RVEA(ref_dirs, ..., **kwargs)` | Reference-vector many-objective route. |
| `GA` | `from pymoo.algorithms.soo.nonconvex.ga import GA` | `GA(pop_size=100, sampling=..., crossover=..., mutation=..., survival=..., eliminate_duplicates=True, **kwargs)` | General-purpose single-objective genetic algorithm. |
| `DE` | `from pymoo.algorithms.soo.nonconvex.de import DE` | `DE(pop_size=100, n_offsprings=None, sampling=..., variant="DE/best/1/bin", **kwargs)` | Continuous global optimization; tune variant and population. |
| `PSO` | `from pymoo.algorithms.soo.nonconvex.pso import PSO` | `PSO(pop_size=25, w=0.9, c1=2.0, c2=2.0, adaptive=True, ..., **kwargs)` | Swarm optimizer for continuous spaces. |
| `CMAES` | `from pymoo.algorithms.soo.nonconvex.cmaes import CMAES` | Constructor delegates to CMA-ES options. | Good for continuous single-objective local/global search; uses `cma`. |

Operator customization belongs to `operators-and-variables`; this table names
only the constructor hooks that often appear on algorithm constructors.

## Direct algorithm lifecycle

Most algorithms can be used without `minimize`:

```python
algorithm.setup(problem, termination=("n_gen", 20), seed=1, verbose=False)
while algorithm.has_next():
    algorithm.next()
res = algorithm.result()
```

This mutates the algorithm object you hold. That is useful for debugging and
interactive control, but it differs from `minimize`, which deep-copies by default.

## Ask-and-tell essentials

```python
from pymoo.core.evaluator import Evaluator

algorithm.setup(problem, termination=("n_gen", 10), seed=1, verbose=False)
while algorithm.has_next():
    pop = algorithm.ask()
    algorithm.evaluator.eval(problem, pop)   # or external evaluation + StaticProblem
    algorithm.tell(infills=pop)
res = algorithm.result()
```

Use ask-and-tell when evaluation is external, asynchronous, simulation-backed, or
must be inspected/modified before reinsertion.

## `Result` fields to inspect

| Field | Meaning | Checks |
| --- | --- | --- |
| `res.X` | Decision variable(s) of the best solution or non-dominated set. | Shape may be `(n_solutions, n_var)` for multi-objective results. |
| `res.F` | Objective values. | Every column is minimized; finite numeric matrix expected. |
| `res.G` / `res.H` | Inequality/equality constraint values, when requested/populated. | Feasible inequalities satisfy `G <= 0`; equality tolerances depend on termination/problem. |
| `res.CV` | Constraint violation aggregate. | Zero/near-zero indicates feasibility; positive values need investigation. |
| `res.opt` | Population/individual object representing optimum set. | Use `.get("X")`, `.get("F")`, `.get("CV")` for robust extraction. |
| `res.algorithm` | Executed algorithm copy/state. | Inspect `n_gen`, `evaluator.n_eval`, population, archive, or history. |
| `res.history` | Snapshots when `save_history=True`. | Memory-heavy; useful for convergence curves. |
| `res.exec_time` | Runtime in seconds. | Compare only under similar hardware/workload conditions. |

## Callback and display hooks

Subclass `pymoo.core.callback.Callback` and implement `notify(self, algorithm)`
when you need structured per-generation data. Keep callback work lightweight and
avoid mutating algorithm internals unless the task explicitly asks for adaptive
control.

Display/output customization affects terminal progress columns, not the core
algorithm result. If a task only needs logged metrics, prefer a callback over a
custom display.
