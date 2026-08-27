# statsmodels package orientation

## Public import surfaces

Use these imports for most tasks:

```python
import statsmodels.api as sm
import statsmodels.formula.api as smf
import statsmodels.tsa.api as tsa
```

`statsmodels.api` exposes common cross-sectional models such as `OLS`, `WLS`, `GLS`, `GLM`, `GEE`, `Logit`, `Poisson`, `MixedLM`, `RLM`, `QuantReg`, `PCA`, `MANOVA`, datasets, graphics, stats, and utility functions such as `add_constant`. `statsmodels.formula.api` exposes formula constructors such as `ols`, `glm`, `logit`, `poisson`, `mixedlm`, and `gee`. `statsmodels.tsa.api` exposes time-series models and tests such as `ARIMA`, `SARIMAX`, `AutoReg`, `VAR`, `VECM`, `STL`, `acf`, `adfuller`, and `kpss`.

For production libraries, direct imports can reduce import cost and make dependencies explicit:

```python
from statsmodels.regression.linear_model import OLS
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.stats.diagnostic import het_breuschpagan
```

## Data terminology

- `endog`: dependent/response/outcome variable.
- `exog`: independent variables/design matrix/regressors.
- Formula strings use `patsy`/R-like syntax such as `y ~ x1 + C(group)`.
- Array/matrix workflows usually need an intercept column added with `sm.add_constant(exog)`.
- Many result objects expose `params`, `bse`, `tvalues` or `zvalues`, `pvalues`, `conf_int()`, `summary()`, `predict()`, and model-specific diagnostics.

## Installation and optional surfaces

Normal users should install a released package:

```bash
python -m pip install statsmodels
# or
conda install -c conda-forge statsmodels
```

Important optional dependencies and surfaces:

| Surface | Requirement | Guidance |
| --- | --- | --- |
| Plotting and graphics | `matplotlib` | Use a noninteractive backend such as `Agg` in headless automation. |
| Tests | `pytest` and test extras | Use focused tests for changed modules; full suite can be long. |
| Distributed estimation | `joblib` optional | Useful only for selected large-data workflows. |
| Polars compatibility | `polars` optional | Verify availability before promising it. |
| X-13/X-12 | external executable | Package import is not enough; check the binary and document unavailability. |
| Source build | compiler, Meson, Cython, NumPy/SciPy build deps | Prefer wheels for normal use; source checkouts need build tooling. |

## Scope boundaries

This skill focuses on public statistical-modeling and maintainer workflows. It does not deeply document deprecated `archive/`, generated docs output, release-key handling, or experimental `sandbox` modules. If a task is purely about generic pandas/NumPy data cleaning, use pandas/NumPy knowledge first and use statsmodels only at the model, test, or diagnostic step.
