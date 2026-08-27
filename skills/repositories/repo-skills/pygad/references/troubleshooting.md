# PyGAD cross-cutting troubleshooting

Use this root guide before diving into sub-skill-specific errors. It covers environment, dependency, and routing issues that affect more than one PyGAD workflow.

## Fast triage

1. Run `import pygad; print(pygad.__version__)` in the same environment as the user's script.
2. Confirm whether the task is core GA, benchmarks, visualization/reporting, or neural adapters; then read the matching sub-skill.
3. Check optional dependencies only when the task needs them.
4. Keep a tiny deterministic reproduction with `random_seed` before scaling population, data, frameworks, or plots.
5. Remember that PyGAD maximizes fitness. Convert losses before debugging optimizer behavior.

## Install and import failures

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `ModuleNotFoundError: No module named 'pygad'` | PyGAD is not installed in the active Python environment. | Install with `python -m pip install pygad` inside the environment that runs the script. |
| `ModuleNotFoundError: No module named 'cloudpickle'` | Core dependency missing or incomplete install. | Reinstall PyGAD or install `cloudpickle`; verify with `python -m pip check`. |
| `ImportError` from `matplotlib` | Plot methods were called without visualization dependencies. | Install `pygad[visualize]` or `pygad[report]`. |
| `ImportError` from `reportlab` | `GA.generate_report()` needs the report extra. | Install `pygad[report]` or `reportlab`. |
| `ModuleNotFoundError: tensorflow` or `keras` | `pygad.kerasga` optional framework missing. | Install an appropriate TensorFlow/Keras stack or `pygad[deep_learning]`. |
| `ModuleNotFoundError: torch` | `pygad.torchga` optional framework missing. | Install PyTorch for the user's platform, then import `pygad.torchga`. |
| TensorFlow/Torch sees no GPU | Framework was installed CPU-only or host drivers/runtime are unavailable. | Treat GPU as optional unless the user required it; verify the framework backend before promising acceleration. |

## Choosing the right sub-skill

| User request | Route |
| --- | --- |
| “Why does my fitness function fail?” | `sub-skills/genetic-algorithm/references/troubleshooting.md` |
| “Use ZDT/DTLZ/Sphere/Knapsack/TSP” | `sub-skills/benchmarks/references/troubleshooting.md` |
| “Plot/report/summary/headless Matplotlib” | `sub-skills/results-and-visuals/references/troubleshooting.md` |
| “KerasGA/TorchGA/GANN/CNN weights are wrong” | `sub-skills/neural-networks/references/troubleshooting.md` |

## Reproducibility and state issues

- Set `random_seed` in `pygad.GA` for repeatable random initialization and operators.
- Saved GA state uses `cloudpickle`. A saved object can fail to load when custom fitness functions/classes changed or are no longer importable.
- `ga.run()` can be called again to continue from current state; create a new `GA` instance for a clean restart.
- `save_solutions=True` and `save_best_solutions=True` can grow memory usage quickly on long runs.

## Headless and CI issues

- Set `MPLBACKEND=Agg` in the environment or call `matplotlib.use("Agg", force=True)` before plotting.
- Create parent directories before using `save_dir` or `generate_report(filename=...)`.
- Close returned Matplotlib figures when generating many plots in one process.
- Use short deterministic smoke scripts first; long training or benchmarks should be opt-in.

## Optional cloud/export surface

`GA.push_to_vilvik()` is a convenience wrapper for an external service SDK and credentials. Do not use it as a default persistence method. Prefer local `GA.save()` and `pygad.load()` unless the user explicitly asks for cloud export and has configured the service.
