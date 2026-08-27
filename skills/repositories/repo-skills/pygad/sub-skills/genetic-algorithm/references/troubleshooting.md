# PyGAD GA troubleshooting

Use this guide when `pygad.GA` construction, `run()`, persistence, or custom operators fail. Most failures come from strict constructor validation or shape mismatches after custom callbacks/operators.

## Fast triage checklist

1. Can `import pygad, numpy` succeed in the active environment?
2. Does `fitness_func` accept exactly `(ga_instance, solution, solution_idx)` or, with batching, `(ga_instance, solutions, solution_indices)`?
3. Are `sol_per_pop`, `num_genes`, and `num_parents_mating` positive and consistent?
4. For multi-objective runs, does the fitness function return an iterable for every solution and use an NSGA selector when intended?
5. If using custom operators/callbacks, do all returned arrays have the expected shape?
6. If using save/load or process parallelism, are functions picklable/importable?

## Constructor and validation errors

| Symptom or message | Likely cause | Fix |
| --- | --- | --- |
| `ModuleNotFoundError: cloudpickle` while importing PyGAD | Core dependency missing. | Install PyGAD with its core dependencies in the runtime environment. |
| `fitness_func ... must accept 3 parameters` | Fitness function signature is outdated or missing `ga_instance`. | Define `def fitness_func(ga_instance, solution, solution_idx): ...`. For bound methods, the class `self` is implicit. |
| `initial_population is None ... sol_per_pop and num_genes cannot be None` | No starting population and missing shape parameters. | Pass a 2D `initial_population`, or pass both `sol_per_pop` and `num_genes`. |
| `num_parents_mating ... cannot be greater than ... sol_per_pop` | Too many parents requested. | Set `num_parents_mating <= sol_per_pop`. |
| Unknown `parent_selection_type` | Typo or unsupported selector. | Use one of `sss`, `rws`, `sus`, `rank`, `random`, `tournament`, `nsga2`, `tournament_nsga2`, `nsga3`, `tournament_nsga3`, or a valid custom callable. |
| Unknown `crossover_type` | Typo or unsupported crossover. | Use `single_point`, `two_points`, `uniform`, `scattered`, `sbx`, `None`, or a valid custom callable. |
| Unknown `mutation_type` | Typo or unsupported mutation. | Use `random`, `swap`, `inversion`, `scramble`, `adaptive`, `polynomial`, `None`, or a valid custom callable. |
| `crossover_probability` or `mutation_probability` must be between `0` and `1` | Probability outside inclusive range. | Clamp or rescale probability into `[0, 1]`. |
| `mutation_num_genes ... cannot be greater than num_genes` | Mutation count too high. | Set `mutation_num_genes <= num_genes`. |
| `mutation_percent_genes` must be `> 0` and `<= 100` | Invalid percentage. | Use the default percentage, a valid percentage, or set `mutation_num_genes`/`mutation_probability`. |
| Integer genes cannot have precision | `gene_type=[int, 2]` or similar. | Use `gene_type=int` or per-gene integer types without precision. Float precision is allowed, e.g. `gene_type=[float, 2]`. |
| Nested `gene_space` length does not equal `num_genes` | Per-gene value spaces do not match chromosome length. | Add/remove entries so `len(gene_space) == num_genes`. |
| `gene_space` dict missing keys | Dict lacks `low`/`high` or has unexpected keys. | Use `{"low": low, "high": high}` or `{"low": low, "high": high, "step": step}`. |
| `gene_constraint` count mismatch | Constraint list length differs from `num_genes`. | Provide exactly one item per gene (`None` for unconstrained genes). |
| `gene_constraint` callable accepts wrong number of arguments | Constraint not shaped as PyGAD expects. | Define `constraint(solution, values)` and return filtered candidate values. |
| `sample_size` must be positive | Candidate sampling size invalid. | Set `sample_size` to a positive integer, often higher for tight constraints. |

## Multi-objective and NSGA issues

| Symptom or message | Cause | Fix |
| --- | --- | --- |
| `single-objective ... parent selection type ... only works for multi-objective` | Fitness returns one scalar while an NSGA selector is configured. | Return a `list`, `tuple`, or `numpy.ndarray` of objective values, or switch to a single-objective selector. |
| Multi-objective run behaves like single objective | Fitness returns a NumPy scalar or Python float. | Return `[obj1, obj2, ...]` for each solution. |
| `nsga3_num_divisions` required | `parent_selection_type` is `nsga3` or `tournament_nsga3` without positive divisions. | Pass `nsga3_num_divisions=<positive int>`. |
| Warning that `sol_per_pop` is smaller than NSGA-III reference points | `C(M+p-1,p)` exceeds population size. | Increase `sol_per_pop` or lower `nsga3_num_divisions`. PyGAD can grow the population, but explicit sizing is more predictable. |
| `reach` stop criterion errors in multi-objective run | Wrong number of target values. | Use `reach_x` for one target shared by all objectives, or `reach_x_y_...` with exactly one value per objective. |
| Unsure which solution is “best” in MOO | A Pareto front has trade-offs; scalar best is not unique. | Inspect `ga.pareto_fronts` and `ga.last_generation_fitness`; `best_solution()` returns the top NSGA-II sort entry. |

## Run-time shape and callback errors

| Symptom | Cause | Fix |
| --- | --- | --- |
| `Size mismatch between selected parents ...` | Custom parent selection returned wrong shape. | Return parents with shape `(num_parents, ga_instance.num_genes)`. |
| `selected parents indices ... expected to have 1 dimension` | Custom selector returned nested or scalar indices. | Return a 1D NumPy array of indices length `num_parents`. |
| `output of crossover step ... expected numpy.ndarray` | Custom crossover returned list/tuple. | Return `numpy.array(offspring)` with shape `offspring_size`. |
| `Size mismatch between crossover output ...` | Custom crossover returned wrong number of rows/columns. | Respect the passed `offspring_size` exactly. |
| `output of mutation step ... expected numpy.ndarray` | Custom mutation returned list/tuple or `None`. | Return a NumPy array with the same shape as input offspring. |
| `Size mismatch between output of on_fitness/on_crossover/on_mutation` | Callback returned replacement data with wrong shape. | Return `None` to keep PyGAD's value, or return an exact shape match. |
| `on_parents` output length error | Callback returned only parents or malformed tuple. | Return `None` or `(parents, parent_indices)` with both valid. |
| `on_generation` does not stop | Callback returns non-string or a different string. | Return exactly `"stop"`; PyGAD lowercases the string before comparing. |

## Fitness evaluation surprises

| Symptom | Cause | Fix |
| --- | --- | --- |
| Fitness function is not called for solution index 0 in later generations | `keep_elitism=1` by default copies the best solution and reuses its fitness. | For forced re-evaluation, set `keep_elitism=0`, `keep_parents=0`, `save_solutions=False`, and `save_best_solutions=False`. |
| Fitness call count is lower than expected | Fitness reuse, batching, or early stopping. | Check `fitness_batch_size`, `stop_criteria`, `keep_elitism`, `keep_parents`, and saved histories. |
| Batch fitness raises mismatch error | Returned batch length differs from passed solution count. | Return exactly one fitness value/objective-vector per input solution. |
| Poor results for minimization | Raw loss returned and PyGAD maximizes it. | Return `-loss`, `1/(loss+epsilon)`, or another higher-is-better transformation. |
| Non-deterministic objective gives inconsistent reuse | PyGAD reuses deterministic fitness by design. | Disable retention/history as described above, or make the fitness deterministic under `random_seed`. |

## Gene-space, duplicate, and constraint issues

| Symptom | Cause | Fix |
| --- | --- | --- |
| PyGAD cannot find values satisfying constraints | Candidate pool too narrow or `sample_size` too low. | Enlarge `gene_space`, relax constraints, or increase `sample_size`. |
| Dependent constraints behave incorrectly | Constraint order conflicts with dependency direction. | Put dependency genes earlier in the solution than genes that read them. |
| Duplicate genes remain or warnings appear | `allow_duplicate_genes=False` but spaces cannot provide unique alternatives. | Ensure each solution can have enough unique values; use richer per-gene spaces. |
| Mutated values violate custom domain rules | Custom mutation bypassed PyGAD's built-in gene-space/type/constraint handling. | Enforce domain rules inside custom mutation or prefer built-in mutation with `gene_space`/`gene_constraint`. |
| Float dict range unexpectedly reaches rounded high value | Dict spaces sample values `< high`, but `gene_type=[float, precision]` can round up. | Adjust `high`, precision, or validation expectations. |

## Parallel processing and persistence

| Symptom | Cause | Fix |
| --- | --- | --- |
| Process parallelism hangs or fails on platform startup | Missing `if __name__ == "__main__":` guard or non-picklable function. | Add the guard around script entry and use top-level fitness functions/classes. |
| Threads/processes slower than serial execution | Fitness is too cheap; executor overhead dominates. | Use `parallel_processing=None` or batch fitness. Benchmark before assuming parallelism helps. |
| `pygad.load()` raises `FileNotFoundError` | Filename mismatch; `.pkl` handling misunderstood. | Pass the same base filename used with `save()`, without `.pkl`. |
| `pygad.load()` raises `BaseException("Error loading the file.")` | Unpickling failed, often because referenced functions/classes changed or are unavailable. | Restore/import the original functions/classes, or re-run from source configuration. |
| Saved histories grow unexpectedly after repeated `run()` calls | PyGAD extends histories on continuation. | Reset/recreate the GA for a fresh run, or manually clear histories only if you know downstream effects. |
| Memory grows with long runs | `save_solutions=True` or `save_best_solutions=True` retains many arrays. | Disable full histories unless required; keep only final `population` and `last_generation_fitness`. |

## Optional cloud persistence

If a user asks about pushing GA state to an external cloud service, confirm the dependency, account, and credential setup first. The safe default is local `save()`/`pygad.load()` only.
