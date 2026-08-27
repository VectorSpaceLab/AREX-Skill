# PyGAD benchmark workflows

These workflows show how to plug the built-in benchmark problem classes into
`pygad.GA` and how to score the final fronts with the quality indicators.
They intentionally keep the runs small and deterministic so they can be used as
smoke checks or starting points for real experiments.

## 1. Classic single-objective smoke run

Use this pattern for Sphere, Rastrigin, Rosenbrock, Griewank, Schwefel, Ackley,
and Himmelblau.

```python
import numpy as np
import pygad
from pygad.benchmarks.classic import Sphere

problem = Sphere(num_genes=4)

initial_population = np.array([
    [0.0, 0.0, 0.0, 0.0],
    [1.0, -1.0, 0.5, -0.5],
    [2.0, 2.0, -2.0, -2.0],
    [-1.0, 1.0, -1.0, 1.0],
])

ga = pygad.GA(
    num_generations=3,
    num_parents_mating=2,
    fitness_func=problem,
    initial_population=initial_population,
    keep_elitism=1,
    crossover_type=None,
    mutation_type=None,
    random_seed=7,
    suppress_warnings=True,
)

ga.run()
solution, fitness, index = ga.best_solution(ga.last_generation_fitness)
```

Validation signals:

- `ga.run_completed` should be `True` after a clean run.
- The best fitness should be near the known optimum for the benchmark.
- `solution.shape[0]` should equal `problem.num_genes`.

## 2. ZDT family with NSGA-II and indicators

Use this pattern for ZDT1, ZDT2, ZDT3, ZDT4, and ZDT6.

```python
import numpy as np
import pygad
from pygad.benchmarks.zdt import ZDT1
from pygad.utils.quality_indicators import (
    generational_distance,
    hypervolume,
    inverted_generational_distance,
    spacing,
)

problem = ZDT1(num_genes=10)

ga = pygad.GA(
    num_generations=5,
    num_parents_mating=4,
    fitness_func=problem,
    initial_population=np.array([
        [0.0] + [0.0] * 9,
        [0.25] + [0.0] * 9,
        [0.50] + [0.0] * 9,
        [0.75] + [0.0] * 9,
    ]),
    parent_selection_type="nsga2",
    crossover_type="sbx",
    sbx_crossover_eta=30,
    mutation_type="polynomial",
    polynomial_mutation_eta=20,
    keep_elitism=1,
    random_seed=9,
    suppress_warnings=True,
)

ga.run()
front = np.asarray(ga.last_generation_fitness)
true_front = problem.pareto_front(num_points=100)
igd = inverted_generational_distance(front, true_front)
gd = generational_distance(front, true_front)
hv = hypervolume(front, front.min(axis=0) - 0.1)
spread = spacing(front)
```

Workflow notes:

- Use `problem.pareto_front()` when available as the reference front for IGD or
  GD.
- `hypervolume` needs a reference point that is smaller than every solution on
  every axis in PyGAD maximization format.
- `spacing` is useful when you want evenness, not just convergence.
- `ZDT3` has no bundled `pareto_front()` helper in this release, so build a
  reference front yourself if you need one.

## 3. DTLZ family with NSGA-III

Use this pattern for DTLZ1, DTLZ2, DTLZ3, and DTLZ4 when you want many
objectives or reference-point diversity.

```python
import math
import numpy as np
import pygad
from pygad.benchmarks.dtlz import DTLZ2

problem = DTLZ2(num_objectives=3, num_distance_vars=4)
nsga3_num_divisions = 2
reference_point_count = math.comb(problem.num_objectives + nsga3_num_divisions - 1,
                                  nsga3_num_divisions)

initial_population = np.array([
    [0.25, 0.75, 0.50, 0.50, 0.50, 0.50],
    [0.10, 0.90, 0.10, 0.20, 0.30, 0.40],
    [0.90, 0.10, 0.20, 0.30, 0.40, 0.50],
    [0.60, 0.40, 0.70, 0.60, 0.50, 0.40],
    [0.20, 0.80, 0.40, 0.30, 0.20, 0.10],
    [0.80, 0.20, 0.30, 0.40, 0.50, 0.60],
])

ga = pygad.GA(
    num_generations=1,
    num_parents_mating=3,
    fitness_func=problem,
    initial_population=initial_population,
    parent_selection_type="nsga3",
    nsga3_num_divisions=nsga3_num_divisions,
    keep_elitism=1,
    crossover_type=None,
    mutation_type=None,
    random_seed=11,
    suppress_warnings=True,
)

ga.run()
```

Validation signals:

- `problem.num_genes` must equal `problem.num_objectives + num_distance_vars - 1`.
- `ga.nsga3_reference_points.shape[0]` should match the reference-point count
  formula.
- DTLZ1 Pareto points satisfy `sum(f_i) = 0.5`.
- DTLZ2/DTLZ3 Pareto points satisfy `sum(f_i**2) = 1`.
- DTLZ4 has the same front as DTLZ2 but a much stronger search-space bias.

## 4. Knapsack workflow

Use this pattern for 0/1 knapsack selection.

```python
import numpy as np
import pygad
from pygad.benchmarks.knapsack import Knapsack

problem = Knapsack(
    weights=[2, 3, 4, 5],
    values=[3, 4, 5, 6],
    capacity=5,
)

initial_population = np.array([
    [1, 1, 0, 0],
    [1, 0, 0, 0],
    [0, 1, 0, 0],
    [0, 0, 1, 0],
])

ga = pygad.GA(
    num_generations=2,
    num_parents_mating=2,
    fitness_func=problem,
    initial_population=initial_population,
    gene_space=problem.gene_space,
    gene_type=problem.gene_type,
    keep_elitism=1,
    crossover_type=None,
    mutation_type=None,
    random_seed=13,
    suppress_warnings=True,
)

ga.run()
```

Workflow notes:

- The genome is binary, so use `gene_space=[0, 1]` and `gene_type=int`.
- Feasible solutions return the total selected value.
- Over-capacity solutions return a negative penalty equal to the overweight
  amount.
- If you want a quick correctness check, evaluate a known feasible subset and a
  known overweight subset directly through the benchmark callable.

## 5. TSP workflow

Use this pattern for permutation-based traveling salesman problems.

```python
import numpy as np
import pygad
from pygad.benchmarks.tsp import TSP

problem = TSP(coordinates=[
    [0.0, 0.0],
    [1.0, 0.0],
    [1.0, 1.0],
    [0.0, 1.0],
])

initial_population = np.array([
    [0, 1, 2, 3],
    [0, 2, 1, 3],
    [0, 1, 3, 2],
    [0, 3, 2, 1],
])

ga = pygad.GA(
    num_generations=2,
    num_parents_mating=2,
    fitness_func=problem,
    initial_population=initial_population,
    gene_space=problem.gene_space,
    gene_type=problem.gene_type,
    allow_duplicate_genes=problem.allow_duplicate_genes,
    keep_elitism=1,
    crossover_type=None,
    mutation_type=None,
    random_seed=17,
    suppress_warnings=True,
)

ga.run()
solution, fitness, index = ga.best_solution(ga.last_generation_fitness)
tour_length = problem.tour_length(solution)
```

Workflow notes:

- Use either `coordinates` or `distance_matrix`, not both.
- `allow_duplicate_genes=False` is required to preserve permutations.
- Fitness is the negative closed-tour length, so the real tour length is
  `-fitness`.
- Invalid tours return a large negative penalty, which is usually a sign that
  the chromosome or gene-space setup is wrong.

## 6. Indicator-only workflow

Use this when you already have a front and only need to score it.

```python
import numpy as np
from pygad.utils.quality_indicators import (
    generational_distance,
    hypervolume,
    inverted_generational_distance,
    spacing,
)

approximation_front = np.array([
    [-1.0, -8.0],
    [-3.0, -5.0],
    [-6.0, -2.0],
])
reference_front = np.array([
    [-1.0, -8.0],
    [-4.0, -4.0],
    [-7.0, -1.0],
])

igd = inverted_generational_distance(approximation_front, reference_front)
gd = generational_distance(approximation_front, reference_front)
hv = hypervolume(approximation_front, approximation_front.min(axis=0) - 0.1)
spread = spacing(approximation_front)
```

Rules:

- Always pass 2D arrays for front-based indicators.
- Use a 1D reference point for hypervolume.
- Negate minimization fronts once before scoring them.
- `spacing` returns `0.0` when fewer than two solutions are supplied.

## 7. Run the bundled smoke script

From this sub-skill directory:

```bash
python scripts/benchmark_smoke.py
```

The script prints a compact JSON summary, exercises the benchmark callables,
and uses only temporary files for save/load round-trips.
