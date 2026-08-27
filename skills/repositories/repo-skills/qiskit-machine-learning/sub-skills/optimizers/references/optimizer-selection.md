# Optimizer selection

Choose from the objective's evaluation model first, then from bounds,
gradients, and budget. These are starting policies, not convergence
promises; validate on a small deterministic objective before a costly
variational run.

## Decision table

| Situation | First choice | Alternatives and caveats |
|---|---|---|
| Smooth objective with analytic gradient | `SLSQP` (with bounds/constraints) or `L_BFGS_B` (simple bounds) | `CG` for unconstrained smooth problems; `TNC` for bounded gradient problems |
| Smooth objective, no analytic gradient | `COBYLA`, `POWELL`, or `NELDER_MEAD` | `COBYLA` is derivative-free but the Qiskit wrapper reports bounds as ignored; use `POWELL`/`SLSQP` when bounds matter |
| Hardware or shot noise | `SPSA` | Set the Qiskit `algorithm_globals` seed; use blocking, resampling, and a termination checker intentionally |
| Noisy objective with a useful gradient estimate | `GradientDescent` or `ADAM` | Tune learning rate and check gradient variance; do not pass bounds to either |
| Need a natural-gradient-like stochastic update | `QNSPSA` | Requires a fidelity callable for the ansatz and costs four additional fidelity samples per perturbation direction |
| Need explicit retry/batching/control of evaluations | `GradientDescent` through `start`/`ask`/`tell` | The steppable API is currently implemented by `GradientDescent`; do not assume every optimizer supports it |
| Quantum analytic parameter-shift update | `AQGD` | It internally evaluates shifted objective points; route gradient construction itself to `qnn-gradients` |
| Population/distribution search | `UMDA` | Stochastic, seed with `algorithm_globals`, and budget by `size_gen * maxiter` |
| Global derivative-free bounded search | NLopt `CRS`, `DIRECT_L`, `DIRECT_L_RAND`, `ESCH`, or `ISRES` | Optional dependency; use finite bounds and a fallback if `nlopt` is unavailable |
| Local derivative-free bounded search with NLopt | `SBPLX` | Optional dependency and finite-bound implementation behavior |
| Need any SciPy method not wrapped by a named class | `SciPyOptimizer(method, options=...)` | Its Qiskit support classification determines whether `jac`/`bounds` are forwarded |

`TrainableModel` (and therefore VQC/VQR and related models) defaults to
`SLSQP()` when no optimizer is supplied. It accepts either an `Optimizer`
instance or a callable implementing the `Minimizer` protocol. Keep this
routing in the algorithms skill when embedding an optimizer in VQC/VQR.

## Selection procedure

1. **Characterize the objective.** Record parameter dimension, smoothness,
   stochasticity, evaluation cost, periodicity, constraints, and whether one
   call can evaluate a batch of points.
2. **Choose derivative mode.** Use analytic `jac` only if its shape is exactly
   the parameter vector shape. If no gradient is available, choose a method
   that ignores gradients rather than expecting the wrapper to invent one.
   `SciPyOptimizer` can finite-difference a supported gradient method; for
   `max_evals_grouped > 1`, the objective must accept the resulting batch.
3. **Apply bounds.** Build one `(lower, upper)` pair per variable. Query
   `get_support_level()` and reject an optimizer that reports bounds as
   `ignored` when feasibility is a hard requirement. Clip an out-of-range
   initial point yourself before NLopt and document the change.
4. **Set a budget.** Distinguish iterations (`maxiter`) from objective calls
   (`nfev`/`maxfev`/`maxfun`/`max_eval`/`max_evals`). SPSA calibration,
   blocking, callbacks, finite differences, batching, and QN-SPSA fidelity
   evaluations add calls.
5. **Set randomness policy.** Set
   `qiskit_machine_learning.utils.algorithm_globals.random_seed` before SPSA,
   QNSPSA, GSLS, UMDA, or P-BFGS. Record package versions and objective noise
   settings. A seed makes a stochastic procedure repeatable only when the
   objective and primitives are also deterministic under that seed.
6. **Run a pilot.** Check `result.x`, `result.fun`, `result.nfev`, and `result.nit`
   plus bound feasibility and callback records. Compare a second optimizer only
   when its support and evaluation budget are comparable.

## Practical defaults

### Low-noise smooth training

Start with `SLSQP(maxiter=...)` when bounds or constraints may be needed, or
`L_BFGS_B(maxfun=...)` for simple bounds. Supply the model's gradient if it is
verified. If no gradient is supplied, use a derivative-free method or let a
supported SciPy wrapper finite-difference with `max_evals_grouped=1` unless
batching is explicitly implemented.

### Hardware-noisy training

Start with `SPSA(maxiter=..., learning_rate=..., perturbation=...)` when
repeatable evaluation cost matters. Supplying both schedules avoids calibration
calls and makes the schedule explicit. Use `blocking=True` only when an
additional candidate evaluation and a loss comparison are acceptable. Increase
`resamplings` to reduce stochastic gradient variance at a proportional
objective cost. `QNSPSA` is justified when a circuit-specific fidelity
primitive is available and the natural-gradient preconditioner is worth its
additional measurements.

### Hard simple bounds

Prefer `L_BFGS_B`, `SLSQP`, `TNC`, `POWELL`, `GSLS`, or finite-bound NLopt.
Do not choose `COBYLA`, `GradientDescent`, `ADAM`, `SPSA`, `QNSPSA`, `AQGD`, or
`UMDA` and assume the bounds are enforced: their support level is ignored.
For ignored-bound optimizers, reparameterize the objective or project points
inside the objective only if that altered objective is explicitly intended.

### Multimodal/global search

Use an NLopt global class only with an optional-install check, finite bounds,
and an evaluation budget. If the dependency is unavailable or the environment
is CPU-only without the optional package, fall back to a supported local
optimizer or `UMDA`; report that this is a change of search strategy, not an
equivalent replacement.
