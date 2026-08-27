# Optimizer workflows

All examples assume the public package is installed in the active environment.
They intentionally use small budgets; scale them only after checking objective
quality and evaluation cost.

## Ordinary minimize

```python
import numpy as np
from qiskit_machine_learning.optimizers import L_BFGS_B


def fun(x):
    return float(np.sum((x - np.array([1.0, 2.0])) ** 2))


def jac(x):
    return 2.0 * (x - np.array([1.0, 2.0]))

optimizer = L_BFGS_B(maxfun=200)
result = optimizer.minimize(
    fun=fun,
    x0=np.array([0.0, 0.0]),
    jac=jac,
    bounds=[(-2.0, 2.0), (-2.0, 3.0)],
)
assert result.x is not None
assert np.all(result.x >= [-2.0, -2.0])
assert np.all(result.x <= [2.0, 3.0])
print(result.x, result.fun, result.nfev, result.njev, result.nit)
```

Before the call, inspect `optimizer.get_support_level()`. A result may have a
valid `x` while an ignored `bounds` or `jac` was never used.

## COBYLA-style derivative-free training

```python
from qiskit_machine_learning.optimizers import COBYLA

optimizer = COBYLA(maxiter=100, rhobeg=0.5, tol=1e-6)
result = optimizer.minimize(fun, x0=[0.0, 0.0])
```

COBYLA is useful when derivatives are unavailable and constraints are encoded
for the underlying SciPy method, but this Qiskit wrapper reports `bounds` as
ignored. If simple bounds are a hard requirement, use `SLSQP`, `L_BFGS_B`,
`TNC`, `POWELL`, `GSLS`, or finite-bound NLopt instead.

## Gradient descent: analytic, finite-difference, and scheduled

With an analytic gradient:

```python
import numpy as np
from qiskit_machine_learning.optimizers import GradientDescent


def f(x):
    return float(np.dot(x, x))


def grad_f(x):
    return 2.0 * x

optimizer = GradientDescent(maxiter=50, learning_rate=0.1, tol=1e-8)
result = optimizer.minimize(f, x0=np.array([1.0, -1.0]), jac=grad_f)
```

Without `jac`, the implementation uses a forward finite difference with
`perturbation` (default `0.01`):

```python
optimizer = GradientDescent(maxiter=50, learning_rate=0.05, perturbation=1e-5)
result = optimizer.minimize(f, x0=np.array([1.0, -1.0]))
```

A schedule may be a list/array of at least `maxiter` values or a factory
returning an iterator. A short list raises `ValueError`. The callback, when
provided, receives `(nfev, parameters, function_value, gradient_norm)`.
`bounds` are ignored; enforce a domain through the objective or choose a
bound-aware optimizer instead.

## Stateful ask/tell loop

`GradientDescent` is the public steppable implementation. Use this form when
a remote evaluator or retry policy controls objective/gradient calls:

```python
import numpy as np
from qiskit_machine_learning.optimizers import GradientDescent


def f(x):
    return float(np.dot(x, x))


def grad_f(x):
    return 2.0 * x

class TransientEvaluationError(Exception):
    """Raised by an external evaluator for a retryable failure."""


optimizer = GradientDescent(maxiter=20, learning_rate=0.1)
optimizer.start(fun=f, jac=grad_f, x0=np.array([1.0, -1.0]))
while optimizer.continue_condition():
    ask_data = optimizer.ask()
    # A production evaluator may retry this call on a transient failure.
    try:
        tell_data = optimizer.evaluate(ask_data)
    except TransientEvaluationError:
        continue
    optimizer.tell(ask_data, tell_data)
result = optimizer.create_result()
```

If evaluation is performed outside `evaluate`, construct `TellData(eval_jac=...)`
(or `eval_fun=...`) and update `optimizer.state.njev`/`nfev` and `nit` for
measurements you actually perform. Do not call `ask`, `step`, or `tell` before
`start`. `step()` is simply `ask -> evaluate -> tell`; `minimize()` manages
that loop automatically.

## SPSA for noisy objectives

Use the Qiskit random generator and make both schedules explicit when the
objective is noisy and a fixed evaluation budget is useful:

```python
from qiskit_machine_learning.optimizers import SPSA
from qiskit_machine_learning.utils import algorithm_globals

algorithm_globals.random_seed = 1376
optimizer = SPSA(
    maxiter=100,
    learning_rate=0.02,
    perturbation=0.05,
    blocking=True,
    allowed_increase=0.0,
    resamplings=2,
    callback=lambda nfev, point, value, step, accepted: print(
        nfev, value, step, accepted
    ),
)
result = optimizer.minimize(noisy_loss, x0=initial_point)
```

The callback and `termination_checker` each receive
`(nfev, point, fvalue, stepsize, accepted)`. A checker returning `True` stops
the loop after an accepted step. Use a custom checker for noisy convergence
rather than requiring a single noisy `fun` value to be monotonic.

If `learning_rate` and `perturbation` are both omitted, SPSA calibrates them
from extra calls. If only one is specified, the run raises `ValueError`. An
array or iterator schedule must be long enough for the requested iterations.
`blocking=True` performs a candidate evaluation and can reject updates;
`allowed_increase=None` estimates a noise allowance from repeated samples.

`SPSA` does not enforce `bounds`. If a physical parameter domain is mandatory,
use a bound-aware optimizer, or explicitly reparameterize the domain and state
that the optimization variables are transformed.

## QNSPSA with fidelity

For a parameterized circuit, construct the fidelity callable with the public
helper and pass it as the required first argument:

```python
from qiskit_machine_learning.optimizers import QNSPSA

fidelity = QNSPSA.get_fidelity(ansatz, sampler=sampler)
optimizer = QNSPSA(
    fidelity,
    maxiter=100,
    learning_rate=0.05,
    perturbation=0.05,
    regularization=1e-3,
    blocking=True,
)
result = optimizer.minimize(loss, x0=initial_point)
```

The sampler and ansatz must be compatible with the installed primitives.
QN-SPSA's fidelity evaluations are additional to loss evaluations; use it when
the natural-gradient geometry is worth that measurement cost. Do not pass a
classical callable as `fidelity` unless it implements the required two-point
fidelity semantics.

## Optional NLopt and fallback

Probe the optional dependency at the point of use. The package documents
`pip install nlopt` for Windows/Linux and `brew install nlopt` for macOS:

```python
from qiskit_machine_learning.optimizers import SLSQP

bounds = [(-5.0, 5.0), (-5.0, 5.0)]
try:
    from qiskit_machine_learning.optimizers import DIRECT_L
    optimizer = DIRECT_L(max_evals=200)
    result = optimizer.minimize(fun, x0=[0.0, 0.0], bounds=bounds)
except Exception as exc:
    # Narrow this to MissingOptionalLibraryError in production; this broad
    # example keeps the fallback policy visible without version assumptions.
    if exc.__class__.__name__ != "MissingOptionalLibraryError":
        raise
    optimizer = SLSQP(maxiter=100)
    result = optimizer.minimize(fun, x0=[0.0, 0.0], bounds=bounds)
```

The NLopt implementation uses finite bounds for the search and substitutes
`[-3*pi, 3*pi]` for missing limits. A fallback changes the algorithm and must
be reported in experiment metadata. Keep `max_evals` small for a smoke test.

## Callback and model embedding

Optimizer callbacks have different arities. For direct use, attach the
optimizer-specific callback shown in the API reference. When a `TrainableModel`
uses a non-`SciPyOptimizer` optimizer with a `callback` attribute, the model
can assign its model callback to that attribute; SciPy wrappers instead receive
model callbacks through the objective wrapper. Therefore, when debugging VQC,
VQR, or another trainable model, inspect the algorithms skill rather than
assuming the direct optimizer callback convention.

## Settings and state persistence

For stateless configuration capture:

```python
settings = optimizer.settings
# Recreate with the same optimizer class when values are portable.
restored = type(optimizer)(**settings)
```

This is tested for named SciPy wrappers and the basic optimizer settings, but
callables are not JSON serializable. SPSA/QNSPSA settings expand generator
factories to arrays and QNSPSA includes its fidelity callable. ADAM's
`snapshot_dir` writes `adam_params.csv`; call `save_params`/`load_params` only
with a compatible ADAM configuration and an existing snapshot file. Do not
serialize a live `state` object as if it were a settings dictionary.

## Batching

`qiskit_machine_learning.utils.set_batching._set_default_batchsize` sets
`max_evals_grouped` to `50` only when the optimizer is an SPSA instance and
its value is `None`; it leaves other optimizers unchanged. For a custom
objective that cannot accept a batch, keep `max_evals_grouped=1` (the default)
and do not invoke this helper blindly.
