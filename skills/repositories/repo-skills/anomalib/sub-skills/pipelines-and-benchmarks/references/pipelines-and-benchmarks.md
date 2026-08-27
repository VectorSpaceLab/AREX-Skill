# Pipelines and Benchmarks Reference

Anomalib pipelines are an experimental orchestration layer for jobs that are independent enough to be run serially or in parallel. Use this reference to repair configs, explain runner behavior, and plan safe preflights. Do not treat a successful parse as permission to execute training or benchmark-scale work.

## Safe versus expensive paths

| Path | Safe by default? | What happens |
| --- | --- | --- |
| Import the public pipeline classes | Yes | Confirms the installed package exposes `Benchmark` and the tiled ensemble entrypoints. |
| Parse YAML and count grid combinations | Yes | Reads user config and predicts how many jobs a benchmark or tiled ensemble may generate. |
| Instantiate benchmark runner choices | Usually safe if done without `run()` | Checks CPU/CUDA runner selection; avoid running jobs. |
| Run `Benchmark().run(...)` | Expensive | Trains/tests every model-data-grid combination and saves CSV results. |
| Run tiled ensemble train/eval | Expensive and experimental | Trains one model per tile location, predicts, merges, optionally smooths/normalizes/thresholds, visualizes, and computes metrics. |
| Run the MEBin post-processing comparison benchmark | Benchmark-scale | Trains multiple models over multiple categories and post-processors; require explicit budget and dataset paths. |

## Pipeline mental model

A pipeline has four moving parts:

1. **Pipeline** parses a YAML config from `--config`, sets up runners, and passes the previous stage output to the next runner.
2. **Runner** schedules jobs. `SerialRunner` runs jobs one by one; `ParallelRunner` uses a spawned process pool and passes a numeric `task_id` to each job.
3. **JobGenerator** reads the config section for one job name and yields concrete `Job` instances. It must expose `job_class`.
4. **Job** is the atomic unit of work. It implements `run(task_id=None)`, `collect(results)`, and `save(gathered_results)`. Its class-level `name` is the config section key that the pipeline passes to that runner.

Pipeline stages are chained through the runner return value. A downstream generator can consume the previous stage result, or ignore it for independent jobs such as benchmark trials.

### Custom pipeline checklist

When explaining or drafting a custom pipeline, keep the job independent of the runner:

```python
class MyJob(Job):
    name = "my_stage"

    def run(self, task_id: int | None = None):
        ...

    @staticmethod
    def collect(results):
        ...

    @staticmethod
    def save(results):
        ...
```

Then pair it with a generator that parses only the `my_stage:` config subtree, and a `Pipeline._setup_runners(args)` method that returns a list such as `[SerialRunner(MyGenerator()), SerialRunner(NextGenerator())]`. Use `ParallelRunner(generator, n_jobs=...)` only for jobs that are independent, process-spawn safe, and able to use `task_id` for device assignment.

## Benchmark pipeline

Use `Benchmark` for model/data grid benchmarking. A future agent can call the package CLI when available:

```bash
anomalib benchmark --config benchmark.yaml
```

or use the Python class without relying on source-checkout scripts:

```python
from argparse import Namespace
from anomalib.pipelines import Benchmark

Benchmark().run(Namespace(config="benchmark.yaml"))
```

### Benchmark config shape

The top-level config must include `accelerator` and `benchmark`:

```yaml
accelerator: cpu
benchmark:
  seed:
    grid: [42, 51]
  model:
    class_path:
      grid: [Padim, Patchcore]
  data:
    class_path: MVTecAD
    init_args:
      category:
        grid:
          - bottle
          - capsule
      image_size: [256, 256]
```

Important details:

- Use the key `grid` for current tested configs. The grid iterator expands every nested `grid` leaf into a Cartesian product and then removes the `.grid` suffix in the generated config.
- Keep static values as ordinary YAML values. Do not wrap a value in `grid` unless it should multiply the job count.
- The benchmark generator flattens each expanded config into dotted keys for the results table, then instantiates the model and datamodule from the expanded config.
- Each benchmark job seeds the run, creates a temporary engine root, calls `fit`, then `test`, and returns timing fields plus test metrics.
- Results are printed as a table and saved under a timestamped `runs/benchmark/.../results.csv` path relative to the current working directory.

### Runner selection and CPU/CUDA fallback

Benchmark runner selection is entirely controlled by the top-level `accelerator` value:

| Config value | Runner behavior |
| --- | --- |
| `accelerator: cpu` | One `SerialRunner` with a CPU benchmark generator. |
| `accelerator: [cpu]` | Same as CPU serial, with a list form. |
| `accelerator: cuda` with more than one visible CUDA device | One `ParallelRunner` with `n_jobs=torch.cuda.device_count()`. Each process receives a `task_id` that maps to a CUDA device index. |
| `accelerator: cuda` with zero or one visible CUDA device | Falls back to `SerialRunner`, but the job still asks the engine for CUDA. On a CPU-only host, prefer changing the config to CPU instead of relying on this path. |
| `accelerator: [cuda, cpu]` | Creates a CUDA runner and a CPU runner; both consume the same `benchmark` grid. |
| Any other value | Unsupported for this benchmark pipeline and should be rejected before execution. |

To switch a benchmark from CUDA parallelism to CPU serial execution without losing the grid, change only the top-level accelerator:

```yaml
accelerator: cpu
benchmark:
  # keep the entire existing benchmark tree unchanged
```

Run the bundled smoke helper to count grid combinations and catch accidental `grid_search`/`grid` mismatches before the expensive run.

## Benchmark-scale MEBin comparison

The repository includes a standalone post-processing comparison benchmark that trains PatchCore, PaDiM, and AnomalyDINO across several MVTec categories and compares the default post-processor against MEBin. Treat it as reference-only unless the user explicitly asks to run a benchmark-scale experiment. Before running any equivalent workflow, require:

- a concrete MVTec root or other dataset plan;
- selected categories, models, and post-processors;
- output CSV path;
- runtime and hardware budget;
- permission to create results directories and train multiple models.

If the user only wants the idea, explain the loop structure rather than running it: for each model/category/post-processor combination, create a fresh datamodule and model, run `Engine.fit`, run `Engine.test`, collect image/pixel metrics, and write rows to CSV.

## Advanced CLI scripts versus pipeline orchestration

Some advanced shell examples show CLI training flags, metrics, and hyperparameter loops. Treat those as configuration examples, not as first-class pipeline components. They belong to core training/evaluation guidance unless the user is explicitly asking how to translate the idea into a `Pipeline`/`Job`/`JobGenerator` structure.
