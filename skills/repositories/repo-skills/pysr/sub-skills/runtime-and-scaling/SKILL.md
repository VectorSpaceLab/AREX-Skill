---
name: runtime-and-scaling
description: "Install, start, probe, and scale PySR runtime without tuning equations."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# PySR runtime and scaling

Use this sub-skill when the task is about making PySR import, start its Julia/SymbolicRegression backend, run within a resource budget, use threads/processes/Slurm safely, or call PySR's command-line test wrapper. Keep equation design, operators, constraints, losses, and objective debugging routed to `customization-and-constraints`; keep hall-of-fame CSVs, checkpoints, SymPy/LaTeX/JAX/Torch export, and reload work routed to `export-and-artifacts`.

## Route within this sub-skill

| Request | Use |
| --- | --- |
| Install PySR, choose pip/conda/source, explain first import, set JuliaCall environment variables, containers, backend checkout | `references/install-runtime.md` |
| Pick `parallelism`, `procs`, Slurm settings, batching, time/evaluation budgets, deterministic recipe | `references/scaling-and-parallelism.md` |
| Run or interpret `python -m pysr` commands and native test subsets | `references/cli-reference.md` |
| Diagnose import hangs, Julia package resolution, stdin/notebook hangs, GLIBCXX, worker, Slurm, and reproducibility symptoms | `references/troubleshooting.md` |
| Probe an environment without fitting a model | `scripts/pysr_environment_probe.py` |

## Non-negotiable runtime facts

- `import pysr` imports JuliaCall and loads the SymbolicRegression Julia backend. On a fresh environment, the first import can download or resolve Julia packages; the first fit can spend additional time compiling Julia code. Do not diagnose that alone as a failed search.
- Set JuliaCall environment variables **before** any `import pysr` or `import juliacall`. PySR sets sensible defaults only if JuliaCall was not already imported. For thread control use `PYTHON_JULIACALL_THREADS=<n>` or `auto` before import; `JULIA_NUM_THREADS` is not the PySR/JuliaCall control path.
- In notebooks, embedded shells, CI, or noninteractive runners that may not provide usable stdin, pass `input_stream="devnull"` to `PySRRegressor` and bound the run with `timeout_in_seconds` or `max_evals`.
- The default search is multithreaded. Use `parallelism="serial"` only for tiny checks or deterministic reproduction; use `parallelism="multiprocessing"` with `procs=...` only when the extra Julia worker startup cost is worth it.
- Slurm is launched from one Python process inside an existing allocation: `parallelism="multiprocessing", cluster_manager="slurm", procs=<total allocation tasks>`. Do not wrap the Python script in `srun`.
- Deterministic runs require all three: `deterministic=True`, a fixed `random_state`, and `parallelism="serial"`. Seeded parallel runs remain stochastic.

## Fast safe probe

The bundled probe never fits a model. Start with the no-import form when you only need package metadata and environment-variable state:

```bash
python scripts/pysr_environment_probe.py --skip-import --json
```

Then, when a first import/Julia initialization is acceptable:

```bash
python scripts/pysr_environment_probe.py --json
python scripts/pysr_environment_probe.py --json --check-cli
```

`--check-cli` is intentionally optional because `python -m pysr --help` imports the package and can trigger the same first-import Julia setup.

## Minimal bounded run template

```python
import os

# Must happen before import pysr/juliacall if overriding the default thread policy.
os.environ.setdefault("PYTHON_JULIACALL_THREADS", "auto")

import numpy as np
from pysr import PySRRegressor

rng = np.random.RandomState(0)
X = rng.randn(200, 2)
y = X[:, 0] + 2 * X[:, 1]

model = PySRRegressor(
    niterations=20,
    timeout_in_seconds=120,
    max_evals=50_000,
    binary_operators=["+", "*", "-"],
    parallelism="multithreading",
    input_stream="devnull",
    random_state=0,
)
model.fit(X, y)
print(model.equations_)
```

For operator or loss changes in this template, route to `customization-and-constraints`. For inspecting the resulting equation table or persisted files, route to `export-and-artifacts`.
