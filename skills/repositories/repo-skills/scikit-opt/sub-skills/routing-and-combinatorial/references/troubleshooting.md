# Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Route result repeats or skips cities | The objective or validation logic is not treating the chromosome as a permutation. | Validate that the route contains every city exactly once and that the objective sums edges over the permutation order. |
| Route cost is non-finite | Distance matrix or route-cost logic is malformed. | Rebuild the distance matrix, check for NaNs/infs, and confirm the route-cost function returns one finite scalar. |
| Distance matrix errors | Matrix is not square, has the wrong size, or does not match the coordinate list. | Recreate the matrix from the same coordinate fixture used by the optimizer. |
| Fixed start/end point route looks wrong | The endpoints were included in the permutation instead of being held out of the optimizer input. | Keep the endpoints outside the route vector and wrap them inside the route-cost function. |
| Plotting examples fail in headless environments | The example needs matplotlib/pandas display support that is not part of the core route workflow. | Use the bundled headless smoke script, or install the optional presentation dependencies only when you need plots. |
| `PSO_TSP` raises `TypeError` during construction | This generated skill was verified against a package version where `PSO_TSP` calls the function transformer without `n_processes`. | Do not use `PSO_TSP` as a working route solver here; use `GA_TSP`, `SA_TSP`, `ACA_TSP`, or `IA_TSP`. |
| Route search appears noisy or unstable | These algorithms are stochastic and the default populations are tiny in smoke runs. | Increase `size_pop` or `max_iter` and compare several seeds. |

## Quick checks

- Confirm `best_y` is finite.
- Confirm `best_x` is a permutation.
- Confirm any synthetic fixture keeps the route-cost function and distance matrix synchronized.
- Prefer a tiny synthetic coordinate fixture over source CSV files so the workflow stays self-contained.
