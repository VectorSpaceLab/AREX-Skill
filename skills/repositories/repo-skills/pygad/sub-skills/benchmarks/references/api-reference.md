# PyGAD benchmark API reference

This reference covers the public benchmark problem classes and quality
indicators used by the `benchmarks` sub-skill.

## Import scope

```python
import numpy
import pygad
from pygad.benchmarks import classic, zdt, dtlz, knapsack, tsp
from pygad.utils import quality_indicators
```

## Core conventions

- All benchmark callables use the PyGAD fitness signature
  `(ga_instance, solution, solution_idx)`.
- PyGAD maximizes fitness. The benchmark problems already return values in
  maximization form, so minimization objectives are negated internally.
- `ga.last_generation_fitness` is the primary array to feed into quality
  indicators.
- Multi-objective benchmark callables return a Python `list` of floats.
- Single-objective benchmark callables return a scalar `float`.

## Package layout

`pygad.benchmarks` exposes the following public modules:

- `classic`
- `zdt`
- `dtlz`
- `knapsack`
- `tsp`

## Classic single-objective benchmarks

All classic classes expose `num_objectives = 1`, a `num_genes` attribute, and a
class-level `bounds` tuple. `Himmelblau` is fixed to two genes.

| Class | Constructor | `bounds` | Notes |
| --- | --- | --- | --- |
| `Sphere` | `Sphere(num_genes=10)` | `(-5.12, 5.12)` | `-sum(x**2)`; optimum at the origin. |
| `Rastrigin` | `Rastrigin(num_genes=10)` | `(-5.12, 5.12)` | Highly multimodal; optimum at the origin. |
| `Rosenbrock` | `Rosenbrock(num_genes=10)` | `(-5.0, 10.0)` | Banana valley; optimum at all ones. |
| `Griewank` | `Griewank(num_genes=10)` | `(-600.0, 600.0)` | Large search region with many local minima. |
| `Schwefel` | `Schwefel(num_genes=10)` | `(-500.0, 500.0)` | Optimum near `420.9687` in every gene. |
| `Ackley` | `Ackley(num_genes=10)` | `(-32.768, 32.768)` | Flat outer region, sharp basin at the origin. |
| `Himmelblau` | `Himmelblau()` | `(-5.0, 5.0)` | Fixed `num_genes=2`; four equal minima. |

### Classic class contract

```python
problem = classic.Sphere(num_genes=5)
fitness = problem(ga_instance, solution, solution_idx)
```

- `solution` may be any array-like sequence of numeric values.
- The callable converts the input to `numpy.asarray(..., dtype=float)`.
- Return value: scalar `float`.
- Validation signal: `problem.num_genes` should match the GA chromosome length.

## ZDT multi-objective benchmarks

ZDT classes expose `num_objectives = 2` and `bounds = (0.0, 1.0)` unless
noted otherwise.

| Class | Constructor | `num_genes` default | Front helper | Notes |
| --- | --- | --- | --- | --- |
| `ZDT1` | `ZDT1(num_genes=30)` | `30` | `pareto_front(num_points=100)` | Convex front: `f2 = 1 - sqrt(f1)`. |
| `ZDT2` | `ZDT2(num_genes=30)` | `30` | `pareto_front(num_points=100)` | Non-convex front: `f2 = 1 - f1**2`. |
| `ZDT3` | `ZDT3(num_genes=30)` | `30` | none | Five disconnected front pieces. |
| `ZDT4` | `ZDT4(num_genes=10)` | `10` | `pareto_front(num_points=100)` | Same convex front as ZDT1; search space uses wider bounds. |
| `ZDT6` | `ZDT6(num_genes=10)` | `10` | `pareto_front(num_points=100)` | Non-uniform front; sampled over `f1 in [0.281, 1.0]`. |

### ZDT class contract

```python
problem = zdt.ZDT1(num_genes=10)
values = problem(ga_instance, solution, solution_idx)
reference_front = problem.pareto_front(num_points=100)
```

- `__call__` returns `[-f1, -f2]` as a Python `list` of two floats.
- Solutions are clipped into the supported variable range before evaluation.
- `pareto_front(num_points=100)` returns an array with shape `(num_points, 2)`
  in PyGAD maximization format.
- `ZDT3` does not ship a `pareto_front()` helper in this release; build a
  reference set analytically if you need one.
- `ZDT4` clips the first gene to `[0, 1]` and the remaining genes to `[-5, 5]`
  before computing fitness.

## DTLZ many-objective benchmarks

DTLZ classes expose `bounds = (0.0, 1.0)` and require at least two objectives.
The number of decision variables is always:

```text
num_genes = num_objectives + num_distance_vars - 1
```

| Class | Constructor | Default args | Front shape | Notes |
| --- | --- | --- | --- | --- |
| `DTLZ1` | `DTLZ1(num_objectives=3, num_distance_vars=5)` | `k=5` | Hyperplane | Pareto front satisfies `sum(f_i) = 0.5`. |
| `DTLZ2` | `DTLZ2(num_objectives=3, num_distance_vars=10)` | `k=10` | Unit sphere | Pareto front is the first orthant of the unit sphere. |
| `DTLZ3` | `DTLZ3(num_objectives=3, num_distance_vars=10)` | `k=10` | Unit sphere | Same front as DTLZ2, but with a harder multimodal `g` function. |
| `DTLZ4` | `DTLZ4(num_objectives=3, num_distance_vars=10, alpha=100.0)` | `k=10`, `alpha=100.0` | Unit sphere | Same front as DTLZ2, with a strong bias toward one corner. |

### DTLZ class contract

```python
problem = dtlz.DTLZ2(num_objectives=3, num_distance_vars=10)
values = problem(ga_instance, solution, solution_idx)
```

- `solution` is clipped into `[0, 1]` before evaluation.
- Return value: Python `list` of length `num_objectives`.
- `num_objectives` must be at least 2; otherwise the constructor raises `ValueError`.
- There is no bundled `pareto_front()` method for DTLZ classes.
- DTLZ1/3 use a multimodal distance term; DTLZ2/4 use a simpler quadratic one.

## Knapsack benchmark

```python
problem = knapsack.Knapsack(weights, values, capacity)
```

### Signature and attributes

- Constructor: `Knapsack(weights, values, capacity)`.
- `num_objectives = 1`.
- `gene_space = [0, 1]`.
- `gene_type = int`.
- `num_genes = len(weights)`.

### Validation rules

- `weights` must be 1D.
- `values` must be 1D.
- `weights` and `values` must have the same length.
- `weights` must be non-negative.
- `values` must be non-negative.
- `capacity` must be positive.

### Fitness contract

- A solution is interpreted as a binary selection vector.
- Feasible solutions return the total value.
- Over-capacity solutions return a negative penalty equal to the overweight
  amount: `-(total_weight - capacity)`.

### Call signature

```python
fitness = problem(ga_instance, solution, solution_idx)
```

Return value: scalar `float`.

## TSP benchmark

```python
problem = tsp.TSP(coordinates=..., distance_matrix=...)
```

### Signature and attributes

- Constructor: `TSP(coordinates=None, distance_matrix=None)`.
- `num_objectives = 1`.
- `gene_type = int`.
- `allow_duplicate_genes = False`.
- `gene_space = list(range(num_cities))` after construction.
- `num_genes = num_cities`.

### Validation rules

- Pass exactly one of `coordinates` or `distance_matrix`.
- `coordinates`, if used, must be a 2D array with at least 2 rows.
- `distance_matrix`, if used, must be square, have at least 2 rows, and contain
  no negative entries.

### Fitness contract

- A solution is interpreted as a city permutation.
- Fitness is the negative closed-tour length.
- Invalid permutations return a large negative penalty.
- Too-short solutions also return a penalty.

### Helper method

```python
length = problem.tour_length(tour)
```

- Returns the closed-tour length as a scalar `float`.
- The last leg goes from the last city back to the first.

## Quality indicators

All quality-indicator functions expect fitness/front arrays in PyGAD's
maximization format.

| Function | Signature | Return | Notes |
| --- | --- | --- | --- |
| `hypervolume` | `hypervolume(fitness, reference_point)` | `float` | Reference point must be worse than every solution on every axis. Dominated rows are dropped internally. |
| `inverted_generational_distance` | `inverted_generational_distance(fitness, reference_front)` | `float` | Mean distance from each reference point to its nearest approximation point. |
| `generational_distance` | `generational_distance(fitness, reference_front)` | `float` | Mean distance from each approximation point to its nearest reference point. |
| `spacing` | `spacing(fitness)` | `float` | Standard deviation of nearest-neighbor distances. Returns `0.0` for one or zero solutions. |

### Quality-indicator shapes

- `fitness`: 2D array with shape `(num_solutions, num_objectives)`.
- `reference_point`: 1D array with length `num_objectives`.
- `reference_front`: 2D array with the same number of objective columns as
  `fitness`.

### Practical sign rule

If you have a minimization front from outside PyGAD, negate it once before
passing it to these helpers. Do not negate it twice.

## Common validation signals to watch

- `ZDT` and `DTLZ` outputs must be vector-valued.
- `Knapsack` and `TSP` outputs must be scalars.
- Hypervolume input must be 2D and use a strictly worse reference point.
- `TSP` permutation validity depends on `gene_space`, `gene_type`, and
  `allow_duplicate_genes=False`.
