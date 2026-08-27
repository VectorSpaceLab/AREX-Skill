# Troubleshooting

## Install and import

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `ModuleNotFoundError: No module named 'sko'` | The package is not installed in the current environment. | Install `scikit-opt` and re-run the import check from the target environment. |
| Editable install fails while building metadata | `setup.py` imports `sko`, which imports NumPy/SciPy during build metadata generation. | Use `pip install --no-build-isolation -e .` from a local checkout, or install the published package instead. |
| `pip check` passes but import still fails | The wrong Python interpreter is active or the install happened in a different environment. | Run the import with the environment Python, not a shell activation guess. |
| Missing `matplotlib`, `pandas`, `joblib`, or `torch` | Optional example/acceleration dependency is absent. | Install only the extra needed for that workflow, or switch to the core CPU workflow. |

## Version-specific caveats

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `PSO_TSP` raises `TypeError: func_transformer() missing 1 required positional argument: 'n_processes'` | Verified package version `0.6.6` has a broken `PSO_TSP` construction path. | Use `GA_TSP`, `SA_TSP`, `ACA_TSP`, or `IA_TSP` instead of claiming `PSO_TSP` works. |
| A task expects GPU acceleration but the installed run is CPU-only | `GA.to(device)` is optional and experimental; no GPU wheel or device is active. | Treat the GPU path as optional, or install/verify PyTorch/CUDA only when the task explicitly needs it. |

## Runtime shape errors

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `best_y` is array-like or non-finite | The objective returned the wrong shape or a non-finite value. | Return one finite scalar per candidate, or route to the objective-speedup sub-skill if you need vectorization. |
| Stochastic results vary too much | The run is too small for the problem. | Increase population or iteration counts and compare several seeds. |

## Where to go next

- For GA-size or precision issues, go to `genetic-algorithms`.
- For DE/PSO/SA/AFSA algorithm-specific failures, go to `continuous-optimizers`.
- For route/permutation issues, go to `routing-and-combinatorial`.
- For objective run modes, caching, and optional acceleration, go to `objective-functions-and-speedups`.
