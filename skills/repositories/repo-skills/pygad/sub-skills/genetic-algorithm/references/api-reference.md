# PyGAD genetic algorithm API reference

This reference covers the public `pygad.GA` workflow for custom optimization. It intentionally keeps plotting/report details minimal; use the visuals-focused sub-skill for those.

## Import and version expectations

```python
import pygad
import numpy
```

The inspected API is `pygad` 3.7.0. Core `GA` usage needs PyGAD's runtime dependencies, including `numpy` and `cloudpickle`. Visualization/report and neural-network extras are outside this sub-skill's default scope.

## `pygad.GA` constructor

```python
pygad.GA(
    num_generations,
    num_parents_mating,
    fitness_func,
    fitness_batch_size=None,
    initial_population=None,
    sol_per_pop=None,
    num_genes=None,
    init_range_low=-4,
    init_range_high=4,
    gene_type=float,
    parent_selection_type="sss",
    keep_parents=None,
    keep_elitism=1,
    K_tournament=3,
    nsga3_num_divisions=None,
    crossover_type="single_point",
    crossover_probability=None,
    sbx_crossover_eta=30,
    mutation_type="random",
    mutation_probability=None,
    polynomial_mutation_eta=20,
    mutation_by_replacement=False,
    mutation_percent_genes="default",
    mutation_num_genes=None,
    random_mutation_min_val=-1.0,
    random_mutation_max_val=1.0,
    gene_space=None,
    gene_constraint=None,
    sample_size=100,
    allow_duplicate_genes=True,
    on_start=None,
    on_fitness=None,
    on_parents=None,
    on_crossover=None,
    on_mutation=None,
    on_generation=None,
    on_stop=None,
    save_best_solutions=False,
    save_solutions=False,
    suppress_warnings=False,
    stop_criteria=None,
    parallel_processing=None,
    random_seed=None,
    logger=None,
)
```

Minimum useful construction requires:

- `num_generations`: non-negative integer. `0` is accepted but only evaluates the starting population.
- `num_parents_mating`: positive integer no larger than `sol_per_pop`.
- `fitness_func`: callable with the expected signature.
- Either `initial_population`, or both `sol_per_pop` and `num_genes`.

## Fitness function contract

### Per-solution fitness

```python
def fitness_func(ga_instance, solution, solution_idx):
    return fitness
```

- `solution` is one chromosome from `ga_instance.population`.
- `solution_idx` is its index in the current population.
- Return a single numeric value for single-objective optimization.
- Return a `list`, `tuple`, or `numpy.ndarray` for multi-objective optimization. Even a one-element iterable is treated as multi-objective.
- PyGAD maximizes every returned objective.

### Batch fitness

Set `fitness_batch_size=N` with `1 < N <= sol_per_pop`.

```python
def fitness_func_batch(ga_instance, solutions, solution_indices):
    return [score_solution(solution) for solution in solutions]
```

The return length must equal the number of passed solutions. For multi-objective batches, return one objective vector per solution.

### Deterministic vs non-deterministic scoring

PyGAD can reuse fitness for previously seen solutions through elitism, parent retention, and optional saved histories. For stochastic/noisy fitness, prefer:

```python
keep_elitism=0
keep_parents=0
save_solutions=False
save_best_solutions=False
```

## Population, genes, and constraints

| Parameter | Accepted forms | Notes |
| --- | --- | --- |
| `initial_population` | 2D list/tuple/NumPy array | If supplied, `sol_per_pop` and `num_genes` are inferred. Values must be numeric. |
| `sol_per_pop` | positive int | Required when `initial_population is None`. |
| `num_genes` | positive int | Required when `initial_population is None`. |
| `init_range_low`, `init_range_high` | scalar or per-gene iterable | Used only for random initial population where no specific `gene_space` value applies. Bounds need not be ordered. |
| `gene_type` | one numeric type; `[float_type, precision]`; per-gene list of types/pairs | Integer types cannot have precision. Float precision rounds gene values. |
| `gene_space` | `None`; flat list/tuple/range/array; nested per-gene list; dict with `low`/`high` and optional `step`; `None` inside a nested space | Dict ranges are sampled from `[low, high)`; `step` makes a discrete grid. Nested length must equal `num_genes`. |
| `allow_duplicate_genes` | bool | If `False`, PyGAD tries to keep values unique inside each solution. |
| `gene_constraint` | `None` or list/tuple length `num_genes` containing `None` or callables | Each callable is `constraint(solution, candidate_values)` and returns the filtered candidates. |
| `sample_size` | positive int | Candidate count used while satisfying duplicate and constraint rules; increase when valid values are rare. |

Gene constraints are evaluated in gene-index order. If gene B depends on gene A, put A earlier in the chromosome so its chosen value is visible to B's constraint.

## Parent selection

`parent_selection_type` may be a built-in string or a callable. Built-ins:

| Value | Use |
| --- | --- |
| `"sss"` | steady-state selection; default. |
| `"rws"` | roulette wheel selection. |
| `"sus"` | stochastic universal selection. |
| `"rank"` | rank-based selection. |
| `"random"` | random parent selection. |
| `"tournament"` | tournament selection using `K_tournament` candidates. |
| `"nsga2"` | NSGA-II non-dominated sorting + crowding distance for multi-objective problems. |
| `"tournament_nsga2"` | tournament using NSGA-II rank/crowding. |
| `"nsga3"` | NSGA-III selection using reference-point niching; requires `nsga3_num_divisions`. |
| `"tournament_nsga3"` | tournament using NSGA-III rank/niche count; requires `nsga3_num_divisions`. |

Custom selector signature:

```python
def parent_selection_func(fitness, num_parents, ga_instance):
    parents = numpy.empty((num_parents, ga_instance.num_genes))
    parent_indices = numpy.empty(num_parents, dtype=int)
    return parents, parent_indices
```

Both returned values must be `numpy.ndarray`; parents must have shape `(num_parents, num_genes)`, indices must be 1D of length `num_parents`.

### NSGA-III reference points

For `"nsga3"` or `"tournament_nsga3"`, set `nsga3_num_divisions` to a positive integer. With `M` objectives and `p = nsga3_num_divisions`, the reference-point count is:

```text
C(M + p - 1, p)
```

If `sol_per_pop` is smaller than that count, PyGAD warns and grows the population to the reference count before the generation loop.

## Elitism and parent retention

| Parameter | Behavior |
| --- | --- |
| `keep_elitism=1` | Keeps the best `K` solutions unchanged at the front of the next population. When nonzero, it takes priority over `keep_parents`. |
| `keep_elitism=0` | Enables `keep_parents` to decide retention. |
| `keep_parents=None` | Resolved to historical default `-1` (keep all selected parents) but ignored while `keep_elitism > 0`. |
| `keep_parents=-1` | Keep all selected parents when `keep_elitism=0`. |
| `keep_parents=0` | Keep no parents when `keep_elitism=0`; useful for stochastic fitness. |
| `keep_parents>0` | Keep that many selected parents when `keep_elitism=0`. |

`keep_parents` must be `>= -1`, `<= sol_per_pop`, and `<= num_parents_mating`. `keep_elitism` must be between `0` and `sol_per_pop`.

## Crossover

`crossover_type` may be a built-in string, a callable, or `None`.

| Value | Use |
| --- | --- |
| `"single_point"` | default single-point crossover. |
| `"two_points"` | two-point crossover. |
| `"uniform"` | uniform crossover. |
| `"scattered"` | random mask-based crossover. |
| `"sbx"` | simulated binary crossover for real-coded genomes; tune `sbx_crossover_eta` (positive, default `30`). |
| `None` | skip crossover; next generation reuses selected/current solutions subject to retention rules. |

`crossover_probability` is `None` or a number in `[0, 1]`.

Custom crossover signature:

```python
def crossover_func(parents, offspring_size, ga_instance):
    return numpy.ndarray(shape=offspring_size)
```

The return must be a `numpy.ndarray` with shape `(ga_instance.num_offspring, ga_instance.num_genes)`.

## Mutation

`mutation_type` may be a built-in string, a callable, or `None`.

| Value | Use |
| --- | --- |
| `"random"` | default random mutation. Uses `random_mutation_min_val`, `random_mutation_max_val`, and optionally `mutation_by_replacement`. |
| `"swap"` | swap two genes. |
| `"inversion"` | reverse a gene segment. |
| `"scramble"` | shuffle a gene segment. |
| `"adaptive"` | choose mutation rate based on below/above average fitness. |
| `"polynomial"` | polynomial mutation for real-coded genomes; tune `polynomial_mutation_eta` (positive, default `20`). |
| `None` | skip mutation. |

Mutation amount is resolved in this priority order:

1. `mutation_probability` if set.
2. `mutation_num_genes` if set.
3. `mutation_percent_genes`, defaulting from `"default"` to `10` percent.

For adaptive mutation, `mutation_probability`, `mutation_num_genes`, or `mutation_percent_genes` must be a list/tuple/array of exactly two values: `[rate_for_low_quality, rate_for_high_quality]`. The first value should be higher than the second; otherwise PyGAD warns.

Custom mutation signature:

```python
def mutation_func(offspring, ga_instance):
    return offspring
```

The returned object must be a `numpy.ndarray` with the same shape as the input offspring.

## Lifecycle callbacks

Callbacks are optional. Functions use these signatures; bound methods include their own `self` implicitly.

| Callback | Called when | Expected function signature | Optional return effect |
| --- | --- | --- | --- |
| `on_start` | before `run()` starts | `(ga_instance)` | ignored. |
| `on_fitness` | after population fitness is calculated at generation head | `(ga_instance, fitness_values)` | `None`, or replacement fitness with the same shape. |
| `on_parents` | after parent selection | `(ga_instance, selected_parents)` | `None`, or `(parents, parent_indices)` with valid shapes. |
| `on_crossover` | after crossover, even when crossover is disabled | `(ga_instance, offspring)` | `None`, or replacement offspring with same shape. |
| `on_mutation` | after mutation, even when mutation is disabled | `(ga_instance, offspring)` | `None`, or replacement offspring with same shape. |
| `on_generation` | after each completed generation | `(ga_instance)` | return string `"stop"` to end early. |
| `on_stop` | once before `run()` returns | `(ga_instance, last_generation_fitness)` | ignored. |

## Stopping, reproducibility, and parallelism

| Parameter | Contract |
| --- | --- |
| `stop_criteria` | `None`, one string, or list/tuple/array of strings. Supported forms: `"reach_<value>"`, `"saturate_<generations>"`, `"time_<seconds>"`, `"evaluations_<count>"`. Multi-objective `reach` may use one target for all objectives or one target per objective, e.g. `"reach_0.8_0.9"`. |
| `random_seed` | Seeds NumPy and Python `random` during construction. Use it for repeatable stochastic runs. |
| `parallel_processing` | `None`; positive int for that many threads; or `("thread", N)` / `("process", N)` where `N` is positive, `0`, or `None`. `0` disables parallelism. |
| `fitness_batch_size` | `None`/`1` for individual calls, or positive integer `<= sol_per_pop` for batched calls. |
| `suppress_warnings` | bool. Hides warnings but does not bypass validation. |
| `logger` | `logging.Logger` instance or `None`; invalid types raise `TypeError`. |

Use threads for I/O-bound fitness and processes for heavy CPU fitness that can be pickled. Simple fitness functions often run slower in parallel due to executor overhead.

## Run, inspect, save, and load

```python
ga.run()
solution, fitness, solution_idx = ga.best_solution(pop_fitness=ga.last_generation_fitness)
ga.save("my_ga_state")
loaded_ga = pygad.load("my_ga_state")
```

| API | Signature / behavior |
| --- | --- |
| `ga.run()` | Runs the generational loop. It can be called again to continue from the current `generations_completed` state; history arrays are extended rather than reset. |
| `ga.best_solution(pop_fitness=None)` | Returns `(best_solution, best_solution_fitness, best_match_idx)`. For multi-objective fitness it uses NSGA-II sorting to choose the top entry. |
| `ga.save(filename)` | Serializes the GA instance with `cloudpickle` and appends `.pkl` automatically. Pass the filename without suffix. |
| `pygad.load(filename)` | Loads a `.pkl` written by `save()`; pass the filename without suffix. Raises `FileNotFoundError` for missing files and `BaseException("Error loading the file.")` for unpickle failures. |
| `ga.summary(...)` | Prints a configuration/lifecycle summary. Keep detailed formatting/reporting in the visuals sub-skill. |

Relevant post-run attributes:

| Attribute | Meaning |
| --- | --- |
| `run_completed` | `True` only after `run()` completes gracefully. |
| `generations_completed` | Last completed generation count. |
| `population` | Current population array. |
| `last_generation_fitness` | Fitness of the current population. Multi-objective shape is `(sol_per_pop, num_objectives)`. |
| `previous_generation_fitness` | Prior generation fitness, used for reuse. |
| `last_generation_parents`, `last_generation_parents_indices` | Parent solutions and indices from the last selection. |
| `last_generation_offspring_crossover`, `last_generation_offspring_mutation` | Last generated offspring arrays. |
| `best_solutions`, `best_solutions_fitness` | Saved best solution history when enabled, and best-fitness trace. |
| `solutions`, `solutions_fitness` | Full solution history when `save_solutions=True`. |
| `best_solution_generation` | Generation index where the best fitness was reached; `-1` before a completed run. |
| `pareto_fronts` | Pareto fronts for multi-objective NSGA workflows. |
| `nsga3_reference_points` | Reference-point grid for NSGA-III selectors. |

## External cloud handoff

`GA` includes a `push_to_vilvik(...)` convenience wrapper, but it requires a separately installed SDK and external service credentials. Treat it as out-of-scope for safe default workflows; use only when the user explicitly asks for that service and has configured access.
