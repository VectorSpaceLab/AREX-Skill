# Custom operators

`SkoBase.register()` attaches a new method to a single algorithm instance. Use it when you want to replace one GA-family operator without subclassing.

## How registration works

- The first argument is the target method name, such as `selection`, `ranking`, `crossover`, or `mutation`.
- The replacement function receives the algorithm instance as its first argument.
- Any extra positional or keyword arguments passed to `register()` are bound into the method call.
- The operator should update `self.Chrom` or `self.FitV` as appropriate and return the updated value.

Example pattern:

```python
ga.register(operator_name="selection", operator=my_selection, tourn_size=3)
```

## Built-in operator families

### Ranking
- `ranking.ranking` — default minimization ranking (`FitV = -Y`).
- `ranking.ranking_linear` — linear rank variant.

### Selection
- `selection.selection_tournament`
- `selection.selection_tournament_faster`
- `selection.selection_roulette_1`
- `selection.selection_roulette_2`

### Crossover
- `crossover.crossover_1point`
- `crossover.crossover_2point`
- `crossover.crossover_2point_bit`
- `crossover.crossover_pmx` for permutation routes
- `crossover.crossover_2point_prob`

### Mutation
- `mutation.mutation`
- `mutation.mutation_reverse`
- `mutation.mutation_swap`
- `mutation.mutation_TSP_1`

## Safe custom selection example

This keeps the top half of the population and duplicates it back to the required even population size. It is deterministic, shape-safe, and compatible with `GA`/`EGA`.

```python
import numpy as np


def selection_top_half(self):
    order = np.argsort(-self.FitV)
    elite = order[: self.size_pop // 2]
    self.Chrom = np.repeat(self.Chrom[elite], 2, axis=0)
    return self.Chrom
```

You can register it together with built-in ranking, crossover, and mutation helpers:

```python
from sko.operators import ranking, crossover, mutation

ga.register(operator_name="selection", operator=selection_top_half) \
    .register(operator_name="ranking", operator=ranking.ranking) \
    .register(operator_name="crossover", operator=crossover.crossover_2point_bit) \
    .register(operator_name="mutation", operator=mutation.mutation)
```

## When to prefer built-ins

Use the bundled operators unless you have a clear reason to change them. The defaults are already compatible with the GA-family population layout and are the safest fallback when you are debugging a new objective.
