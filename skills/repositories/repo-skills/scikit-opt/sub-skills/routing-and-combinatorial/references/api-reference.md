# API reference

## Class chooser

| Class | Use it when | Core representation |
| --- | --- | --- |
| `GA_TSP` | You want the package's permutation GA for TSP-style routes. | Permutation chromosome. |
| `SA_TSP` | You want permutation annealing for routes. | Single route permutation. |
| `ACA_TSP` | You want ant-colony routing. | Ant path table plus pheromone matrix. |
| `IA_TSP` | You want immune-algorithm routing behavior. | TSP-oriented GA/TSP variant. |
| `PSO_TSP` | Only as a version-specific caveat in this release. | The installed package raises a construction `TypeError`. |

## Constructor signatures

```python
GA_TSP(func, n_dim, size_pop=50, max_iter=200, prob_mut=0.001)
SA_TSP(func, x0, T_max=100, T_min=1e-07, L=300, max_stay_counter=150, **kwargs)
ACA_TSP(func, n_dim, size_pop=10, max_iter=20, distance_matrix=None, alpha=1, beta=2, rho=0.1)
IA_TSP(func, n_dim, size_pop=50, max_iter=200, prob_mut=0.001, T=0.7, alpha=0.95)
```

## Route helper

`sko.demo_func.function_for_TSP(num_points, seed=None)` is the built-in helper for synthetic route fixtures. It returns a tuple containing the number of points, coordinates, a distance matrix, and a route-cost callable. Use it when you want a small repeatable route dataset without external files.

## Parameter notes

### `GA_TSP`
- `size_pop` and `max_iter` are the main control knobs.
- `prob_mut` controls permutation mutation rate.
- The chromosome is a permutation, so the objective must interpret the vector as an order of visiting cities.

### `SA_TSP`
- `x0` is an initial permutation.
- Use it when you want annealing over route permutations.

### `ACA_TSP`
- `distance_matrix` is required for normal operation.
- `alpha`, `beta`, and `rho` control pheromone influence and evaporation.

### `IA_TSP`
- `T` and `alpha` control antibody concentration and diversity balance.

## Result and history fields

| Field | Meaning |
| --- | --- |
| `best_x` / `best_y` | Best route and route cost seen so far. |
| `generation_best_X` / `generation_best_Y` | Best route/cost per generation for route algorithms that track history. |
| `Tau` | Pheromone matrix in `ACA_TSP`. |
| `Table` | Ant route table in `ACA_TSP`. |

## Important note

In the verified `0.6.6` release used for this skill, `PSO_TSP` construction raised `TypeError: func_transformer() missing 1 required positional argument: 'n_processes'`. Do not present it as a working route solver in this generated skill.
