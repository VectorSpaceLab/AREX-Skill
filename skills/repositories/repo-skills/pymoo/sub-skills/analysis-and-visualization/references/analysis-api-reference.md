# Analysis API Reference

This reference covers postprocessing APIs for pymoo result matrices. It assumes
all objectives are minimized, matching pymoo's optimization convention.

## Shape and normalization conventions

| Name | Expected shape | Meaning | Common checks |
| --- | --- | --- | --- |
| `F` | `(n_points, n_obj)` | Objective values for candidate solutions, usually `res.F`, `res.opt.get("F")`, or `algorithm.pop.get("F")`. | Finite float values; lower is better in every column. A 1-D row is often accepted but a 2-D matrix is clearer. |
| `X` | `(n_points, n_var)` | Decision variables for solution rows. | Keep row order aligned with `F` when selecting MCDM indices. |
| `pf` | `(n_pf, n_obj)` | True or accepted approximate Pareto front in objective space. | Same column count as `F`; required by distance and epsilon indicators. |
| `ref_point` | `(n_obj,)` | Hypervolume point dominated by, and worse than, the relevant solution/Pareto region. | Must be larger than the relevant minimization objective values after any normalization convention is applied. |
| `ideal`, `nadir` | `(n_obj,)` each | Lower and upper objective-space bounds for zero-to-one normalization. | Require `nadir > ideal` per objective; use observed min/max only as an approximation. |

For scaled or mixed-unit objectives, normalize before ranking or computing
preference distances. If using an indicator with `zero_to_one=True`, provide a
consistent Pareto front or explicit `ideal` and `nadir`.

## Pareto-front and non-dominated-set helpers

Known test or custom problems may provide:

```python
pf = problem.pareto_front()
ps = problem.pareto_set()
```

For a result matrix whose true front is unknown, filter the non-dominated rows:

```python
from pymoo.util.nds.non_dominated_sorting import NonDominatedSorting, find_non_dominated

front_indices = NonDominatedSorting().do(F, only_non_dominated_front=True)
F_nd = F[front_indices]
# Equivalent index helper for just the non-dominated set:
front_indices = find_non_dominated(F)
```

`NonDominatedSorting(epsilon=None, method="fast_non_dominated_sort")` supports
`do(F, return_rank=False, only_non_dominated_front=False, n_stop_if_ranked=None,
n_fronts=None, **kwargs)`. With `return_rank=True`, it returns `(fronts, ranks)`.

## Performance indicators

All indicator objects are callable and also expose `.do(F)`. Lower is better for
all distance/epsilon/KKTPM/R-IGD metrics; hypervolume (`HV`) is better when
larger.

| Capability | Import and minimal signature | Requires | Notes |
| --- | --- | --- | --- |
| Hypervolume | `from pymoo.indicators.hv import HV, Hypervolume`; `HV(ref_point=None, pf=None, nds=True, norm_ref_point=True, ideal=None, nadir=None, **kwargs)` | Explicit `ref_point`, or a `pf` from which a reference point can be derived. | Prefer an explicit `ref_point`. If `zero_to_one=True` and `ref_point` is already normalized, set `norm_ref_point=False`; otherwise let pymoo normalize it consistently with `ideal`/`nadir` or `pf`. Exact HV can be costly as objectives increase. |
| Approximate HV | `from pymoo.indicators.hv.approximate import ApproximateHypervolume`; `ApproximateHypervolume(ref_point, n_samples=10000, method="Rphi-FWE+", seed=None)` | `ref_point` | Supports `.add(F)`, `.delete(k)`, and reads `.hv`/`.hvc`; useful for higher-dimensional or incremental HV estimates. |
| Generational distance | `from pymoo.indicators.gd import GD`; `GD(pf, **kwargs)` | Pareto front `pf` | Average distance from each solution in `F` to the nearest front point. |
| Generational distance plus | `from pymoo.indicators.gd_plus import GDPlus`; `GDPlus(pf, **kwargs)` | Pareto front `pf` | Uses weakly Pareto-compliant modified distance for minimization. |
| Inverted GD | `from pymoo.indicators.igd import IGD`; `IGD(pf, **kwargs)` | Pareto front `pf` | Average distance from each front point to the nearest solution in `F`. |
| Inverted GD plus | `from pymoo.indicators.igd_plus import IGDPlus`; `IGDPlus(pf, **kwargs)` | Pareto front `pf` | Weakly Pareto-compliant IGD variant. |
| Additive epsilon | `from pymoo.indicators.epsilon import Epsilon`; `Epsilon(pf, **kwargs)` | Pareto front `pf` | Compares `F` against reference front. Lower is better; zero means matching under the additive convention. |
| Multiplicative epsilon | `from pymoo.indicators.epsilon import EpsilonMultiplicative`; `EpsilonMultiplicative(pf, **kwargs)` | Positive-valued front and results | Avoid zeros or negative values; shift or use additive epsilon if the multiplicative ratio is not meaningful. |
| KKTPM | `from pymoo.indicators.kktpm import KKTPM`; `KKTPM().calc(X, problem, ideal=None, utopian_eps=1e-4, rho=1e-3)` | Decision matrix `X`; problem that evaluates `F`, `G`, `dF`, and `dG`; suitable ideal point | Does not require a Pareto front, but it does require derivatives. Wrap differentiable problems with automatic differentiation and include derivative values in the evaluator if scoring a stored run. |
| R-metric | `from pymoo.indicators.rmetric import RMetric`; `RMetric(problem, ref_points, w=None, delta=0.2, pf=None).do(F, others=None, calc_hv=True)` | Problem or explicit `pf`; region-of-interest reference points | Returns `(rigd, rhv)` when `calc_hv=True`; set `calc_hv=False` to return only R-IGD or avoid unsupported/high-dimensional HV. |

## Anytime indicators and convergence helpers

```python
from pymoo.indicators.anytime import (
    AnytimeCallback, attainment_curve, first_hitting_time, ert, data_profile,
)
```

- `attainment_curve(history, indicator, mode="min", stride=1)` scores a
  `res.history` list and returns `(n_evals, values)` best-so-far arrays.
- `AnytimeCallback(indicator, mode="min", stride=1)` records the same style of
  curve during a run without deep-copying every algorithm state.
- `first_hitting_time(n_evals, values, target, mode="min")`, `ert(runtimes,
  budget)`, and `data_profile(curves, targets, budgets, mode="min")` summarize
  target-reaching behavior.

Use `mode="max"` for hypervolume and `mode="min"` for distance or epsilon
metrics.

## Reference directions

```python
from pymoo.util.ref_dirs import get_reference_directions
ref_dirs = get_reference_directions(name, *args, **kwargs)
```

The result is a matrix shaped `(n_dirs, n_obj)` on the unit simplex, so rows
should sum to one and entries should be non-negative up to numeric tolerance.

| Name | Typical call | Best fit | Common pitfall |
| --- | --- | --- | --- |
| `"uniform"` / `"das-dennis"` | `get_reference_directions("uniform", n_obj, n_partitions=12)` or an exactly achievable `n_points` | Structured simplex lattice for NSGA-III/MOEA/D-style workflows. | Not every requested `n_points` is achievable; use `n_partitions` or switch to `energy`/`reduction`. |
| `"energy"` | `get_reference_directions("energy", n_obj, n_points, seed=1)` | Well-spaced directions for arbitrary counts. | More expensive than a lattice; use small counts for quick checks. |
| `"multi-layer"` | `get_reference_directions("multi-layer", layer_a, layer_b, ...)` | Combine scaled direction arrays/layers. | Pass arrays generated by other factories; duplicate directions are removed. |
| `"layer-energy"` | `get_reference_directions("layer-energy", n_obj, [p1, p2, ...])` | Automatically optimize scaling for multiple lattice layers. | Partitions define layers, not final `n_points` directly. |
| `"reduction"` | `get_reference_directions("reduction", n_obj, n_points)` | Approximate arbitrary target count through sampling/reduction. | Tune sample counts only when needed; defaults are usually enough for routing. |
| `"incremental"` | `get_reference_directions("incremental", n_obj, n_partitions=8)` or achievable `n_points` | Incremental lattice construction. | Like Das-Dennis, requested `n_points` may be rejected if no exact lattice exists. |

## Decomposition and multi-to-single conversion

Decomposition objects expose `do(F, weights, _type="auto", ideal_point=None,
utopian_point=None, nadir_point=None, **kwargs)` and are callable.

| Method | Import | Constructor | Use |
| --- | --- | --- | --- |
| Weighted sum | `from pymoo.decomposition.weighted_sum import WeightedSum` | `WeightedSum(eps=0.0, _type="auto", **kwargs)` | Linear scalarization; simple but can miss non-convex regions. |
| ASF | `from pymoo.decomposition.asf import ASF` | `ASF(eps=0.0, _type="auto", **kwargs)` | Achievement scalarization; common for compromise programming. For preference weights, pass inverse weights when using the divide-by-weight formulation. |
| AASF | `from pymoo.decomposition.aasf import AASF` | `AASF(eps=1e-10, _type="auto", rho=None, beta=None, **kwargs)` | Augmented ASF. In this version, pass either `rho` or `beta`. |
| Tchebicheff | `from pymoo.decomposition.tchebicheff import Tchebicheff` | `Tchebicheff(eps=0.0, _type="auto", **kwargs)` | Minimize maximum weighted deviation from a utopian point. Note the class/module spelling is `Tchebicheff`. |
| PBI | `from pymoo.decomposition.pbi import PBI` | `PBI(theta=5, **kwargs)` | Penalty boundary intersection; balances distance along and away from a weight direction. |

Automatic `_type` routes:

- one `F` row with many weight rows -> one-to-many vector;
- many `F` rows with one weight row -> many-to-one vector;
- matching counts of `F` and weights -> one-to-one vector;
- many rows against many weights -> matrix `(n_points, n_weights)`.

To convert a multi-objective problem to a scalar problem before optimization:

```python
from pymoo.problems.util import decompose
scalar_problem = decompose(problem, ASF(), weights)
```

The conversion itself belongs here; executing and tuning the resulting optimizer
belongs to the optimization workflow sub-skill.

## MCDM selection helpers

| Method | Import and signature | Output | Guidance |
| --- | --- | --- | --- |
| Pseudo weights | `from pymoo.mcdm.pseudo_weights import PseudoWeights`; `PseudoWeights(weights, **kwargs).do(F, return_pseudo_weights=False)` | Selected row index, or `(index, pseudo_weights)` | Weights must match the number of objectives. Use consistent `ideal`/`nadir` or normalize first. Pseudo weights describe location on the observed front and are not equivalent to a weighted-sum optimum on non-convex fronts. |
| High-tradeoff/knee | `from pymoo.mcdm.high_tradeoff import HighTradeoffPoints`; `HighTradeoffPoints(epsilon=0.125, **kwargs).do(F)` | Indices of outlier high-tradeoff points, or `None` | Normalize objective scales first; no knee may be returned for smooth or tiny sets. |
| Compromise programming | Reliable route: normalize `F`, then minimize a decomposition value such as `ASF().do(nF, 1 / weights)`. | Selected row index from `.argmin()` | The explicit decomposition route is preferable in this version. The `CompromiseProgramming` class exists, but verify its behavior before relying on it as a selector. |

## Visualization helpers

All these classes wrap Matplotlib. They share `add(F, **kwargs)`, `do()`,
`save(fname, **kwargs)`, `show(**kwargs)`, `apply(func)`, `get_figure()`,
`get_axes()`, `reset()`, and `set_axis_style(**kwargs)` through the base plot
class.

| Visualization | Import and constructor | Best fit |
| --- | --- | --- |
| Scatter | `from pymoo.visualization.scatter import Scatter`; `Scatter(plot_3d=True, angle=(45, 45), **kwargs)` | 1-D/2-D/3-D objective clouds; pairwise grid when higher-dimensional and `plot_3d=False`. |
| PCP | `from pymoo.visualization.pcp import PCP`; `PCP(bounds=None, show_bounds=True, n_ticks=5, normalize_each_axis=True, bbox=False, **kwargs)` | Parallel-coordinate view for many objectives or decision variables. |
| Radviz | `from pymoo.visualization.radviz import Radviz`; `Radviz(endpoint_style=None, **kwargs)` | Nonlinear 2-D projection of higher-dimensional objective sets. |
| Radar | `from pymoo.visualization.radar import Radar`; `Radar(normalize_each_objective=True, n_partitions=3, point_style=None, **kwargs)` | Compare a few solutions across objectives with ideal/nadir bounds. |
| Star coordinate | `from pymoo.visualization.star_coordinate import StarCoordinate`; `StarCoordinate(axis_extension=1.03, **kwargs)` | Higher-dimensional projection where points may lie outside the circle. |
| Heatmap | `from pymoo.visualization.heatmap import Heatmap`; `Heatmap(cmap="Blues", order_by_objectives=False, reverse=True, solution_labels=True, **kwargs)` | Matrix view of solution-by-objective values. |
| Petal | `from pymoo.visualization.petal import Petal`; `Petal(bounds=None, **kwargs)` | Trade-off profile for one or several selected solutions. |

Headless static pattern:

```python
import matplotlib
matplotlib.use("Agg")        # set before importing pymoo visualization modules
from pymoo.visualization.scatter import Scatter

plot = Scatter(title="Objective space", legend=True)
plot.add(F, label="solutions")
plot.save("objective_space.png", dpi=150)
```

Optional video/animation recording uses `pyrecorder`; treat it as an optional
dependency and keep static `.save(...)` plots as the base path.
