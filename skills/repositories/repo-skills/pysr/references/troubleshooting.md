# Cross-cutting PySR Troubleshooting

Start here for broad symptoms, then follow the owner link for detailed recovery.

| Symptom | Likely cause | First response | Owner |
| --- | --- | --- | --- |
| Fresh `import pysr` appears stuck or slow | JuliaCall is resolving/downloading Julia packages or precompiling SymbolicRegression.jl | Wait long enough for first setup, use `scripts/check_pysr_environment.py --json`, and avoid repeatedly starting fresh processes while diagnosing | `sub-skills/runtime-and-scaling/` |
| First `.fit()` takes much longer than later fits | Julia compilation happens per Python process | Keep a long-lived Python/IPython process for iterative experiments | `runtime-and-scaling`, `fit-and-diagnose` |
| Notebook or embedded runner hangs around input/interrupt behavior | stdin/progress handling is not interactive | Use `input_stream="devnull"`, disable progress if needed, and bound the run with timeout/evaluation limits | `runtime-and-scaling` |
| Search returns constants or very tiny equations | Operators/search space/data scale/loss do not expose the signal, or `maxsize` is too small | Inspect data, simplify operators, add needed operators, adjust loss/weights, increase `maxsize`, and rerun bounded tests | `sub-skills/fit-and-diagnose/` |
| Search is slow or bloated | Too many redundant operators, too many rows/features, or over-large search space | Subsample, use `select_k_features`/`batching`, remove redundant operators, and tune constraints | `fit-and-diagnose`, `customization-and-constraints` |
| Custom operator causes domain errors or export failures | Operator is not total on real inputs, has Float64 literals in Float32 mode, or lacks mapping | Add typed `NaN` guards and `extra_sympy_mappings`; add JAX/Torch mappings for those backends | `sub-skills/customization-and-constraints/` |
| Custom loss errors before search | Loss string has wrong signature or returns an invalid type/sign | Use two/three-argument `elementwise_loss`, full `(tree, dataset, options)` objective for `loss_function`, and `loss_scale="linear"` for negative losses | `customization-and-constraints` |
| Template model cannot export to SymPy/LaTeX/JAX/Torch | Template `combine` can contain arbitrary Julia and not all exports are supported | Inspect `model.equations_` and component `julia_expression` trees instead | `sub-skills/structured-expressions/`, `sub-skills/export-and-artifacts/` |
| Reloaded model or CSV lacks expected behavior | Pickle/checkpoint is version-sensitive or reconstruction options are missing | Keep CSV plus model-construction code; call `PySRRegressor.from_file(run_directory=...)` with matching operator/template options | `sub-skills/export-and-artifacts/` |
| Slurm job launches too many Python processes or fails to use allocation | The Python coordinator was wrapped in `srun`, or `procs` does not match allocation tasks | Run one Python script inside the allocation with `parallelism="multiprocessing", cluster_manager="slurm", procs=<total tasks>` | `sub-skills/runtime-and-scaling/` |
