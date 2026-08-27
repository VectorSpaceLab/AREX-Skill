# Scaling and parallelism

Use this reference to choose runtime controls after the model's operators, losses, and constraints have already been chosen. For search-space design, route to `customization-and-constraints`; for inspecting outputs after the run, route to `export-and-artifacts`.

## Parallelism modes

| Mode | Use when | Required knobs | Caveats |
| --- | --- | --- | --- |
| `parallelism="multithreading"` or `None` | Normal laptop, workstation, or single-node use | Set `PYTHON_JULIACALL_THREADS` before import if you need a fixed thread count | One Julia runtime in the Python process. `procs` is ignored. |
| `parallelism="serial"` | Tiny smoke checks or fully deterministic reproduction | Set `deterministic=True` and fixed `random_state` for reproducibility | Slow for real searches. |
| `parallelism="multiprocessing"` | Long runs where extra Julia worker startup is worth it | Set `procs=<worker count>`; if omitted, PySR uses available CPU count | Higher startup cost and more worker failure modes. |
| `parallelism="multiprocessing", cluster_manager="slurm"` | Multi-node Slurm allocation | Set `procs` equal to total allocated tasks | Launch one Python script inside the allocation; do not wrap it in `srun`. |

Other supported cluster manager names include `pbs`, `lsf`, `sge`, `qrsh`, `scyld`, and `htc`, but Slurm is the documented and tested multi-node path in this skill.

## Thread startup rule

Thread count is fixed when Julia starts. Set it before import:

```bash
export PYTHON_JULIACALL_THREADS=8
python my_pysr_run.py
```

Inside Python, this is acceptable only if it happens before any PySR/JuliaCall import:

```python
import os
os.environ["PYTHON_JULIACALL_THREADS"] = "8"

from pysr import PySRRegressor
```

If PySR warns that JuliaCall was already imported, start a fresh process and set the environment first.

## Populations and coordination overhead

- Keep `populations` larger than the number of workers/threads so every worker has candidates to process. A common starting point is roughly `2x` to `3x` the number of workers.
- On many-core or multi-node runs, raise `ncycles_per_iteration` to reduce how often workers communicate with the coordinator. This can lower head-node load, but it also delays hall-of-fame migration.
- Do not tune parallelism before confirming the model can produce sensible equations on a small bounded run.

## Large datasets and batching

For large row counts, symbolic regression usually benefits more from representative data than from evaluating every row in every mutation.

Practical recipe:

```python
model = PySRRegressor(
    niterations=200,
    batching=True,          # or keep the default "auto"
    batch_size=256,         # optional; leave None for backend defaults
    timeout_in_seconds=1800,
    max_evals=1_000_000,
    input_stream="devnull",
)
```

Batching compares population members on mini-batches during evolution, but still evaluates on the full dataset when comparing against the hall of fame. Use it when data are noisy, high-dimensional, or too large for full evaluation at mutation time. If only a small representative subset is needed, subsampling before `.fit()` may be simpler and faster.

## Budget controls

Use multiple independent bounds for safe agent-driven runs:

| Control | Meaning | Use |
| --- | --- | --- |
| `niterations` | Evolution iterations/generations | Set high for final runs, low for smoke checks. |
| `timeout_in_seconds` | Wall-clock limit | Best default safety cap for notebooks, CI, services, and batch jobs. |
| `max_evals` | Total expression-evaluation cap | Good for compute-matched comparisons; not the same as `niterations * populations * population_size`. |
| `early_stop_condition` | Loss threshold or Julia predicate on `(loss, complexity)` | Stop when a target-quality/simple equation appears. |
| `input_stream` | Where PySR reads user stop commands | Use `"stdin"` for terminal/IPython stop with `q`; use `"devnull"` for noninteractive runs. |

Example early stop predicate:

```python
PySRRegressor(
    niterations=1_000_000,
    timeout_in_seconds=6 * 3600,
    early_stop_condition="stop_if(loss, complexity) = loss < 1e-6 && complexity < 12",
    input_stream="devnull",
)
```

In terminal/IPython, the user can press `q` then Enter to stop gracefully. In notebooks, prefer explicit time/evaluation caps because interactive stop behavior is less reliable.

## Deterministic reproduction

For a run intended to be repeatable on the same software/hardware stack:

```python
model = PySRRegressor(
    deterministic=True,
    random_state=0,
    parallelism="serial",
    niterations=50,
    input_stream="devnull",
)
```

Warnings:

- A fixed `random_state` without `deterministic=True` and `parallelism="serial"` is not a deterministic search.
- Parallel searches are stochastic even when seeded.
- Different CPU architectures, Julia versions, precision choices, or backend revisions can still shift floating-point details. Use `precision=64` when numerical sensitivity matters.

## Slurm pattern

Request resources with `sbatch` or `salloc`, then run one Python process inside the allocation. PySR uses SlurmClusterManager on the Julia side to start workers.

Job script shape:

```bash
#!/bin/bash
#SBATCH --job-name=pysr
#SBATCH --partition=normal
#SBATCH --nodes=2
#SBATCH --ntasks-per-node=3
#SBATCH --time=01:00:00

set -euo pipefail
export PYTHON_JULIACALL_THREADS=auto
python pysr_script.py
```

Python script shape:

```python
import numpy as np
from pysr import PySRRegressor

rng = np.random.RandomState(0)
X = rng.randn(1000, 2)
y = X[:, 0] + 2 * X[:, 1]

model = PySRRegressor(
    niterations=200,
    populations=6,
    parallelism="multiprocessing",
    cluster_manager="slurm",
    procs=6,                 # nodes * ntasks-per-node
    input_stream="devnull",
)
model.fit(X, y)
print(model)
```

Slurm rules:

- `procs` must equal the total task count allocated to the job.
- Submit the batch script once with `sbatch`, or start an interactive allocation and run Python once.
- Do **not** run `srun python pysr_script.py`; that launches multiple independent Python coordinators instead of one PySR coordinator.
- Use `worker_imports=[...]` when custom Julia packages must be loaded on every worker.
- Use `heap_size_hint_in_bytes` only for multiprocessing/cluster runs that need a Julia heap-size hint per worker.

## Multiprocessing worker options

```python
PySRRegressor(
    parallelism="multiprocessing",
    procs=8,
    worker_timeout=120,
    worker_imports=["SpecialFunctions"],
    heap_size_hint_in_bytes=2_000_000_000,
)
```

- `worker_timeout` restarts workers that stop responding.
- `worker_imports` runs `using <module>` on workers; it is for Julia modules used by operators/losses/backend code.
- `heap_size_hint_in_bytes` passes a memory hint to Julia workers and is mainly useful in distributed or memory-constrained jobs.

## Container and scheduler interaction

When running inside Docker or Apptainer under a scheduler:

- Keep one Python coordinator process per PySR run.
- Ensure the container can write output/checkpoint directories; route artifact inspection to `export-and-artifacts`.
- Pre-warm the Julia package cache when many jobs will start concurrently.
- Avoid oversubscription: scheduler tasks, JuliaCall threads, and multiprocessing `procs` should describe the same resource plan, not multiply each other accidentally.
