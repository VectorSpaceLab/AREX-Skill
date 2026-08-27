---
name: optimizers
description: "Select, configure, run, and troubleshoot Qiskit Machine Learning
  optimizers for classical objectives and variational training, including SciPy
  wrappers, SPSA/QNSPSA, gradient and steppable workflows, bounds, callbacks,
  serialization, and optional NLopt."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Optimizers

Use this skill when a downstream task must minimize a scalar objective over
parameter vectors with `qiskit_machine_learning.optimizers`. It covers the
optimizer contract and optimizer-specific behavior. It does **not** design a
VQC/VQR or other trainable model, and it does not implement quantum gradients;
route model embedding to `algorithms` and gradient construction to
`qnn-gradients`.

## Fast route

1. Define `fun(x) -> scalar`, a one-dimensional initial point `x0`, and, when
   available, `jac(x) -> gradient`. Decide whether the objective is smooth,
   noisy, constrained/bounded, or requires a global search.
2. Use the decision table in [optimizer-selection.md](references/optimizer-selection.md).
   Prefer `minimize(fun, x0, jac=jac, bounds=bounds)` for an ordinary run.
3. Check `get_support_level()` before trusting `jac` or `bounds`; `ignored` is
   not the same as `supported`. The support matrix and constructor facts are in
   [api-reference.md](references/api-reference.md).
4. Use [workflows.md](references/workflows.md) for ordinary, noisy, ask/tell,
   QN-SPSA, serialization, and optional-NLopt procedures.
5. Interpret `OptimizerResult` and verify that the final point is feasible and
   that the reported objective was evaluated under the same noise/seed policy.
   If anything fails, use [troubleshooting.md](references/troubleshooting.md).

## Public entry points

```python
from qiskit_machine_learning.optimizers import (
    ADAM, AQGD, CG, COBYLA, GSLS, GradientDescent, L_BFGS_B,
    NELDER_MEAD, NFT, P_BFGS, POWELL, QNSPSA, SLSQP, SPSA, TNC,
    UMDA, SciPyOptimizer,
)
```

The optional NLopt-backed exports are `CRS`, `DIRECT_L`, `DIRECT_L_RAND`,
`ESCH`, `ISRES`, and `SBPLX`. Instantiate them only after checking the
optional dependency. Do not silently substitute an unsupported optimizer:
choose a documented CPU fallback when NLopt is unavailable.

## Guardrails

- Every ordinary optimizer consumes `fun`, `x0`, optional `jac`, and optional
  `bounds`, and returns an `OptimizerResult`; most optimizers require an
  initial point even when their support level says it is merely supported.
- Bounds are a list of `(lower, upper)` pairs aligned with `x0`. Do not pass
  bounds to an optimizer whose level is `ignored` and then assume they were
  enforced. Use `L_BFGS_B`, `SLSQP`, `TNC`, `POWELL`, `GSLS`, or finite-bound
  NLopt when bound enforcement is required.
- `SPSA` and `QNSPSA` are stochastic. Set
  `qiskit_machine_learning.utils.algorithm_globals.random_seed` before the run
  when reproducibility matters; a NumPy seed alone is not a substitute.
- If only one of SPSA's `learning_rate` and `perturbation` is supplied,
  construction of the run raises `ValueError`. Supplying neither invokes
  calibration and consumes extra objective evaluations.
- Callback signatures are optimizer-specific. Never reuse a callback written
  for one optimizer without adapting its arguments. Model-level callback
  behavior belongs to `algorithms`, not this skill.
- `settings` is a configuration snapshot, not generally a live optimizer
  state. Callables, fidelity functions, termination checkers, and custom linear
  solvers are not JSON values. ADAM has a separate CSV snapshot mechanism.

## Verification checklist

Before handing off an optimizer choice, check: import path; constructor
signature; support levels; objective and gradient shapes; finite bounds when
required; seed and evaluation budget; callback arity; `result.x` feasibility;
and `result.fun`, `nfev`, and `nit` interpretation. Run the bundled smoke
script from any working directory with `python .../optimizer_smoke.py --help`
or a small installed-package invocation using
[scripts/optimizer_smoke.py](scripts/optimizer_smoke.py).

Read the linked references progressively rather than loading the entire
catalog into every optimization task.
