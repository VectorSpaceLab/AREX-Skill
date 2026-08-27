# Optimization Workflow Troubleshooting

## `Termination not found`

Symptoms:
- Passing a tuple such as `("gens", 100)` raises an exception.
- A custom string alias does not work.

Fix:
- Use one of pymoo's known aliases: `"n_gen"`, `"n_iter"`, `"n_eval"`,
  `"n_evals"`, `"time"`, `"fmin"`, `"soo"`, or `"moo"`.
- If you need tolerance composition, instantiate termination objects explicitly
  instead of inventing a tuple string.

## `res.X` or `res.F` is `None`

Likely causes:
- No feasible solution was found and `return_least_infeasible=False`.
- Problem evaluation returned NaN/invalid shapes, so no valid optimum exists.
- The termination budget was too small to initialize/evaluate useful candidates.

Recovery:
1. Inspect `res.algorithm.evaluator.n_eval`, `res.algorithm.pop.get("F")`, and
   `res.algorithm.pop.get("CV")`.
2. Check problem outputs with the problem-modeling validation script.
3. For constrained tasks, rerun with `return_least_infeasible=True` only if the
   caller understands the returned point is infeasible.
4. Increase the initial population/evaluation budget after shape and feasibility
   checks pass.

## All solutions are infeasible

Likely causes:
- Constraints are written with the wrong sign. pymoo expects inequality values
  in `G` to satisfy `G <= 0`.
- A maximization objective was not negated.
- Equality constraints are too strict for an evolutionary method without repair.
- Bounds or variable encodings make feasible points impossible.

Recovery:
- Route to `problem-modeling` to normalize `G`/`H`, objective minimization, and
  bounds.
- Add a repair operator or problem-specific feasibility-preserving encoding.
- Inspect `res.opt.get("CV")` and the best infeasible row before changing the
  algorithm.

## Same seed, different results

Likely causes:
- Objective code uses unseeded NumPy/Python/random-library calls outside pymoo.
- Parallel workers consume randomness in nondeterministic order.
- The algorithm object was mutated directly and reused instead of calling
  `minimize` with a fresh copy.

Recovery:
- Pass `seed=...` to `minimize` and seed any objective/simulation randomness
  explicitly.
- Construct a fresh algorithm per run or rely on `minimize` cloning.
- For parallel evaluation, pass deterministic candidate-index-derived seeds into
  the simulation instead of using global random state.

## `minimize` did not mutate my algorithm object

This is expected. `minimize` deep-copies the algorithm by default. Inspect
`res.algorithm` for the executed state, or set `copy_algorithm=False` only when
in-place mutation is intentional and documented.

## Direct algorithm loop never stops

Likely causes:
- No termination was passed to `algorithm.setup(...)`.
- You used `NoTermination` or an ask-and-tell loop without a generation/eval
  budget.
- External evaluation did not call `Evaluator().eval(...)` or otherwise update
  evaluated infills before `tell`.

Recovery:
- Always pass a termination to `setup` for direct loops.
- Print `algorithm.n_gen` and `algorithm.evaluator.n_eval` during a tiny debug
  run.
- In ask-and-tell, make sure every infill has the requested objective/constraint
  values before `algorithm.tell(infills=pop)`.

## Callback or display slows the run

Likely causes:
- Callback stores whole populations every generation.
- Display/progress output is enabled during timing.
- `save_history=True` stores deep snapshots of algorithm state.

Recovery:
- Store only scalar metrics or small arrays in callbacks.
- Set `verbose=False` while benchmarking.
- Use `save_history=True` only for short runs or when convergence analysis needs
  snapshots; otherwise use `AnytimeCallback` or a custom callback.

## Algorithm performs poorly

Checklist:
1. Validate the problem first: objective sign, constraints, finite outputs, and
   bounds.
2. Confirm objective count and variable type match the algorithm.
3. Increase budget gradually and monitor `n_eval`.
4. Tune population size, offspring count, sampling/crossover/mutation, and
   termination after a small smoke passes.
5. Compare across multiple seeds and a consistent metric.

Do not switch to a more specialized algorithm before fixing invalid problem
outputs or impossible constraints.
