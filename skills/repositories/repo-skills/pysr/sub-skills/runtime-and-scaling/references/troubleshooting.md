# Runtime troubleshooting

Use this reference for install, import, startup, parallelism, scheduler, and runtime-budget failures. For bad equations, operator domain bugs, custom losses, constraints, or structural tuning, route to `customization-and-constraints`. For missing hall-of-fame/checkpoint/export artifacts, route to `export-and-artifacts`.

## Symptom table

| Symptom | Likely cause | Action |
| --- | --- | --- |
| First `import pysr` takes a long time | JuliaCall is locating/installing Julia packages and loading SymbolicRegression | Wait if progress is visible. In future jobs, warm the environment/cache before launching many runs. |
| First `.fit()` takes much longer than later fits | Julia JIT compilation in the process | Keep the Python process alive while iterating; avoid repeated short script relaunches. |
| Warning that `juliacall` was already imported | PySR cannot set its JuliaCall defaults after JuliaCall is loaded | Start a fresh process. Set `PYTHON_JULIACALL_THREADS`, `PYTHON_JULIACALL_HANDLE_SIGNALS`, and `PYTHON_JULIACALL_OPTLEVEL` before imports. |
| Warning about `PYTHON_JULIACALL_THREADS` | Thread policy was already explicitly set | If the value is intentional, continue. If not, start a fresh process with the desired value or `auto`. |
| Changing `PYTHON_JULIACALL_THREADS` has no effect | Julia threads are fixed at Julia startup | Set it before import and restart the Python process. |
| Import crash mentioning `GLIBCXX_... not found` | Incompatible C++ runtime loaded by another package/environment | Use a cleaner environment, import PySR before large compiled packages, or put the correct Julia library directory first in `LD_LIBRARY_PATH`. |
| Startup appears hung in a notebook or embedded runner | PySR stdin watcher cannot read from the environment | Pass `input_stream="devnull"`; use `timeout_in_seconds` or `max_evals` because notebook interactive stop is limited. |
| Cannot stop search with `q` in Jupyter | Notebook stdin does not behave like terminal/IPython stdin | Use explicit time/evaluation bounds or run from terminal/IPython for interactive `q` then Enter. |
| Julia package lock or `lock.pid` blocks import after a killed job | Previous Julia package operation was interrupted | Confirm no installer/import process is still running, then clear the stale lock according to your environment policy and import once in a fresh process. |
| `python -m pysr --help` is slow | The CLI imports PySR before showing help | Treat CLI help as an import check. Use the bundled probe with `--skip-import` for a no-import metadata check. |
| `python -m pysr install` does nothing useful | CLI install command is deprecated | Install with pip/conda; dependencies are resolved at first import. |
| Slurm job starts multiple independent searches | Python script was wrapped in `srun` | Submit one batch script or run one Python coordinator inside the allocation; let PySR start Julia workers with `cluster_manager="slurm"`. |
| Slurm workers do not match allocation | `procs` does not equal total allocated tasks | Set `procs = nodes * ntasks-per-node` or the allocation's `--ntasks` value. |
| Cluster manager error says multiprocessing is required | `cluster_manager` was set without `parallelism="multiprocessing"` | Set both `parallelism="multiprocessing"` and the cluster manager. |
| Worker cannot find a Julia package used by a custom operator/loss | Package is not loaded on workers | Add module names to `worker_imports=[...]` and ensure the Julia environment contains them. Operator/loss design belongs in `customization-and-constraints`. |
| Worker timeouts/restarts on long distributed runs | Worker startup, package load, or evaluation is slow | Increase `worker_timeout`; reduce worker count for diagnosis; pre-warm packages; inspect custom Julia code for slow imports. |
| Memory pressure in multiprocessing or Slurm | Too many workers, large data, or Julia heap behavior | Reduce `procs`, batch/subsample data, or set `heap_size_hint_in_bytes` for Julia workers. |
| Results differ between runs despite `random_state` | Parallel searches are stochastic | For deterministic reproduction, use `deterministic=True`, fixed `random_state`, and `parallelism="serial"`. |
| Results differ slightly across machines | Floating-point, Julia, CPU, or backend differences | Record package/backend versions. Use `precision=64` if numerical sensitivity matters. |
| Large dataset run is slow | Full-data evaluation is dominating mutation time | Use representative subsampling or `batching=True`/`batching="auto"` with an explicit `batch_size`. Search-space design is a separate tuning problem. |
| Noninteractive job runs forever | Missing wall-clock/evaluation cap | Always set `timeout_in_seconds`, `max_evals`, or a clear `early_stop_condition` in automation. |

## Startup triage sequence

1. Check package metadata and environment variables without import:

   ```bash
   python scripts/pysr_environment_probe.py --skip-import --json
   ```

2. If thread settings are wrong, fix the shell/job environment and start a fresh process.
3. Run the import probe when first Julia setup is acceptable:

   ```bash
   python scripts/pysr_environment_probe.py --json
   ```

4. If import succeeds, run `python -m pysr --help` or the probe's `--check-cli` only if a CLI smoke check is needed.
5. Before a long run, execute a bounded tiny fit with `input_stream="devnull"`, `timeout_in_seconds`, and `max_evals`.

## Slurm triage sequence

1. Confirm there is an active allocation or batch job with the expected total task count.
2. Confirm the Python script is launched once, not through `srun`.
3. Set:

   ```python
   PySRRegressor(
       parallelism="multiprocessing",
       cluster_manager="slurm",
       procs=<total_tasks>,
       input_stream="devnull",
   )
   ```

4. If custom Julia packages are used, add `worker_imports` and verify the packages exist in the Julia environment used by workers.
5. If startup is slow but eventually succeeds, pre-warm Julia/PySR once before launching many jobs.

## When not to treat as a runtime problem

- Poor equation quality, invalid custom operator domains, loss-function type instability, missing SymPy mappings, and over-tight constraints are owned by `customization-and-constraints`.
- Choosing rows from `equations_`, reading hall-of-fame CSVs, reloading checkpoints, and exporting to SymPy/LaTeX/JAX/Torch are owned by `export-and-artifacts`.
- Known structural templates and vector-valued/differential expressions are owned by `structured-expressions`.
