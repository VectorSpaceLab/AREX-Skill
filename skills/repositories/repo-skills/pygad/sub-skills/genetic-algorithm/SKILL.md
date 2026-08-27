---
name: genetic-algorithm
description: "Build, tune, run, persist, and troubleshoot pygad.GA for custom
  single- and multi-objective optimization."
metadata:
  disco-role: operating
disable-model-invocation: true
license: BSD 3-Clause
---

# genetic-algorithm

Use this sub-skill when the task is to configure and operate `pygad.GA` directly: define a fitness function, shape the population and genes, choose selection/crossover/mutation operators, run single- or multi-objective optimization, inspect the best solution, persist a run, or debug GA validation/runtime errors.

## Route elsewhere

- Built-in benchmark problem classes, ZDT/DTLZ/knapsack/TSP, or quality indicators: use the `benchmarks` sub-skill.
- Plotting, report PDFs, headless `matplotlib`, or detailed visual summaries: use the `results-and-visuals` sub-skill.
- NN/GANN/CNN/KerasGA/TorchGA model-weight optimization: use the `neural-networks` sub-skill.

## Operating flow

1. **Frame the genome and objective.** Decide `num_genes`, `sol_per_pop`, value bounds/choices (`gene_space`), type/precision (`gene_type`), and whether the fitness is single-objective (return one number) or multi-objective (return `list`, `tuple`, or `numpy.ndarray`).
2. **Write a valid fitness function.** Public functions must accept `(ga_instance, solution, solution_idx)`. With `fitness_batch_size`, the second/third arguments become batches and the return must contain one fitness value per solution.
3. **Instantiate `pygad.GA`.** Set at least `num_generations`, `num_parents_mating`, `fitness_func`, and either `initial_population` or both `sol_per_pop` and `num_genes`.
4. **Tune operators.** Use built-ins first (`parent_selection_type`, `crossover_type`, `mutation_type`), then custom callables only when the built-ins cannot express the workflow.
5. **Run and inspect.** Call `ga.run()`, then `ga.best_solution(ga.last_generation_fitness)`, `ga.run_completed`, `ga.generations_completed`, and `ga.best_solution_generation`.
6. **Persist if needed.** Call `ga.save(filename_without_pkl)` and restore with `pygad.load(filename_without_pkl)`. The `.pkl` suffix is added automatically.

## Reference map

- Constructor signatures, public method contracts, operators, callbacks, attributes, and validation rules: [references/api-reference.md](references/api-reference.md)
- Recipes for single-objective, multi-objective, adaptive mutation, gene constraints, custom operators, parallel/batch fitness, callbacks, and save/load continuation: [references/workflows.md](references/workflows.md)
- Error diagnosis and corrective actions: [references/troubleshooting.md](references/troubleshooting.md)

## Bundled safe scripts

- [scripts/core_ga_smoke.py](scripts/core_ga_smoke.py): deterministic single-objective GA smoke with binary genes, callback assertions, and save/load through a temporary file.
- [scripts/multi_objective_template.py](scripts/multi_objective_template.py): deterministic NSGA-II/NSGA-III template for a two-objective trade-off; accepts `--selector` for NSGA variants and writes only temporary state.

## Safety notes

- PyGAD maximizes fitness. Convert minimization losses to maximization scores, for example with `-loss` or `1 / (loss + epsilon)`.
- Keep `save_solutions=True` and `save_best_solutions=True` off for large populations unless the user explicitly needs full history.
- Use process-based `parallel_processing` only when the fitness function is picklable and expensive enough to offset process overhead.
- Do not use external cloud persistence from a GA object unless the user explicitly supplies the service intent, dependency, and credentials.
