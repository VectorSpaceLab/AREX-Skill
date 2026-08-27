# Workflows

## Build a route objective

1. Create a small coordinate array.
2. Build a square distance matrix with Euclidean distances.
3. Define a route-cost function that sums the edges of a permutation.
4. Run a TSP optimizer and validate that the result is a true permutation.

```python
import numpy as np
from scipy.spatial import distance

coords = np.array([
    [0.0, 0.0],
    [1.0, 0.0],
    [1.0, 1.0],
    [0.0, 1.0],
])

dm = distance.cdist(coords, coords)

def route_cost(route):
    route = np.asarray(route, dtype=int)
    return float(sum(dm[route[i % len(route)], route[(i + 1) % len(route)]] for i in range(len(route))))
```

## Choose the route optimizer

| Problem shape | Pick | Why |
| --- | --- | --- |
| Permutation GA route search | `GA_TSP` | Simple route baseline and the most direct permutation workflow. |
| Permutation annealing | `SA_TSP` | Single-route simulated annealing on permutations. |
| Pheromone-based routing | `ACA_TSP` | Useful when you want ant-colony behavior and an explicit distance matrix. |
| Immune-style routing | `IA_TSP` | Package-provided route variant for immune-algorithm users. |
| Particle-swarm route search | avoid `PSO_TSP` in this release | Known construction failure in the installed package version. |

## Tiny GA_TSP workflow

```python
from sko.GA import GA_TSP

route = GA_TSP(func=route_cost, n_dim=len(coords), size_pop=8, max_iter=5, prob_mut=0.1)
best_route, best_distance = route.run()
```

## Fixed start/end points

The README demonstrates a safe pattern for fixed endpoints: keep the endpoints outside the optimizer input, optimize only the intermediate cities, and prepend/append the fixed endpoints inside the route-cost function.

Use this when a real route has a fixed depot or terminal and the optimizer should not permute those positions.

## Validation checks

- Confirm the route length equals `n_dim`.
- Confirm each city index appears exactly once.
- Confirm the route-cost result is finite.
- Confirm the distance matrix is square and matches the coordinate count.

## When to stop and switch

- If the task is not a permutation route, switch to `continuous-optimizers`.
- If the task needs custom genetic operators or integer precision, switch to `genetic-algorithms`.
- If the user only wants objective run modes or benchmark functions, switch to `objective-functions-and-speedups`.
