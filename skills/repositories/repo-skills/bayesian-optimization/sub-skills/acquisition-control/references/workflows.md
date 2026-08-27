# Acquisition Workflows

Use these workflows to choose, tune, and extend acquisition behavior without relying on original examples or notebooks.

## 1. Select an acquisition strategy

| Situation | Recommended acquisition | Why | Avoid |
|---|---|---|---|
| Unconstrained optimization, general-purpose starting point | `UpperConfidenceBound(kappa=2.576)` or the optimizer default | Good exploration/exploitation balance; default for unconstrained optimizer setup. | UCB if the optimizer has constraints. |
| Constrained optimization | Optimizer default `ExpectedImprovement(xi=0.01)` or explicit EI/PI | EI/PI multiply acquisition by constraint fulfillment probability through the standard acquisition wrapper. | UCB and Constant Liar; GPHedge portfolios containing UCB. |
| Need more exploration early, more exploitation later | UCB with high `kappa` plus decay, or EI/PI with high `xi` plus decay | Decay can reduce exploration automatically after suggestions. | Decay outside `(0, 1]` or negative/non-integer delay. |
| Need async/batch-like dummy suggestions | `ConstantLiar(UpperConfidenceBound(...), strategy='max')` or another unconstrained base acquisition | Tracks in-flight suggestions as dummies so workers are less likely to receive identical points. | Constrained target spaces; old `UtilityFunction` ask/tell snippets. |
| Unsure which acquisition family fits | `GPHedge([UpperConfidenceBound(...), ExpectedImprovement(...), ProbabilityOfImprovement(...)])` for unconstrained use | Lets a portfolio compete through softmax-weighted gains. | Too-small `n_random`/`n_smart`; constraint-incompatible base acquisitions. |
| Need problem-specific behavior | Custom `AcquisitionFunction` subclass | Encodes cost, greedy policy, Thompson sampling, or other custom score. | Saving/loading without state methods. |

## 2. Tune exploration and exploitation

### UCB

```python
from bayes_opt import BayesianOptimization, acquisition

acq = acquisition.UpperConfidenceBound(
    kappa=5.0,                    # larger means more exploration
    exploration_decay=0.95,       # multiply kappa after eligible suggest calls
    exploration_decay_delay=3,    # wait for three suggest calls before decay
)
optimizer = BayesianOptimization(
    f=None,
    pbounds={"x": (-2.0, 4.0)},
    acquisition_function=acq,
    random_state=7,
    verbose=0,
)
```

Use lower `kappa` such as `0.1` for exploitation-heavy search and higher `kappa` such as `5` or `10` when the function is multimodal or early exploration is valuable. Decay begins after successful acquisition suggestions; with delay `2`, the first suggestion leaves the value unchanged and the second can decay it.

### EI and PI

```python
acq = acquisition.ExpectedImprovement(
    xi=0.05,                      # larger requires more improvement and explores more
    exploration_decay=0.9,
    exploration_decay_delay=2,
)
```

Use `xi=0.0` or very small values for exploitation. Increase `xi` when suggestions cluster too tightly around the current best point. EI considers improvement magnitude; PI only considers improvement probability and can be greedier.

## 3. Seed observations before acquisition-driven suggestions

Lower-level acquisition calls need at least one observation. The optimizer-level method handles the empty case by random sampling.

```python
optimizer = BayesianOptimization(
    f=None,
    pbounds={"x": (-2.0, 4.0)},
    acquisition_function=acquisition.ExpectedImprovement(xi=0.01),
    random_state=7,
    verbose=0,
)

# These can come from historical measurements or explicit probes.
optimizer.register({"x": -1.0}, target=-4.29)
optimizer.register({"x": 0.0}, target=-0.69)
optimizer.register({"x": 2.5}, target=-0.44)

suggestion = optimizer.suggest()
```

For constrained EI/PI, at least one registered point must satisfy the constraint. Invalid constrained observations are useful data, but they do not provide the valid `y_max` required by EI/PI.

## 4. Use lower-level `suggest(...)` knobs

Use lower-level calls to reduce compute, make smoke tests deterministic, or tune smart optimizer effort.

```python
acq = acquisition.ProbabilityOfImprovement(xi=0.01)
optimizer = BayesianOptimization(
    f=None,
    pbounds={"x": (-2.0, 4.0)},
    acquisition_function=acq,
    random_state=7,
    verbose=0,
)
for x, y in [(-1.0, -4.29), (0.0, -0.69), (2.5, -0.44)]:
    optimizer.register({"x": x}, target=y)

raw = acq.suggest(
    gp=optimizer._gp,
    target_space=optimizer.space,
    n_random=512,
    n_smart=3,
    fit_gp=True,
    random_state=7,
)
params = optimizer.space.array_to_params(raw)
```

Guidelines:

- Keep `fit_gp=True` unless you have just fit the same GP on the same observations.
- Use `n_smart=0` for fast random-only smoke checks.
- Use larger `n_random` and `n_smart` for real optimization in higher dimensions.
- Do not set both budgets to zero.
- For GPHedge, multiply the desired per-acquisition budget by the number of base acquisitions because the portfolio divides the values across children.

## 5. Constant Liar ask-tell pattern for async workers

The safe current pattern is to pass `ConstantLiar` as `acquisition_function` and use `optimizer.suggest()` / `optimizer.register(...)`. Do not call old `optimizer.suggest(UtilityFunction(...))` patterns.

```python
from bayes_opt import BayesianOptimization, acquisition

base = acquisition.UpperConfidenceBound(
    kappa=10.0,
    exploration_decay=0.95,
    exploration_decay_delay=0,
)
async_acq = acquisition.ConstantLiar(base, strategy="max")

optimizer = BayesianOptimization(
    f=None,
    pbounds={"x": (-5.0, 5.0), "y": (-5.0, 5.0)},
    acquisition_function=async_acq,
    random_state=11,
    verbose=0,
)

# Register seed observations first.
optimizer.register({"x": -4.0, "y": -4.0}, target=-128.0)
optimizer.register({"x": 0.0, "y": 0.0}, target=0.0)
optimizer.register({"x": 3.0, "y": 2.0}, target=-13.0)

# Ask: issue suggestions to workers. Each call records a dummy internally.
in_flight = [optimizer.suggest() for _ in range(3)]

# Tell: as each worker returns, register the true result. Dummies are removed
# on later suggestions when registered points match within atol/rtol.
for params in in_flight:
    target = expensive_measurement(**params)
    optimizer.register(params=params, target=target)
```

Strategy choices:

- `strategy='max'`: optimistic lie; often useful for maximization when you want dummies to look attractive enough to reserve a region.
- `strategy='mean'`: moderate lie.
- `strategy='min'`: pessimistic lie; pushes workers away from pending locations.
- Numeric strategy: fixed dummy target value when the measurement scale is known.

Source script adaptation note: the safe dummy-suggestion pattern above adapts the current Constant Liar example. The older server-style async example is reference-only because it imports removed `UtilityFunction`, starts network services, and uses a stale `suggest` calling convention.

## 6. GPHedge portfolio acquisition

```python
portfolio = acquisition.GPHedge(
    base_acquisitions=[
        acquisition.UpperConfidenceBound(kappa=2.576),
        acquisition.ExpectedImprovement(xi=0.01),
        acquisition.ProbabilityOfImprovement(xi=0.01),
    ]
)
optimizer = BayesianOptimization(
    f=None,
    pbounds={"x": (-2.0, 4.0)},
    acquisition_function=portfolio,
    random_state=7,
    verbose=0,
)
```

Operational notes:

- GPHedge calls each base acquisition, stores the candidate list, and chooses among them by softmax of cumulative gains.
- The gains update on the next suggestion after the GP has been fit with new observations.
- `portfolio.base_acq(...)` is not meaningful; call `portfolio.base_acquisitions[i].base_acq(...)` for diagnostic calculations.
- Keep base-acquisition order stable across save/load.
- For constrained optimization, use only constraint-compatible base acquisitions such as EI/PI after valid constrained observations exist.

## 7. Custom acquisition subclass

Implement `base_acq`. Add state methods if optimizer state persistence is needed.

```python
import numpy as np
from bayes_opt import acquisition

class GreedyMean(acquisition.AcquisitionFunction):
    def __init__(self, offset: float = 0.0):
        super().__init__()
        self.offset = float(offset)

    def base_acq(self, mean, std):
        return np.asarray(mean) + self.offset

    def get_acquisition_params(self):
        return {"offset": self.offset}

    def set_acquisition_params(self, params):
        self.offset = float(params["offset"])
```

Use this with the optimizer:

```python
optimizer = BayesianOptimization(
    f=None,
    pbounds={"x": (-2.0, 4.0)},
    acquisition_function=GreedyMean(offset=0.0),
    random_state=7,
    verbose=0,
)
```

If the acquisition needs more than posterior mean/std, override `_get_acq(...)` or `suggest(...)`. For example, a cost-aware EI subclass can call `super()._get_acq(gp, constraint)` and divide the resulting minimization objective by a deterministic cost term. If the custom acquisition cannot handle constraints, raise `ConstraintNotSupportedError` when `constraint is not None`. If it can handle constraints through the standard wrapper, let the inherited `_get_acq(...)` multiply by constraint probability.

### Save/load with custom acquisitions

```python
optimizer.save_state("state.json")

# Later: recreate the same acquisition class first, then load.
new_optimizer = BayesianOptimization(
    f=None,
    pbounds={"x": (-2.0, 4.0)},
    acquisition_function=GreedyMean(offset=0.0),
    random_state=7,
    verbose=0,
)
new_optimizer.load_state("state.json")
```

The saved optimizer state stores acquisition parameters, not the Python class. Loading into the wrong custom class, or omitting `get_acquisition_params` / `set_acquisition_params`, is a usability bug.

## 8. Validate with the bundled probe

Run the helper from the `sub-skills/acquisition-control/` directory after package installation:

```bash
python scripts/acquisition_probe.py --include-constant-liar --include-gphedge
```

Use lower budgets for quick parser/runtime checks:

```bash
python scripts/acquisition_probe.py --n-random 64 --n-smart 3 --include-gphedge
```

The helper intentionally avoids plots, network calls, server startup, and original repository files.
