# API reference

## Class chooser

| Class | Use it when | Core representation |
| --- | --- | --- |
| `GA` | You want Gray-coded search for bounded continuous, integer, or mixed-precision variables. | Bit chromosome decoded to real values. |
| `EGA` | You want the same GA behavior, but with explicit elitist carry-over. | Same as `GA`, plus preserved elites. |
| `RCGA` | Your variables are naturally continuous and you want real-coded search. | Real-valued chromosome in `[0, 1]` mapped to bounds. |
| `GA_TSP` | You need permutation-based TSP handoff behavior. | Route chromosome. Full route recipes belong to `routing-and-combinatorial`. |

## Constructor signatures

```python
GA(func, n_dim, size_pop=50, max_iter=200, prob_mut=0.001,
   lb=-1, ub=1, constraint_eq=(), constraint_ueq=(),
   precision=1e-07, early_stop=None, n_processes=0)

EGA(func, n_dim, size_pop=50, max_iter=200, prob_mut=0.001,
    n_elitist=0, lb=-1, ub=1, constraint_eq=(), constraint_ueq=(),
    precision=1e-07, early_stop=None)

RCGA(func, n_dim, size_pop=50, max_iter=200, prob_mut=0.001,
     prob_cros=0.9, lb=-1, ub=1, n_processes=0)
```

## Parameter meanings

### Shared GA-family parameters

| Parameter | Meaning |
| --- | --- |
| `func` | Objective callable evaluated on one candidate `x`; smaller values are better. Keep it scalar-valued per candidate. |
| `n_dim` | Number of decision variables. |
| `size_pop` | Population size. For `GA`, `EGA`, and `GA_TSP`, this must be an even integer. |
| `max_iter` | Maximum generations for one `run(max_iter)` call. Repeated calls continue from the current population state. |
| `prob_mut` | Mutation probability. |
| `lb`, `ub` | Per-dimension lower and upper bounds. Scalars broadcast; sequences must match `n_dim` for clear intent. |
| `constraint_eq` | Iterable of equality constraints `c(x) == 0`. Violations are penalized. |
| `constraint_ueq` | Iterable of inequality constraints `c(x) <= 0`. Positive violations are penalized. |
| `early_stop` | Stop after this many generations without a new best-so-far improvement. |
| `n_processes` | Worker-count hint forwarded to the wrapped objective. Use `0` for the default all-CPU behavior when a non-common evaluation mode is enabled; otherwise it is ignored. |

### GA-specific parameters

| Parameter | Meaning |
| --- | --- |
| `precision` | Per-dimension step size. Scalars or sequences are accepted. Integer precisions enable discrete/mixed-precision search. The implementation may extend the upper bound internally so the Gray-code lattice fits the requested step grid. |

### EGA-specific parameters

| Parameter | Meaning |
| --- | --- |
| `n_elitist` | Number of elite individuals copied forward untouched each generation. Keep it smaller than `size_pop`. Use `0` when you want GA-like behavior without explicit elitism. |

### RCGA-specific parameters

| Parameter | Meaning |
| --- | --- |
| `prob_cros` | Crossover probability for the real-coded GA. |

## Result and history fields

| Field | Meaning |
| --- | --- |
| `best_x` | Best candidate seen across all completed generations. |
| `best_y` | Objective value at `best_x`. In this release it may be a length-1 NumPy array; convert it to a scalar when you need comparisons. |
| `generation_best_X` | Best candidate from each generation. |
| `generation_best_Y` | Best objective value from each generation. |
| `all_history_Y` | Raw objective values for the whole population in each generation. |
| `all_history_FitV` | Fitness values after ranking in each generation. |

## Default operators

### `GA`
- `ranking = ranking.ranking`
- `selection = selection.selection_tournament_faster`
- `crossover = crossover.crossover_2point_bit`
- `mutation = mutation.mutation`

### `EGA`
- Same default operator family as `GA`, plus elitist preservation in `run()`.

### `RCGA`
- `ranking = ranking.ranking`
- `selection = selection.selection_tournament_faster`
- `crossover = simulated binary crossover (SBX)`
- `mutation = polynomial mutation`

## Notes

- `GA` and `EGA` use Gray-code decoding under the hood.
- `RCGA` is the right choice when you do not want bit encoding.
- `GA_TSP` is a route-optimization handoff only in this sub-skill; use the routing sub-skill for full workflow recipes.
