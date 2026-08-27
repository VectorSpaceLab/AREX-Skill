---
name: optimization-workflows
description: "Run, control, and debug pymoo optimization workflows with
  algorithms, termination, callbacks, ask-and-tell loops, and result
  interpretation."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# optimization-workflows

Use this sub-skill when a task asks how to run pymoo optimizers: choosing an
algorithm, calling `minimize`, setting termination, controlling stochastic
reproducibility, using callbacks or display/output hooks, stepping an algorithm
manually, adapting an ask-and-tell loop, interpreting `Result`, or diagnosing an
empty/infeasible optimization outcome.

## Route first

- Define objective/constraint functions, `Problem` output shapes, bounds, or
  built-in test problems with `problem-modeling`.
- Customize variables, sampling, crossover, mutation, repair, duplicate
  elimination, or initialization with `operators-and-variables`.
- Speed up expensive evaluation, use starmap/joblib/dask/ray, or inspect compiled
  extensions with `performance-and-parallelization`.
- Compute hypervolume, IGD/GD, MCDM decisions, convergence curves, reference
  directions, or plots with `analysis-and-visualization`.
- Stay here for optimization execution control, algorithm portfolio routing,
  termination decisions, callbacks/display/history, and `Result` fields.

## Fast operating checklist

1. **Normalize the optimization contract**: pymoo minimizes every objective.
   Confirm the problem exposes `n_obj`, `n_ieq_constr`/`n_eq_constr`, bounds, and
   finite `F`/`G`/`H` values before tuning algorithms.
2. **Choose an algorithm by objective count and variable type**: use single-
   objective algorithms such as `GA`, `DE`, `PSO`, `CMAES`, or local searches for
   one objective; use `NSGA2`, `SPEA2`, `SMSEMOA`, `GDE3`, or reference-direction
   algorithms such as `NSGA3`, `UNSGA3`, `RVEA`, `MOEAD` for multi/many-objective
   runs.
3. **Start with functional `minimize`**: pass `(problem, algorithm,
   termination)` plus `seed` and `verbose=False`. Remember `minimize` deep-copies
   the algorithm by default; inspect the executed copy through `res.algorithm`.
4. **Select an explicit termination**: use a tuple such as `("n_gen", 50)`,
   `("n_evals", 5000)`, `("time", "00:05:00")`, or a termination object when
   defaults are too vague for verification.
5. **Control stochasticity**: pass `seed=...` and avoid hidden random draws in
   objective code. Compare algorithms with the same problem, seed policy, and
   evaluation budget.
6. **Use callbacks/history intentionally**: callbacks are lightweight for
   logging; `save_history=True` stores algorithm snapshots and can use substantial
   memory.
7. **Interpret `Result` defensively**: check `res.X`, `res.F`, `res.G`, `res.CV`,
   `res.opt`, `res.algorithm.evaluator.n_eval`, `res.exec_time`, and whether the
   best solution is feasible before reporting success.

## Open the bundled references

- [API reference](references/api-reference.md): signatures and field contracts for
  `minimize`, algorithms, termination, callbacks, display/output, and `Result`.
- [Algorithm selection](references/algorithm-selection.md): representative SOO,
  MOO, many-objective, dynamic, and preference-guided algorithm routes with
  import paths and fit signals.
- [Workflows](references/workflows.md): functional `minimize`, direct algorithm
  stepping, ask-and-tell, external evaluation, checkpoint/debug, and comparison
  patterns.
- [Troubleshooting](references/troubleshooting.md): termination lookup failures,
  infeasible/empty results, stochastic drift, callback/history mistakes, and
  common API misuse.

## Bundled script

- [scripts/run_minimize_smoke.py](scripts/run_minimize_smoke.py): safe CPU-only
  quickstart smoke that runs a tiny NSGA-II/ZDT1 optimization and asserts the
  result shape and evaluation count.
