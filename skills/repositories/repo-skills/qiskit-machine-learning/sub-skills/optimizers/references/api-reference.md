# Optimizer API reference

This reference targets the public `qiskit-machine-learning` 1.0.0 optimizer
API evidenced by the package source and native optimizer tests. Confirm the
installed version's signature if a later release is being used.

## Common protocol

`Optimizer` exposes:

- `minimize(fun, x0, jac=None, bounds=None) -> OptimizerResult`.
- `get_support_level()`, returning levels for `gradient`, `bounds`, and
  `initial_point`.
- `set_options(**kwargs)` for implementation-specific options and
  `set_max_evals_grouped(limit)` for batched finite-difference or stochastic
  evaluations.
- support-level properties such as `is_gradient_ignored`,
  `is_bounds_supported`, and `is_initial_point_required`.

`OptimizerSupportLevel` means:

| Level | Meaning |
|---|---|
| `not_supported` | The argument is not a usable feature. |
| `ignored` | A non-`None` argument may be accepted but the optimizer does not use it. |
| `supported` | The optimizer uses the argument. |
| `required` | The argument must be supplied. |

`OptimizerResult` has `x`, `fun`, `jac`, `nfev`, `njev`, and `nit` properties.
Native implementations do not necessarily populate every property. Treat
`None` as “not reported”, not as zero. Some stochastic implementations call
`fun(result.x)` again to populate `fun`, so the final value can be a new noisy
sample.

## Support catalog

The following is the practical support classification in this package. A
wrapper may support a feature even if a newer SciPy release has gained a
related capability; use the Qiskit wrapper's classification as the contract.

| Export | Gradient | Bounds | Initial point | Best fit |
|---|---|---|---|---|
| `SciPyOptimizer(method)` | method-dependent | method-dependent | required | direct access to any SciPy method |
| `CG` | supported | ignored | required | smooth unconstrained objectives |
| `COBYLA` | ignored | ignored by wrapper | required | derivative-free constrained objective |
| `L_BFGS_B` | supported | supported | required | smooth objectives with simple bounds |
| `NELDER_MEAD` | ignored | ignored | required | low-dimensional, derivative-free local search |
| `NFT` | ignored by generic method classification | ignored | required | periodic/circuit objectives satisfying NFT assumptions |
| `P_BFGS` | supported | supported | required | L-BFGS-B with classical parallel restarts |
| `POWELL` | ignored | supported | required | derivative-free direction search with bounds |
| `SLSQP` | supported | supported | required | smooth bounds and constraints |
| `TNC` | supported | supported | required | gradient-based bounded problems |
| `ADAM` | supported (finite differences if `jac` omitted) | ignored | supported | adaptive first-order updates and noisy/sparse gradients |
| `AQGD` | ignored (internally estimates quantum gradients if `jac` omitted) | ignored | required | analytic quantum parameter-shift updates with epochs |
| `GradientDescent` | supported | ignored | required | explicit or finite-difference gradient descent |
| `GSLS` | ignored | supported | required | Gaussian-smoothed line search without a supplied gradient |
| `SPSA` | ignored | ignored | required | noisy objectives and hardware measurements |
| `QNSPSA` | ignored | ignored | required | SPSA with a fidelity-derived natural-gradient preconditioner |
| `UMDA` | ignored | ignored | required | stochastic population/distribution search |
| NLopt family | ignored | supported | required | optional global/local derivative-free search |

`SciPyOptimizer` classifies bounds as supported for `l-bfgs-b`, `tnc`, `slsqp`,
`powell`, and `trust-constr`. It classifies gradients as supported for `cg`,
`bfgs`, `newton-cg`, `l-bfgs-b`, `tnc`, `slsqp`, `dogleg`, `trust-ncg`,
`trust-krylov`, `trust-exact`, and `trust-constr`; other methods are treated as
ignoring the corresponding argument. It requires an initial point.

## SciPy wrappers and settings

All named SciPy wrappers delegate to `scipy.optimize.minimize` through
`SciPyOptimizer`. `options` is a dictionary for the underlying method and
extra constructor keyword arguments are forwarded to SciPy. `settings` splits
known wrapper options from the remaining `options`, includes
`max_evals_grouped`, and includes `method` when the class is exactly
`SciPyOptimizer`.

Notable public constructor shapes include:

```python
COBYLA(maxiter=1000, disp=False, rhobeg=1.0, tol=None,
       options=None, **kwargs)
SPSA(maxiter=100, blocking=False, allowed_increase=None,
     trust_region=False, learning_rate=None, perturbation=None,
     last_avg=1, resamplings=1, perturbation_dims=None,
     second_order=False, regularization=None, hessian_delay=0,
     lse_solver=None, initial_hessian=None, callback=None,
     termination_checker=None)
```

Use the installed `inspect.signature` for less common wrapper details. The
common examples are `L_BFGS_B(maxfun=..., maxiter=..., options=...)`,
`SLSQP(maxiter=..., ftol=..., tol=...)`, `POWELL(maxfev=..., xtol=...)`, and
`NELDER_MEAD(maxfev=..., xatol=...)`.

SciPy finite-difference batching is activated by `max_evals_grouped > 1` when
a supported gradient is omitted. The objective must then accept the batched
array shape produced by the wrapper; set it to `1` when it cannot batch.
Gradients are flattened to one dimension before SciPy receives them.

## Gradient and adaptive optimizers

### `GradientDescent`

`GradientDescent(maxiter=100, learning_rate=0.01, tol=1e-7,
callback=None, perturbation=None)` accepts a float, list/array, or generator
factory for `learning_rate`. A list/array must contain at least `maxiter`
values. With no `jac`, it uses a forward finite-difference gradient with
`perturbation` (default `0.01`) and counts one base plus one evaluation per
parameter per step. With `jac`, it counts gradient evaluations instead.
`bounds` are ignored.

The callback receives `(nfev, parameters, function_value, gradient_norm)`.
`settings` expands a generator factory to an array of `maxiter` values, so it
may be a useful snapshot but not a portable representation of the factory.

### `ADAM`

`ADAM(maxiter=10000, tol=1e-6, lr=1e-3, beta_1=0.9, beta_2=0.99,
noise_factor=1e-8, eps=1e-10, amsgrad=False, snapshot_dir=None,
callback=None)` supports an analytic `jac` or finite differences. It ignores
bounds. The callback receives `(time_step, parameters, function_value)`. If
`snapshot_dir` is set, parameter state is appended to `adam_params.csv`; use
`load_params` on a compatible ADAM instance to restore that runtime state.

### `AQGD`

`AQGD` accepts scalar or same-length lists for `maxiter`, `eta`, and
`momentum`; `momentum` must lie in `[0, 1)`. `param_tol`, `tol`, `averaging`,
and `max_evals_grouped` control convergence and batching. With no `jac`, it
computes an analytic quantum parameter-shift estimate using positive and
negative `pi/2` shifts, requiring `2 * number_of_parameters + 1` objective
values per iteration. Its initial point is required and bounds are ignored.

## SPSA and QNSPSA

`SPSA` estimates a gradient with Bernoulli perturbations using a constant two
objective samples per stochastic direction, independent of parameter count.
`second_order=True` adds a Hessian estimate and regularized linear solve.
`resamplings` can be an integer or an `{iteration: count}` dictionary;
`perturbation_dims` can reduce the number of perturbed coordinates.
`blocking=True` evaluates a proposed point and rejects it when its loss
exceeds the current loss plus `allowed_increase`. If
`allowed_increase=None`, it is calibrated from an estimated loss standard
deviation. `trust_region=True` limits update norm to one, and `last_avg > 1`
returns an average of the last points.

If both `learning_rate` and `perturbation` are `None`, SPSA calibrates power
series and consumes calibration evaluations. If one is provided, both must be
provided. Each may be a float, an array/list with at least `maxiter` values,
or a callable returning an iterator. `termination_checker`, when present, is
called after accepted iterations with
`(nfev, point, fvalue, stepsize, accepted)` and a true result stops the loop.
The callback receives the same five values. `fun` and `jac` arguments to
`minimize` are not used as a supplied gradient by SPSA.

`QNSPSA(fidelity, ...)` subclasses SPSA and requires a fidelity function as
its first argument. `QNSPSA.get_fidelity(circuit, sampler=...)` returns a
fidelity callable for a parameterized circuit. QN-SPSA uses six evaluations per
sample direction (two loss and four fidelity evaluations), uses a natural-
gradient preconditioner, and disallows the SPSA trust region. It requires a
fidelity-compatible ansatz/primitives; it is not a generic replacement for
SPSA on a classical objective.

## Steppable protocol

`SteppableOptimizer` adds explicit state control:

```python
optimizer.start(fun=fun, x0=x0, jac=jac)
while optimizer.continue_condition():
    ask_data = optimizer.ask()
    tell_data = evaluate_or_retry(ask_data)
    optimizer.tell(ask_data, tell_data)
result = optimizer.create_result()
```

`step()` is the convenience composition of `ask`, `evaluate`, and `tell`;
`minimize()` runs `start` followed by repeated `step()` calls. `AskData` has
`x_fun` and `x_jac`; `TellData` has `eval_fun` and `eval_jac`. This interface
is appropriate when objective/gradient calls can fail, need retries, or are
provided by a remote evaluator. Calling `ask`, `step`, or `tell` before
`start` leaves no state and is an error.

## NLopt family

`CRS`, `DIRECT_L`, `DIRECT_L_RAND`, `ESCH`, `ISRES`, and `SBPLX` use the
optional `nlopt` package. `CRS`, `DIRECT_L`, `DIRECT_L_RAND`, `ESCH`, and
`ISRES` are global derivative-free algorithms; `SBPLX` is local Subplex.
`max_evals` controls the objective evaluation budget. Bounds are required by
the underlying global search concept; use finite `(lower, upper)` pairs. The
implementation substitutes finite `-3*pi` and `3*pi` thresholds for completely
unbounded dimensions, so do not interpret `bounds=None` as an unlimited
search domain.

Install the optional package with the public instructions `pip install nlopt`
on Windows/Linux or `brew install nlopt` on macOS. If it is absent, a
`MissingOptionalLibraryError` is expected at construction; use a CPU fallback
such as `SLSQP`, `L_BFGS_B`, `POWELL`, or `UMDA` according to the objective.
