# PyGAD capability map

## Package purpose

PyGAD is a Python genetic-algorithm library for single-objective and multi-objective optimization. The main `pygad.GA` class is the generic optimizer; surrounding modules provide benchmark problem callables, visualization/reporting utilities, pure NumPy neural-network helpers, and Keras/PyTorch weight-vector adapters.

## Module map

| Module | Primary APIs | Owned by sub-skill | Notes |
| --- | --- | --- | --- |
| `pygad` / `pygad.pygad` | `GA`, `load`, `GA.save`, `GA.run`, `GA.best_solution`, `GA.summary`, `GA.push_to_vilvik` | `genetic-algorithm` for optimizer; `results-and-visuals` for summary/report; root note for external cloud handoff | Core user entry point. |
| `pygad.utils.parent_selection` | `ParentSelection`, selectors `sss`, `rws`, `sus`, `rank`, `random`, `tournament`, NSGA variants | `genetic-algorithm` | Usually configured through `parent_selection_type`. |
| `pygad.utils.crossover` | crossover operators including `single_point`, `two_points`, `uniform`, `scattered`, `sbx` | `genetic-algorithm` | Usually configured through `crossover_type`. |
| `pygad.utils.mutation` | mutation operators including `random`, `swap`, `inversion`, `scramble`, `adaptive`, `polynomial` | `genetic-algorithm` | Usually configured through `mutation_type`. |
| `pygad.utils.nsga`, `nsga2`, `nsga3` | non-dominated sorting, crowding, NSGA-III reference points | `genetic-algorithm`; `benchmarks` for benchmark use | Used automatically by NSGA selectors and MOO plots. |
| `pygad.benchmarks.classic` | `Sphere`, `Rastrigin`, `Rosenbrock`, `Griewank`, `Schwefel`, `Ackley`, `Himmelblau` | `benchmarks` | Callable fitness problems in PyGAD maximization form. |
| `pygad.benchmarks.zdt` | `ZDT1`, `ZDT2`, `ZDT3`, `ZDT4`, `ZDT6` | `benchmarks` | Two-objective problems; most ship `pareto_front()`. |
| `pygad.benchmarks.dtlz` | `DTLZ1`, `DTLZ2`, `DTLZ3`, `DTLZ4` | `benchmarks` | Many-objective problems, suited to NSGA-III. |
| `pygad.benchmarks.knapsack` | `Knapsack` | `benchmarks` | Binary genome with capacity penalty. |
| `pygad.benchmarks.tsp` | `TSP` | `benchmarks` | Permutation genome with negative tour length fitness. |
| `pygad.utils.quality_indicators` | `hypervolume`, `inverted_generational_distance`, `generational_distance`, `spacing` | `benchmarks` | All expect PyGAD maximization-form objective arrays. |
| `pygad.visualize.plot` | `plot_fitness`, Pareto plots, diversity/history plots | `results-and-visuals` | Mixed into `GA`; requires `matplotlib` at call time. |
| `pygad.utils.report` | `GA.generate_report()` | `results-and-visuals` | Requires `matplotlib` and `reportlab`. |
| `pygad.nn`, `pygad.gann` | dense NumPy layers and GA populations | `neural-networks` | Core dependency only. |
| `pygad.cnn`, `pygad.gacnn` | pure NumPy CNN layers and GA populations | `neural-networks` | Keep data tiny for smoke checks. |
| `pygad.kerasga` | `KerasGA`, Keras weight vector/matrix helpers, prediction | `neural-networks` | Requires TensorFlow/Keras. |
| `pygad.torchga` | `TorchGA`, PyTorch weight vector/dict helpers, prediction | `neural-networks` | Requires PyTorch. |

## Cross-sub-skill workflow dependencies

- A built-in benchmark run usually starts in `benchmarks`, then routes to `genetic-algorithm` if custom GA operators or constraints are needed, and to `results-and-visuals` for plots/reports.
- A neural-network GA workflow starts in `neural-networks`, but its actual `pygad.GA` constructor choices are still governed by `genetic-algorithm`.
- A multi-objective custom run starts in `genetic-algorithm`; if it uses ZDT/DTLZ or quality indicators, also read `benchmarks`.
- Any completed run that needs a figure, summary, PDF, headless plotting, or logging guidance routes to `results-and-visuals`.

## High-value validation patterns

- Core optimizer: run a tiny deterministic GA with `random_seed`, assert `run_completed`, inspect `best_solution`, then save/load through `pygad.load()`.
- Multi-objective: assert `last_generation_fitness` is 2D and inspect `pareto_fronts`; for NSGA-III, check `nsga3_reference_points` count.
- Benchmarks: call the benchmark object directly on a hand-built solution before wiring it into a GA.
- Visualization/reporting: set a headless backend, call the target plot with `save_dir`, assert the output file exists, and close the figure.
- Neural adapters: round-trip model weights from model/network to vector and back before running a GA.

## Explicitly out of default scope

- Long benchmark sweeps, production-scale training, and large image datasets are not safe default smoke checks.
- External cloud push workflows require the user's service intent, SDK dependency, and credentials.
- Legacy tutorial/Cython implementations are evidence only; this skill focuses on the current public `pygad` package API.
