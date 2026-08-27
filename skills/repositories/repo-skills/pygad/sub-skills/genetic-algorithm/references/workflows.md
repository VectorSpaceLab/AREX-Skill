# PyGAD GA workflows

These workflows distill practical `pygad.GA` usage patterns. Copy the relevant snippets into a user project and adapt names, bounds, objectives, and stopping criteria.

## 1. Minimal single-objective run

Use this when the user has one maximization objective or a minimization loss that can be negated.

```python
import numpy
import pygad

inputs = numpy.array([4.0, -2.0, 3.5, 5.0])
target = 31.0

def fitness_func(ga_instance, solution, solution_idx):
    prediction = numpy.dot(solution, inputs)
    error = abs(prediction - target)
    return 1.0 / (error + 1e-6)  # PyGAD maximizes.

ga = pygad.GA(
    num_generations=80,
    num_parents_mating=6,
    sol_per_pop=16,
    num_genes=len(inputs),
    fitness_func=fitness_func,
    parent_selection_type="sss",
    crossover_type="single_point",
    mutation_type="random",
    mutation_probability=0.2,
    random_seed=13,
)

ga.run()
solution, fitness, index = ga.best_solution(ga.last_generation_fitness)
print(solution, fitness, index)
```

Validation signals:

- `ga.run_completed` is `True` after a clean run.
- `ga.last_generation_fitness` has length `sol_per_pop`.
- `ga.best_solution(...)` returns a 1D NumPy array with `num_genes` entries.

## 2. Use bounded, typed, and constrained genes

Choose `gene_space` instead of only `init_range_low`/`init_range_high` when the valid values are known.

```python
import numpy
import pygad

# Gene 0 is a small integer, gene 1 is continuous-ish, gene 2 is chosen from a grid.
gene_space = [range(0, 6), {"low": -1.0, "high": 1.0, "step": 0.1}, [10, 20, 30]]
gene_type = [int, [float, 2], int]

def gene1_above_gene0(solution, values):
    # Constraints are applied in gene-index order. Earlier genes are safer dependencies.
    return [value for value in values if value > -solution[0]]

def fitness_func(ga_instance, solution, solution_idx):
    return float(solution[0] - abs(solution[1]) + solution[2] / 10.0)

ga = pygad.GA(
    num_generations=25,
    num_parents_mating=4,
    sol_per_pop=10,
    num_genes=3,
    fitness_func=fitness_func,
    gene_space=gene_space,
    gene_type=gene_type,
    gene_constraint=[None, gene1_above_gene0, None],
    sample_size=200,
    allow_duplicate_genes=True,
    random_seed=5,
)

ga.run()
```

Guidelines:

- A nested `gene_space` must have exactly `num_genes` entries.
- A dict `gene_space` samples `[low, high)`; `step` makes a discrete grid.
- Constraint callables receive `(solution, candidate_values)` and must return a filtered list/array. Return an empty list when no value is valid.
- Increase `sample_size` when constraints or uniqueness fail intermittently.

## 3. Tune adaptive mutation

Adaptive mutation mutates low-quality solutions more than high-quality solutions. Set `mutation_type="adaptive"` and give exactly two rates.

```python
ga = pygad.GA(
    num_generations=120,
    num_parents_mating=8,
    sol_per_pop=20,
    num_genes=6,
    fitness_func=fitness_func,
    mutation_type="adaptive",
    mutation_probability=[0.35, 0.08],  # low-quality, high-quality
    random_seed=21,
)
```

Alternative controls:

```python
mutation_num_genes=[4, 1]
mutation_percent_genes=[40, 10]
```

If PyGAD warns that the first adaptive value is lower than the second, swap them unless the user intentionally wants to disrupt high-quality solutions more.

## 4. Real-coded operators for continuous genomes

For continuous search spaces, pair SBX crossover with polynomial mutation.

```python
ga = pygad.GA(
    num_generations=100,
    num_parents_mating=10,
    sol_per_pop=30,
    num_genes=5,
    fitness_func=fitness_func,
    gene_space={"low": -5.0, "high": 5.0},
    gene_type=[float, 4],
    crossover_type="sbx",
    sbx_crossover_eta=20,
    mutation_type="polynomial",
    polynomial_mutation_eta=20,
    mutation_probability=0.15,
    random_seed=17,
)
```

Higher `sbx_crossover_eta` keeps children closer to parents. Higher `polynomial_mutation_eta` makes smaller mutation steps.

## 5. Multi-objective NSGA-II

Return one objective vector per solution and select a multi-objective parent selector.

```python
import numpy
import pygad

def fitness_func(ga_instance, solution, solution_idx):
    x, y = solution
    objective_a = -((x + 2.0) ** 2 + y ** 2)
    objective_b = -((x - 2.0) ** 2 + y ** 2)
    return [objective_a, objective_b]

ga = pygad.GA(
    num_generations=60,
    num_parents_mating=8,
    sol_per_pop=24,
    num_genes=2,
    fitness_func=fitness_func,
    gene_space=[{"low": -4, "high": 4}, {"low": -2, "high": 2}],
    parent_selection_type="nsga2",
    crossover_type="sbx",
    mutation_type="polynomial",
    mutation_probability=0.2,
    random_seed=9,
)

ga.run()
fronts = ga.pareto_fronts
solution, objectives, index = ga.best_solution(ga.last_generation_fitness)
```

Notes:

- `last_generation_fitness` is a 2D array-like object with shape `(population, objectives)`.
- `best_solution()` uses NSGA-II ordering for multi-objective fitness. For a full Pareto analysis, inspect `ga.pareto_fronts` and the whole `last_generation_fitness` matrix.

## 6. Multi-objective NSGA-III

Use NSGA-III when there are many objectives or when reference-point diversity matters.

```python
import math

num_objectives = 4
p = 3
reference_points = math.comb(num_objectives + p - 1, p)
sol_per_pop = max(40, reference_points)

ga = pygad.GA(
    num_generations=80,
    num_parents_mating=12,
    sol_per_pop=sol_per_pop,
    num_genes=10,
    fitness_func=multi_objective_fitness,
    parent_selection_type="nsga3",
    nsga3_num_divisions=p,
    random_seed=2,
)
```

Guidelines:

- `nsga3_num_divisions` is required and must be positive for `"nsga3"` and `"tournament_nsga3"`.
- The reference-point count is `C(M + p - 1, p)` for `M` objectives and `p` divisions.
- If `sol_per_pop` is too small, PyGAD grows it and re-evaluates fitness. Prefer computing a suitable population upfront to avoid surprises.

## 7. Custom operators

Use custom operators only when built-ins cannot meet constraints or domain-specific behavior.

```python
import numpy


def parent_selection_func(fitness, num_parents, ga_instance):
    order = numpy.argsort(fitness)[::-1]
    indices = order[:num_parents]
    return ga_instance.population[indices, :].copy(), indices.astype(int)


def crossover_func(parents, offspring_size, ga_instance):
    offspring = numpy.empty(offspring_size, dtype=parents.dtype)
    for row in range(offspring_size[0]):
        p1 = parents[row % parents.shape[0]].copy()
        p2 = parents[(row + 1) % parents.shape[0]]
        split = offspring_size[1] // 2
        p1[split:] = p2[split:]
        offspring[row] = p1
    return offspring


def mutation_func(offspring, ga_instance):
    mutated = offspring.copy()
    mutated[:, 0] = mutated[:, 0] + 0.1
    return mutated


ga = pygad.GA(
    num_generations=20,
    num_parents_mating=4,
    sol_per_pop=10,
    num_genes=3,
    fitness_func=fitness_func,
    parent_selection_type=parent_selection_func,
    crossover_type=crossover_func,
    mutation_type=mutation_func,
)
```

Validation requirements:

- Parent selection returns two NumPy arrays: parents shape `(num_parents, num_genes)` and 1D indices length `num_parents`.
- Crossover returns a NumPy array with `offspring_size`.
- Mutation returns a NumPy array with the same offspring shape.
- Custom mutation should preserve `gene_type`, `gene_space`, constraints, and duplicate rules if those matter to the problem.

## 8. Parallel and batch fitness

Use batch fitness to reduce Python call overhead; use parallelism only when each fitness call is expensive.

```python
def batch_fitness(ga_instance, solutions, solution_indices):
    return [score(solution) for solution in solutions]

ga = pygad.GA(
    num_generations=40,
    num_parents_mating=6,
    sol_per_pop=24,
    num_genes=8,
    fitness_func=batch_fitness,
    fitness_batch_size=4,
    parallel_processing=["thread", 4],
)
```

Use `parallel_processing=["process", N]` only when:

- the fitness function is picklable;
- the script has an `if __name__ == "__main__":` guard on platforms that need it;
- work per solution/batch is heavy enough to offset process overhead.

## 9. Callbacks and early stopping

```python
history = []

def on_generation(ga_instance):
    _, fitness, _ = ga_instance.best_solution(ga_instance.last_generation_fitness)
    history.append(float(fitness))
    if len(history) >= 5 and max(history[-5:]) - min(history[-5:]) < 1e-9:
        return "stop"


def on_stop(ga_instance, last_generation_fitness):
    print("completed", ga_instance.generations_completed)


ga = pygad.GA(
    num_generations=200,
    num_parents_mating=8,
    sol_per_pop=20,
    num_genes=6,
    fitness_func=fitness_func,
    on_generation=on_generation,
    on_stop=on_stop,
    stop_criteria=["time_30", "evaluations_5000"],
)
```

Use callback returns carefully. `on_fitness`, `on_parents`, `on_crossover`, and `on_mutation` can replace internal values, but only with exactly matching shapes.

## 10. Save, load, and continue

```python
from pathlib import Path
import pygad

state = Path("ga_state")  # Pass without .pkl.

ga.run()
ga.save(str(state))

loaded = pygad.load(str(state))
loaded.num_generations = 50  # Optional: set additional generations before continuing.
loaded.run()
```

Rules:

- `save()` appends `.pkl`; `load()` expects the filename without `.pkl`.
- Functions/classes referenced by a saved GA must remain importable or serializable by `cloudpickle`.
- Re-running an already run GA continues from its current generation state and extends `best_solutions`, `best_solutions_fitness`, `solutions`, and `solutions_fitness` rather than resetting them.

## 11. Run the bundled scripts

From this sub-skill directory, run:

```bash
python scripts/core_ga_smoke.py
python scripts/multi_objective_template.py --selector nsga2
python scripts/multi_objective_template.py --selector nsga3 --nsga3-num-divisions 4
```

The scripts create only temporary output files and print compact JSON summaries. They are safe smoke tests, not benchmarks.
