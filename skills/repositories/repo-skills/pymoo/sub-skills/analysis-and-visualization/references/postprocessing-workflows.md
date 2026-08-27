# Postprocessing Workflows

Use these recipes after a pymoo run has produced a `Result`, an objective matrix,
or a saved population. They are designed to be self-contained and do not require
opening package examples or documentation.

## 1. Start from a completed result

```python
import numpy as np
from pymoo.util.nds.non_dominated_sorting import find_non_dominated

F = np.asarray(res.F if res.F is not None else res.opt.get("F"), dtype=float)
if F.ndim == 1:
    F = F[None, :]
assert F.ndim == 2 and np.isfinite(F).all()

nd = find_non_dominated(F)
F_nd = F[nd]
X_nd = None if res.X is None else np.asarray(res.X)[nd]
approx_ideal = F_nd.min(axis=0)
approx_nadir = F_nd.max(axis=0)
```

Keep `X_nd` aligned with `F_nd` when later selecting a row by MCDM. If the
optimization problem has constraints, use feasible rows for quality metrics when
that is the intended comparison.

## 2. Choose indicators by what reference information exists

### Known or accepted approximate Pareto front

Use distance and epsilon indicators only when `pf` is available and has the same
number of objective columns as `F`.

```python
from pymoo.indicators.gd import GD
from pymoo.indicators.gd_plus import GDPlus
from pymoo.indicators.igd import IGD
from pymoo.indicators.igd_plus import IGDPlus
from pymoo.indicators.epsilon import Epsilon

pf = np.asarray(pf, dtype=float)
assert pf.ndim == 2 and pf.shape[1] == F_nd.shape[1]

scores = {
    "gd": GD(pf).do(F_nd),
    "gd_plus": GDPlus(pf).do(F_nd),
    "igd": IGD(pf).do(F_nd),
    "igd_plus": IGDPlus(pf).do(F_nd),
    "epsilon": Epsilon(pf).do(F_nd),
}
```

If objectives have very different scales, use `zero_to_one=True` with a Pareto
front or explicit `ideal`/`nadir` so all compared matrices are normalized in the
same way.

### Pareto front unknown

Do not invent `pf` for IGD/GD. Prefer hypervolume with a defensible reference
point, convergence curves, or a front approximation clearly labeled as an
approximation.

```python
from pymoo.indicators.hv import HV

# For minimization, the reference point must be worse than the front in every
# objective. This conservative observed-front reference point adds a 10% margin.
span = np.maximum(approx_nadir - approx_ideal, 1e-12)
ref_point = approx_nadir + 0.10 * span
hv = HV(ref_point=ref_point).do(F_nd)
```

If you normalize objective values yourself to `[0, 1]`, use a normalized
reference point too:

```python
from pymoo.indicators.hv import HV

nF = (F_nd - approx_ideal) / np.maximum(approx_nadir - approx_ideal, 1e-12)
hv_norm = HV(ref_point=np.ones(F_nd.shape[1]) * 1.1).do(nF)
```

For high-dimensional exact hypervolume cost, switch to the approximate helper:

```python
from pymoo.indicators.hv.approximate import ApproximateHypervolume

approx_hv = ApproximateHypervolume(ref_point, n_samples=10000, seed=1).add(F_nd)
print(approx_hv.hv, approx_hv.hvc)  # total HV and contributions
```

## 3. Convergence from `save_history=True`

A run must be executed with `save_history=True` before `res.history` exists.
History stores deep copies of algorithm state at each generation, so avoid it
for very large populations, thousands of generations, or objects holding large
external data unless the post-hoc analysis is worth the memory.

```python
import numpy as np
from pymoo.indicators.hv import HV

hist = res.history
n_evals = np.array([algo.evaluator.n_eval for algo in hist])
hist_F = []
for algo in hist:
    opt = algo.opt
    F_gen = opt.get("F")
    feasible = opt.get("feasible")
    if feasible is not None and feasible.any():
        F_gen = F_gen[np.where(feasible)[0]]
    hist_F.append(F_gen)

metric = HV(ref_point=ref_point)
hv_curve = np.array([metric.do(F_gen) for F_gen in hist_F if len(F_gen) > 0])
```

For fixed-target/anytime assessment, let pymoo build best-so-far curves:

```python
from pymoo.indicators.anytime import attainment_curve, first_hitting_time
from pymoo.indicators.igd import IGD

igd_metric = IGD(pf)
n_evals, best_igd = attainment_curve(res.history, igd_metric, mode="min", stride=1)
first_hit = first_hitting_time(n_evals, best_igd, target=0.01, mode="min")
```

If memory is the concern, record only the needed values with a callback during
the run instead of storing full history snapshots. Running the optimization and
choosing callback placement belongs to the optimization workflow sub-skill; this
sub-skill owns how to score and plot the collected arrays.

## 4. MCDM: choose one or a few solutions from a front

Always decide whether preference methods should operate on raw objectives or a
normalized objective matrix. For mixed units, normalization is usually required.

```python
import numpy as np
from pymoo.decomposition.asf import ASF
from pymoo.mcdm.pseudo_weights import PseudoWeights
from pymoo.mcdm.high_tradeoff import HighTradeoffPoints

ideal = F_nd.min(axis=0)
nadir = F_nd.max(axis=0)
denom = np.maximum(nadir - ideal, 1e-12)
nF = (F_nd - ideal) / denom

weights = np.array([0.2, 0.8])
weights = weights / weights.sum()

# Compromise-programming route through ASF. For ASF's divide-by-weight
# formulation, invert positive preference weights.
i_asf = ASF().do(nF, 1.0 / np.maximum(weights, 1e-12)).argmin()

# Pseudo-weight location matching on the observed front.
i_pw, pseudo = PseudoWeights(weights).do(nF, return_pseudo_weights=True)

# Knee/high-tradeoff outliers; may return None when no strong outlier exists.
knee_idx = HighTradeoffPoints().do(nF)

selected = {
    "asf": int(i_asf),
    "pseudo_weights": int(i_pw),
    "high_tradeoff": None if knee_idx is None else knee_idx.tolist(),
}
```

Report selected rows on the original scale:

```python
print("ASF selected row", i_asf, "F=", F_nd[i_asf], "X=", None if X_nd is None else X_nd[i_asf])
```

Pseudo weights describe the location of a solution on the observed objective
front. They are not the same as optimizing a weighted sum on non-convex Pareto
fronts.

## 5. Decomposition for ranking or scalar problem conversion

Decomposition can rank a matrix directly:

```python
import numpy as np
from pymoo.decomposition.weighted_sum import WeightedSum
from pymoo.decomposition.tchebicheff import Tchebicheff
from pymoo.decomposition.pbi import PBI

weights = np.array([0.5, 0.5])
rank_ws = WeightedSum().do(nF, weights).argsort()
rank_tch = Tchebicheff().do(nF, weights).argsort()
rank_pbi = PBI(theta=5).do(nF, weights).argsort()
```

The same decomposition can scalarize a multi-objective problem before running a
single-objective optimizer:

```python
from pymoo.problems.util import decompose
from pymoo.decomposition.asf import ASF

scalar_problem = decompose(problem, ASF(), weights)
```

Use the optimization workflow sub-skill for the actual optimizer choice,
termination, and result interpretation after conversion.

## 6. Reference directions for many-objective analysis

Reference directions are rows on the unit simplex. Use them for many-objective
algorithms, Pareto-front generation for built-in many-objective test problems,
and visual/contextual comparisons.

```python
import numpy as np
from pymoo.util.ref_dirs import get_reference_directions

ref_dirs = get_reference_directions("uniform", 3, n_partitions=12)
assert ref_dirs.shape[1] == 3
assert np.allclose(ref_dirs.sum(axis=1), 1.0)
assert np.all(ref_dirs >= -1e-12)

# If an exact Das-Dennis point count is not achievable, use energy or reduction.
ref_dirs_any_count = get_reference_directions("energy", 3, 50, seed=1)
```

Layered directions can bias points toward the center:

```python
outer = get_reference_directions("das-dennis", 3, n_partitions=8, scaling=1.0)
inner = get_reference_directions("das-dennis", 3, n_partitions=4, scaling=0.5)
ref_dirs = get_reference_directions("multi-layer", outer, inner)
```

## 7. Headless static plotting

Set the backend before importing pymoo visualization modules or `pyplot`.

```python
import matplotlib
matplotlib.use("Agg")

from pymoo.visualization.scatter import Scatter
from pymoo.visualization.pcp import PCP
from pymoo.visualization.heatmap import Heatmap

Scatter(title="Objective space", legend=True).add(F_nd, label="solutions").save("objective_space.png", dpi=150)
PCP(title="Parallel coordinates").add(F_nd).save("pcp.png", dpi=150)
Heatmap(bounds=[0, 1]).add(nF).save("heatmap.png", dpi=150)
```

Use `Scatter` for 2-D/3-D objective spaces, `PCP` for many objectives or design
variables, `Radviz`/`StarCoordinate` for 2-D projections of many objectives,
`Radar`/`Petal` for selected-solution profiles, and `Heatmap` for a
solution-by-objective matrix.

The bundled [indicator script](../scripts/check_indicators.py) provides a quick
numeric smoke check. The bundled [scatter script](../scripts/save_scatter_plot.py)
shows the safe `Agg` save pattern.

## 8. Optional animation/video

Static plots require only Matplotlib. Video recording uses `pyrecorder` and can
also require a working video writer or display streamer. Keep optional video as
a best-effort add-on:

```python
# Optional dependency path; guard this import in reusable scripts.
from pyrecorder.recorder import Recorder
from pyrecorder.writers.video import Video
from pymoo.visualization.scatter import Scatter

with Recorder(Video("optimization.mp4")) as rec:
    for entry in res.history:
        Scatter(title=f"Gen {entry.n_gen}").add(entry.pop.get("F")).do()
        rec.record()
```

If `pyrecorder` or a video writer is unavailable, save per-generation PNG files
or a final static summary instead.
