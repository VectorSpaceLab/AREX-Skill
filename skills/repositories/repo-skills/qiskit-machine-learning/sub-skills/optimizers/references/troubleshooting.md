# Optimizer troubleshooting

## Import or optional dependency failures

- `from qiskit_machine_learning.optimizers import ...` fails before an
  optimizer is constructed: verify the public package installation and its
  compatible Qiskit dependency. Do not import from an old
  `qiskit.algorithms.optimizers` path for this package.
- Constructing `CRS`, `DIRECT_L`, `DIRECT_L_RAND`, `ESCH`, `ISRES`, or `SBPLX`
  raises `MissingOptionalLibraryError`: this is expected when `nlopt` is not
  installed. Install `nlopt` using the public platform instructions, or select
  a CPU fallback (`SLSQP`, `L_BFGS_B`, `POWELL`, or `UMDA`) and record the
  algorithm change. Do not catch every exception and silently fall back; a
  malformed objective or invalid bounds must remain visible.
- Optional NLopt imports can be present while native binary loading fails.
  Treat that as an environment/installation failure, not as evidence that the
  optimizer supports unbounded variables. Reinstall a compatible wheel or use
  a fallback.

## Objective and gradient shape errors

- The objective should accept a one-dimensional NumPy vector and return one
  scalar for an ordinary call. A batched finite-difference call can pass an
  array of multiple points; only enable `max_evals_grouped > 1` if the
  objective explicitly handles that shape and returns one value per point.
- A supplied `jac` must return one component per parameter. `GradientDescent`
  raises `ValueError` on a mismatched shape; SciPy gradients are flattened by
  the wrapper, which can hide an accidental extra dimension, so validate the
  shape yourself.
- If a gradient appears unused, inspect `get_support_level()`. `SPSA`,
  `QNSPSA`, `COBYLA`, `NELDER_MEAD`, `POWELL`, `GSLS`, `AQGD`, `UMDA`, and
  NLopt classes have no ordinary supplied-gradient path in their support
  contract. `SciPyOptimizer` removes `jac` before calling methods classified as
  gradient-ignoring.
- A `None` objective value, object dtype, NaN, or infinity can break SciPy and
  stochastic updates. Convert backend results to a finite scalar and handle
  failed hardware evaluations with an explicit retry or sentinel policy.

## Bounds are not respected

- First print `optimizer.get_support_level()` and confirm `bounds` is
  `supported` or `required`. `ignored` means the Qiskit optimizer may discard
  the argument; it is not a warning that should be overridden.
- The Qiskit wrapper classifies `COBYLA` bounds as ignored. `GradientDescent`,
  `ADAM`, `AQGD`, `SPSA`, `QNSPSA`, and `UMDA` also ignore bounds. Choose
  `L_BFGS_B`, `SLSQP`, `TNC`, `POWELL`, `GSLS`, or an NLopt class instead.
- For NLopt, use one finite `(lower, upper)` pair per coordinate and ensure
  `x0` is in those bounds. The implementation replaces missing limits with
  finite thresholds, so `None` is not an unlimited global domain.
- For a required physical domain with an ignored-bound optimizer, use an
  explicit variable transformation or a projected objective and document that
  the transformed/projected problem is being optimized.

## Noisy or unstable convergence

- Seed `algorithm_globals.random_seed` before SPSA, QNSPSA, GSLS, UMDA, or
  P-BFGS. Also seed any primitive and objective-side random generator. A
  NumPy-only seed does not control the package's `algorithm_globals.random`.
- SPSA's default calibration costs extra calls. Supply both
  `learning_rate` and `perturbation` to avoid calibration, and ensure arrays
  or iterator factories have at least `maxiter` values.
- Increase SPSA `resamplings` to reduce gradient variance, at the cost of two
  objective evaluations per sample for first-order SPSA and four more per
  sample when `second_order=True`. Use `blocking=True` with an explicit or
  calibrated `allowed_increase` when rejecting harmful noisy updates is
  valuable.
- Do not require a noisy objective to decrease at every accepted step. Use
  `termination_checker` based on a moving average, repeated estimates, or a
  known evaluation budget. Remember that a final `result.fun` may be a fresh
  noisy evaluation.
- `QNSPSA` adds fidelity calls and needs a working ansatz/sampler fidelity
  function. If the fidelity is noisy or incompatible, use SPSA first and
  compare under the same measurement budget.

## Learning-rate and termination problems

- `GradientDescent` raises `ValueError` when a list/array learning-rate
  schedule is shorter than `maxiter`. A callable is expected to return an
  iterator. Check the first few values for finite, positive, appropriately
  scaled steps.
- A gradient-descent run stops when the last gradient norm is no larger than
  `tol` or when `nit` reaches `maxiter`; `tol` is not an objective-value
  tolerance. A very small finite-difference `perturbation` can turn backend
  noise into a useless gradient.
- SPSA's `maxiter` is an iteration count, not an objective-call cap. Use the
  result's `nfev` and method-specific max-evaluation options to enforce a
  measurement budget.
- `AQGD` accepts scalar or aligned lists for `maxiter`, `eta`, and `momentum`.
  A length mismatch raises `AlgorithmError`; `momentum` must be in `[0, 1)`.
  Its no-`jac` finite/parameter-shift-like evaluation costs
  `2 * dimension + 1` objective values per update.

## Callback problems

- Direct callbacks are not uniform:
  - `SPSA`/`QNSPSA`: `(nfev, point, fvalue, stepsize, accepted)`.
  - `GradientDescent`: `(nfev, parameters, function_value, gradient_norm)`.
  - `ADAM`: `(time_step, parameters, function_value)`.
  - `UMDA`: `(nfev, best_parameters, best_function_value)`.
- SciPy callbacks are forwarded to SciPy and commonly receive the current
  point; model-level callbacks can instead be called from the objective in
  `TrainableModel`. Check which object owns the callback before changing its
  signature.
- If callback logging changes the result, check whether the callback is
  re-evaluating a noisy objective. Pass the value supplied by the optimizer
  rather than calling `fun` again.
- A callback that raises stops the optimizer. Wrap only known, recoverable
  logging failures; do not hide numerical exceptions.

## Steppable workflow errors

- `GradientDescent.state` is `None` until `start`. Call `start(fun, x0, jac)`
  before `ask`, `evaluate`, `tell`, or `step`.
- `ask()` returns `AskData(x_jac=...)` for gradient descent. Evaluate that
  point, create `TellData(eval_jac=gradient)`, and pass both objects to
  `tell()`. A gradient of the wrong shape raises `ValueError`.
- If an external evaluator retries, increment the state counters only for
  evaluations actually performed and make sure `nit` advances exactly once
  per accepted update. For ordinary use, let `evaluate()` and `step()` manage
  counters.
- Do not reuse a partially advanced `LearningRate` schedule as if it were
  fresh. Call `start()` for a new run and construct a new optimizer if the
  schedule's lifetime is ambiguous.

## Settings, snapshots, and reproducibility

- `settings` is intended for configuration reconstruction, but callables and
  primitives/fidelity functions are not automatically JSON serializable.
  SPSA/QNSPSA callable schedules are expanded to arrays in settings; this can
  be large and loses the original factory identity.
- ADAM snapshots require an existing `adam_params.csv` in the configured
  directory. `save_params` appends rather than overwrites. Load only into a
  matching ADAM/AMSGRAD configuration and do not treat CSV state as a portable
  optimizer configuration.
- If two nominally identical runs differ, compare package versions, initial
  points, optimizer settings, `algorithm_globals.random_seed`, primitive seeds,
  objective noise, and callback side effects. Compare `nfev` as well as final
  objective values.

## Fast diagnostic sequence

1. Replace the objective with a bounded two-variable quadratic and run the
   bundled `optimizer_smoke.py`.
2. Print `type(optimizer).__name__`, `optimizer.settings`, and
   `optimizer.get_support_level()`.
3. Run with `maxiter`/evaluation limits of 1–5 and a deterministic objective;
   verify callback arity and counter changes.
4. Reintroduce gradients, bounds, batching, noise, and quantum primitives one
   at a time. The first changed layer is the likely fault boundary.
