# Operator API Reference

This reference summarizes pymoo search-space and operator APIs. Problem
formulation and optimizer execution are sibling sub-skills.

## Variable classes

```python
from pymoo.core.variable import Real, Integer, Binary, Choice

vars = {
    "length": Real(bounds=(0.0, 1.0)),
    "count": Integer(bounds=(0, 10)),
    "enabled": Binary(),
    "mode": Choice(options=["fast", "accurate"]),
}
```

Verified constructors:

| Class | Minimal constructor | Use |
| --- | --- | --- |
| `Real` | `Real(value=None, bounds=(None, None), strict=None, **kwargs)` | Bounded continuous variables. |
| `Integer` | `Integer(value=None, bounds=(None, None), strict=None, **kwargs)` | Integer variables; upper bound required for sampling. |
| `Binary` | `Binary(value=None, bounds=(None, None), strict=None, **kwargs)` | Boolean variables. |
| `Choice` | `Choice(value=None, options=None, all=None, **kwargs)` | Categorical/discrete values. |

Use a variable dict with `Problem(vars=vars, ...)` and a compatible mixed-variable
algorithm. Ordinary float-coded algorithms will not automatically respect
categorical values.

## Mixed-variable classes

```python
from pymoo.core.mixed import (
    MixedVariableGA,
    MixedVariableSampling,
    MixedVariableMating,
    MixedVariableDuplicateElimination,
)
```

Verified `MixedVariableGA` signature:

```python
MixedVariableGA(pop_size=50, n_offsprings=None, output=..., sampling=...,
                mating=..., eliminate_duplicates=..., survival=..., **kwargs)
```

Default mixed-variable mating maps variable classes to suitable crossover and
mutation defaults:

- `Binary` -> uniform crossover and bitflip mutation.
- `Real` -> SBX crossover and polynomial mutation.
- `Integer` -> SBX/PM with rounding repair.
- `Choice` -> uniform crossover and choice-random mutation.

## Sampling operators

| Import | Use |
| --- | --- |
| `from pymoo.operators.sampling.rnd import FloatRandomSampling` | Random real-valued samples inside bounds. |
| `from pymoo.operators.sampling.rnd import BinaryRandomSampling` | Binary bit vectors. |
| `from pymoo.operators.sampling.rnd import IntegerRandomSampling` | Integer samples. |
| `from pymoo.operators.sampling.rnd import PermutationRandomSampling` | Permutation encodings. |
| `from pymoo.operators.sampling.lhs import LHS` | Latin-hypercube sampling for continuous spaces. |
| `from pymoo.core.sampling import Sampling` | Base class for custom sampling. |

Custom sampling contract:

```python
class MySampling(Sampling):
    def _do(self, problem, n_samples, **kwargs):
        X = ...  # shape (n_samples, problem.n_var) or object-compatible rows
        return X
```

## Crossover operators

| Import | Use |
| --- | --- |
| `from pymoo.operators.crossover.sbx import SBX` | Simulated binary crossover for real/integer-with-repair variables. |
| `from pymoo.operators.crossover.ux import UX` | Uniform crossover, often binary/choice/object-compatible. |
| `from pymoo.operators.crossover.hux import HUX` | Half-uniform binary crossover. |
| `from pymoo.operators.crossover.ox import OrderCrossover` | Permutation/order crossover. |
| `from pymoo.operators.crossover.dex import DEX` | Differential-evolution style crossover. |
| `from pymoo.core.crossover import Crossover` | Base class for custom crossover. |

Verified `SBX` signature:

```python
SBX(prob_var=0.5, eta=15, prob_exch=1.0, prob_bin=0.5,
    n_offsprings=2, **kwargs)
```

Custom crossover contract:

```python
class MyCrossover(Crossover):
    def __init__(self):
        super().__init__(n_parents=2, n_offsprings=2)

    def _do(self, problem, X, **kwargs):
        # X shape: (n_parents, n_matings, n_var)
        Y = ...  # shape: (n_offsprings, n_matings, n_var)
        return Y
```

For object variables, allocate arrays with `dtype=object` when values are strings,
lists, dicts, routes, or other Python objects.

## Mutation operators

| Import | Use |
| --- | --- |
| `from pymoo.operators.mutation.pm import PM` | Polynomial mutation for real/integer-with-repair variables. |
| `from pymoo.operators.mutation.bitflip import BFM` | Binary bitflip mutation. |
| `from pymoo.operators.mutation.inversion import InversionMutation` | Permutation inversion. |
| `from pymoo.operators.mutation.gauss import GaussianMutation` | Gaussian perturbation. |
| `from pymoo.core.mutation import Mutation` | Base class for custom mutation. |

Verified `PM` signature:

```python
PM(prob=0.9, eta=20, at_least_once=False, **kwargs)
```

Custom mutation contract:

```python
class MyMutation(Mutation):
    def _do(self, problem, X, **kwargs):
        # X shape: (n_individuals, n_var)
        return X_mutated
```

## Repair operators

| Import | Use |
| --- | --- |
| `from pymoo.operators.repair.rounding import RoundingRepair` | Round floats to integer-compatible values after variation. |
| `from pymoo.operators.repair.bounds_repair import repair_random_init, repair_clamp` | Bounds-oriented repair helpers. |
| `from pymoo.operators.repair.to_bound import ToBoundOutOfBoundsRepair` | Move out-of-bound values to nearest bound. |
| `from pymoo.core.repair import Repair` | Base class for custom repair. |

Verified `RoundingRepair()` constructor takes `**kwargs` and is usually passed to
operators such as `SBX(vtype=float, repair=RoundingRepair())` or
`PM(vtype=float, repair=RoundingRepair())`.

## Duplicate elimination

Use duplicate elimination when equivalent encodings waste evaluations:

```python
from pymoo.core.duplicate import ElementwiseDuplicateElimination

class MyDuplicateElimination(ElementwiseDuplicateElimination):
    def is_equal(self, a, b):
        return a.X[0] == b.X[0]
```

For mixed-variable dictionaries, `MixedVariableDuplicateElimination` compares
keys and values. For floating arrays, use built-in duplicate elimination or
algorithm-level `eliminate_duplicates=True` when available.

## Hyperparameter helpers

```python
from pymoo.core.parameters import get_params, flatten, hierarchical, set_params
from pymoo.algorithms.hyperparameters import HyperparameterProblem
```

Use these helpers to inspect/tune algorithm/operator parameters. Optional
`optuna`-backed algorithms require optional dependencies and should not be
assumed in a base install.
