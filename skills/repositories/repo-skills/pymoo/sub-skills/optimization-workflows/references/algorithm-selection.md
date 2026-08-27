# Algorithm Selection Guide

pymoo exposes a broad algorithm portfolio. Choose by objective count, variable
space, constraints, preference/reference directions, and the budget you can
spend on objective evaluations. Start with a simple, well-supported algorithm and
only add specialized operators or optional dependencies after a small smoke run.

## Quick decision table

| Task shape | Good first choices | Import examples | Watch-outs |
| --- | --- | --- | --- |
| Single-objective continuous/global search | `GA`, `DE`, `PSO`, `CMAES`, `ES`, `SRES`/`ISRES` for constraints | `pymoo.algorithms.soo.nonconvex.ga.GA`, `...de.DE`, `...pso.PSO`, `...cmaes.CMAES` | CMA-ES uses its own strategy/options; equality constraints usually need repair or reformulation. |
| Single-objective local/direct search | `NelderMead`, `PatternSearch`, `DIRECT`, `RandomSearch` baseline | `pymoo.algorithms.soo.nonconvex.nelder.NelderMead`, `...pattern.PatternSearch`, `...direct.DIRECT` | Local/direct methods can require careful bounds and initialization. |
| Two-objective default | `NSGA2`, `SPEA2`, `SMSEMOA`, `GDE3`, `NSDE` | `pymoo.algorithms.moo.nsga2.NSGA2`, `...spea2.SPEA2`, `...sms.SMSEMOA`, `...gde3.GDE3` | Use adequate population/generation budget; hypervolume-based survival can be expensive. |
| Many-objective or reference-vector tasks | `NSGA3`, `UNSGA3`, `RNSGA3`, `MOEAD`, `RVEA`, `CTAEA`, `AGEMOEA`, `AGEMOEA2` | `pymoo.algorithms.moo.nsga3.NSGA3`, `...moead.MOEAD`, `...rvea.RVEA` | Many require reference directions; generate them with the analysis sub-skill. |
| Preference-guided search | `RNSGA2`, `RNSGA3`, `PINSGA2`, reference-point variants | `pymoo.algorithms.moo.rnsga2.RNSGA2`, `...rnsga3.RNSGA3`, `...pinsga2.PINSGA2` | Ensure reference/aspiration points use the same objective scaling/minimization convention as `F`. |
| Dynamic multi-objective problems | `DNSGA2`, `KGB`, dynamic problem classes | `pymoo.algorithms.moo.dnsga2.DNSGA2`, `...kgb.KGB` | Requires change handling and careful evaluation budget; not a default for static problems. |
| Mixed/discrete/permutation spaces | `MixedVariableGA` or standard algorithms with matching operators | `pymoo.core.mixed.MixedVariableGA` | Route to `operators-and-variables` for variables, sampling/crossover/mutation/repair. |
| Decomposition-based scalarization | `MOEAD` or decompose multi-objective problem then run SOO algorithm | `pymoo.algorithms.moo.moead.MOEAD`; `pymoo.problems.util.decompose` | Weights/reference directions drive behavior; route postprocessing to analysis. |

## Representative import map

Single-objective:

```python
from pymoo.algorithms.soo.nonconvex.ga import GA
from pymoo.algorithms.soo.nonconvex.de import DE
from pymoo.algorithms.soo.nonconvex.pso import PSO
from pymoo.algorithms.soo.nonconvex.cmaes import CMAES
from pymoo.algorithms.soo.nonconvex.nelder import NelderMead
from pymoo.algorithms.soo.nonconvex.pattern import PatternSearch
from pymoo.algorithms.soo.nonconvex.sres import SRES
from pymoo.algorithms.soo.nonconvex.isres import ISRES
```

Multi-/many-objective:

```python
from pymoo.algorithms.moo.nsga2 import NSGA2
from pymoo.algorithms.moo.spea2 import SPEA2
from pymoo.algorithms.moo.sms import SMSEMOA
from pymoo.algorithms.moo.gde3 import GDE3
from pymoo.algorithms.moo.nsga3 import NSGA3
from pymoo.algorithms.moo.unsga3 import UNSGA3
from pymoo.algorithms.moo.rnsga3 import RNSGA3
from pymoo.algorithms.moo.moead import MOEAD
from pymoo.algorithms.moo.rvea import RVEA
from pymoo.algorithms.moo.ctaea import CTAEA
from pymoo.algorithms.moo.age import AGEMOEA
from pymoo.algorithms.moo.age2 import AGEMOEA2
```

Dynamic/preference routes:

```python
from pymoo.algorithms.moo.rnsga2 import RNSGA2
from pymoo.algorithms.moo.pinsga2 import PINSGA2
from pymoo.algorithms.moo.dnsga2 import DNSGA2
from pymoo.algorithms.moo.kgb import KGB
```

## Selection heuristics

- **Unknown two-objective continuous problem**: start with `NSGA2(pop_size=40 or
  100)` and a small `("n_gen", ...)` smoke. Add custom operators only after
  confirming problem shape and constraints.
- **More than three objectives**: generate reference directions and use
  `NSGA3`, `UNSGA3`, `MOEAD`, or `RVEA`. If no obvious reference-direction count
  exists, start small and inspect diversity before scaling.
- **Constrained single-objective problem**: consider `GA`/`DE` with repair or
  constraint-aware strategies; `SRES` and `ISRES` are explicitly constrained
  evolutionary strategies.
- **Expensive objective**: choose a smaller population/generation budget first
  and route to performance guidance for vectorization or elementwise runners.
- **Discrete or mixed variables**: use variable-aware operators. A float-coded
  algorithm without rounding/repair can silently produce invalid integer or
  choice values.
- **Preference/region of interest**: choose algorithms accepting reference or
  aspiration points, then normalize objective scales and document the preference
  point convention.
- **Need a scalar final decision from a Pareto set**: do not force the optimizer
  to select one row prematurely; run a multi-objective method, then route to
  MCDM/analysis for final row selection.

## Hyperparameter comparison pattern

When comparing algorithms or hyperparameters:

1. Fix problem definition, random seeds, and evaluation budgets.
2. Record algorithm constructor parameters and termination.
3. Compare objective-space quality with the same metric and reference point/front.
4. Run multiple seeds for stochastic conclusions; one seed is only a smoke.
5. Keep `verbose=False` and avoid expensive callbacks while timing.

pymoo also exposes hyperparameter helpers (`get_params`, `flatten`,
`hierarchical`, `set_params`, `HyperparameterProblem`). Operator-level and
optional `optuna` details live in `operators-and-variables`; do not install
optional optimization extras unless the task explicitly needs them.
