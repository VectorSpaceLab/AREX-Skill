# Variable and Operator Workflows

## Mixed-variable optimization

Use explicit variables and `MixedVariableGA` when candidates combine real,
integer, binary, and categorical values.

```python
from pymoo.core.problem import ElementwiseProblem
from pymoo.core.variable import Real, Integer, Binary, Choice
from pymoo.core.mixed import MixedVariableGA
from pymoo.optimize import minimize

class MixedToy(ElementwiseProblem):
    def __init__(self):
        vars = {
            "x": Real(bounds=(0.0, 1.0)),
            "n": Integer(bounds=(0, 5)),
            "flag": Binary(),
            "mode": Choice(options=["cheap", "accurate"]),
        }
        super().__init__(vars=vars, n_obj=1)

    def _evaluate(self, x, out, *args, **kwargs):
        penalty = 0.0 if x["mode"] == "accurate" else 0.2
        out["F"] = (x["x"] - 0.3) ** 2 + abs(x["n"] - 2) + penalty + (0.0 if x["flag"] else 0.1)

res = minimize(MixedToy(), MixedVariableGA(pop_size=20), ("n_gen", 5), seed=1, verbose=False)
print(res.X, res.F)
```

Checklist:
- The problem receives a dictionary `x` for elementwise evaluation.
- Keep categorical options explicit and stable.
- Validate result types (`int`, `bool`, option membership) after a smoke run.
- For multi-objective mixed-variable problems, `MixedVariableGA` is a GA base; if
  a task needs MOO behavior, review survival/output choices carefully or use a
  compatible algorithm/mating strategy.

## Integer variables with real-coded operators

If an algorithm uses SBX/PM on integer-like arrays, add rounding repair:

```python
from pymoo.operators.crossover.sbx import SBX
from pymoo.operators.mutation.pm import PM
from pymoo.operators.repair.rounding import RoundingRepair

crossover = SBX(vtype=float, repair=RoundingRepair())
mutation = PM(vtype=float, repair=RoundingRepair())
```

Also check bounds after rounding. If the task has many heterogeneous types,
prefer `vars={...}` and `MixedVariableGA`.

## Custom string/object operator pattern

For object-valued variables such as strings, routes, subsets, or trees:

1. Use `ElementwiseProblem` so `_evaluate` gets one Python object at a time.
2. Create sampling that returns an object array.
3. Create crossover with `dtype=object` and the required output shape.
4. Create mutation that preserves valid object invariants.
5. Create duplicate elimination that compares semantic equality, not object IDs.

Skeleton:

```python
import numpy as np
from pymoo.core.sampling import Sampling
from pymoo.core.crossover import Crossover
from pymoo.core.mutation import Mutation
from pymoo.core.duplicate import ElementwiseDuplicateElimination

class StringSampling(Sampling):
    def _do(self, problem, n_samples, **kwargs):
        X = np.empty((n_samples, 1), dtype=object)
        for i in range(n_samples):
            X[i, 0] = "abc"  # replace with a random valid string
        return X

class StringCrossover(Crossover):
    def __init__(self):
        super().__init__(2, 2)

    def _do(self, problem, X, **kwargs):
        Y = np.empty_like(X, dtype=object)
        # X shape: (2, n_matings, 1); Y shape: (2, n_matings, 1)
        for k in range(X.shape[1]):
            a, b = X[0, k, 0], X[1, k, 0]
            cut = len(a) // 2
            Y[0, k, 0] = a[:cut] + b[cut:]
            Y[1, k, 0] = b[:cut] + a[cut:]
        return Y

class StringMutation(Mutation):
    def _do(self, problem, X, **kwargs):
        # Modify and return X with shape (n_individuals, 1)
        return X

class StringDuplicate(ElementwiseDuplicateElimination):
    def is_equal(self, a, b):
        return a.X[0] == b.X[0]
```

## Permutation or routing problems

Use permutation-aware sampling/crossover/mutation instead of treating a
permutation as independent integers. Preserve each item exactly once after every
operator. Common checks:

```python
assert sorted(route) == list(range(n_items))
assert len(set(route)) == n_items
```

If a route must satisfy additional constraints, add a repair operator that fixes
or rejects invalid permutations after variation.

## Initial populations

Common initialization routes:

- **Random default sampling**: pass no sampling or a sampling operator.
- **Initial array**: provide a NumPy array of candidate rows through the
  algorithm's `sampling` argument when the algorithm accepts arrays.
- **Evaluated population**: construct a `Population` with `X` and precomputed
  `F`/`G` only when you are certain those values match the problem and evaluator
  expectations.
- **Not-yet-evaluated population**: pass candidate rows and let pymoo evaluate
  them during setup.

Validate shapes and bounds before relying on an initial population. A malformed
initial population can fail inside algorithm setup or silently bias the run.

## Repair workflow

Use repair when validity can be restored without re-running the expensive
objective:

```python
from pymoo.core.repair import Repair

class SumToOneRepair(Repair):
    def _do(self, problem, X, **kwargs):
        X = X.clip(problem.xl, problem.xu)
        denom = X.sum(axis=1, keepdims=True)
        denom[denom == 0.0] = 1.0
        return X / denom
```

Repair is especially useful for equality-like constraints, integer rounding,
bounds, portfolio weights, or permutation validity. Document whether repair
changes the mathematical problem or only maps invalid encodings back into a
valid representation.

## Hyperparameter helper workflow

```python
from pymoo.core.parameters import get_params, flatten, hierarchical, set_params

params = flatten(get_params(algorithm))
# choose or optimize new values, then:
set_params(algorithm, hierarchical(new_flat_params))
```

For automated hyperparameter search, `HyperparameterProblem` wraps an algorithm
and a performance measure. Keep budgets tiny for smoke tests and compare multiple
seeds before making research claims. Optional `optuna` integration requires the
optional dependency; base pymoo can use `MixedVariableGA` as a tuner in examples.

## Operator validation checklist

- Sampling returns the number of requested rows.
- Crossover returns exactly `n_offsprings` for every mating.
- Mutation preserves row count and valid value types.
- Repair preserves bounds and domain invariants.
- Duplicate elimination agrees with the semantic equality of your encoding.
- A tiny optimization run completes with `res.F` finite and candidate values
  valid under your problem's invariants.
