# Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `AssertionError: size_pop must be even integer` | `GA`, `EGA`, and `GA_TSP` pair individuals during crossover. | Use an even population size. |
| `best_y` has an unexpected shape or dtype | The objective returned an array-like object instead of a scalar per candidate. | Make the objective return one scalar value for each `x`. If you need vectorized evaluation, route to `objective-functions-and-speedups`. |
| Discrete variables land on surprising values | `precision`, `lb`, and `ub` do not line up with the intended grid, or integer precision triggered bound extension. | Make the bound/precision lengths match `n_dim`, and confirm whether integer precision is extending the upper bound internally. |
| Feasible points still look heavily penalized | Equality and inequality violations are added through a fixed `1e5` penalty term. | Tighten bounds, repair candidates, or simplify the constraint set. |
| Custom operator never seems to run | Wrong `operator_name`, wrong function signature, or the function does not return the updated field. | Register the exact slot name, accept `self` as the first argument, and return `self.Chrom` or `self.FitV` as appropriate. |
| Optimization appears to stall or fluctuate | GA-family search is stochastic; tiny runs can get stuck in local minima. | Increase `size_pop` or `max_iter`, adjust `prob_mut` or `prob_cros`, or compare multiple seeded runs. |
| Repeated `run()` calls do not reset the search | This is expected; continuation keeps the same population and appends to history. | Create a new instance if you want a fresh restart. |
| You need `GA.to(device)` or run-mode acceleration | That path belongs to objective evaluation and optional PyTorch support, not to this GA sub-skill. | Route to `objective-functions-and-speedups` for the device or run-mode guide. |
| Route/TSP operators feel incompatible with a binary GA objective | Route operators are permutation-specific. | Hand the problem off to `routing-and-combinatorial` or switch to the proper permutation workflow. |

## Quick sanity checks

- Verify `best_x` and `best_y` are finite.
- Verify the history lists have the expected length after repeated `run(max_iter)` calls.
- Verify any custom operator preserves population shape.
