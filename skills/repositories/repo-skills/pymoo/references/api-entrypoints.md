# pymoo API Entrypoints

This repo skill uses public pymoo APIs and avoids depending on any original
checkout files. Install the public package with `python -m pip install -U pymoo`
and then choose a sub-skill by workflow.

## Package and dependency notes

- Package/import name: `pymoo`.
- Version baseline for this skill: `0.6.2`.
- Python requirement in the package metadata: Python `>=3.10`.
- Base dependencies include NumPy, SciPy, moocore, autograd, cma, matplotlib,
  alive-progress, and Deprecated.
- Optional extras are task-specific: `parallelization` for joblib/dask/ray,
  `others` for integrations such as Optuna/COMO-CMA-ES, `visualization` for
  recorder/video helpers, and `full` for a broad optional install.

Do not install optional extras unless the user's workflow needs them. Base
optimization, custom problems, indicators, static plotting, and many algorithm
workflows run without the broad extras.

## Core execution imports

```python
from pymoo.optimize import minimize
from pymoo.termination import get_termination
from pymoo.problems import get_problem
```

Representative algorithms:

```python
from pymoo.algorithms.moo.nsga2 import NSGA2
from pymoo.algorithms.moo.nsga3 import NSGA3
from pymoo.algorithms.moo.moead import MOEAD
from pymoo.algorithms.soo.nonconvex.ga import GA
from pymoo.algorithms.soo.nonconvex.de import DE
from pymoo.algorithms.soo.nonconvex.pso import PSO
```

Read `sub-skills/optimization-workflows/` for algorithm selection, termination,
callbacks, ask-and-tell, and `Result` fields.

## Problem modeling imports

```python
from pymoo.core.problem import Problem, ElementwiseProblem
from pymoo.problems.functional import FunctionalProblem
```

Use `Problem` for vectorized matrix evaluation, `ElementwiseProblem` for one
candidate at a time, and `FunctionalProblem` for compact formulas. Inequality
constraints are feasible when `G <= 0`; equality residuals go in `H`. Read
`sub-skills/problem-modeling/` for shapes, bounds, and validation.

## Variables and operators

```python
from pymoo.core.variable import Real, Integer, Binary, Choice
from pymoo.core.mixed import MixedVariableGA
from pymoo.operators.crossover.sbx import SBX
from pymoo.operators.mutation.pm import PM
from pymoo.operators.repair.rounding import RoundingRepair
```

Use `sub-skills/operators-and-variables/` for mixed variables, custom sampling,
crossover/mutation/repair, duplicate elimination, initial populations, and
operator shape contracts.

## Performance and backend imports

```python
from pymoo.functions import is_compiled
from pymoo.parallelization.starmap import StarmapParallelization
```

Base pymoo can use vectorized NumPy evaluation and stdlib starmap runners.
Optional `joblib`, `dask`, and `ray` runners require optional dependencies.
GPU acceleration is a user-supplied vectorized objective pattern, not a base
pymoo backend guarantee. Read `sub-skills/performance-and-parallelization/`.

## Analysis and visualization imports

```python
from pymoo.indicators.hv import HV
from pymoo.indicators.gd import GD
from pymoo.indicators.igd import IGD
from pymoo.util.ref_dirs import get_reference_directions
from pymoo.decomposition.asf import ASF
from pymoo.mcdm.pseudo_weights import PseudoWeights
from pymoo.visualization.scatter import Scatter
```

Read `sub-skills/analysis-and-visualization/` for indicator requirements,
reference directions, decomposition, MCDM row selection, convergence/history,
and headless plotting.

## First diagnostic commands

```bash
python - <<'PY'
import pymoo
from pymoo.functions import is_compiled
print("pymoo", getattr(pymoo, "__version__", "unknown"))
print("compiled", is_compiled())
PY
```

Then run the root smoke script or a targeted sub-skill script before debugging
larger workflows.
