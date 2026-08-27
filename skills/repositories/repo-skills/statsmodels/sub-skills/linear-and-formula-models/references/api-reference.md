# Linear and formula API reference

## Formula wrappers

Import formula wrappers with:

```python
import statsmodels.formula.api as smf
```

Common wrappers expose model `from_formula` methods:

| Wrapper | Use |
| --- | --- |
| `smf.ols(formula, data, ...)` | Ordinary least squares. |
| `smf.wls(formula, data, weights=...)` | Weighted least squares. |
| `smf.gls(formula, data, sigma=...)` | Generalized least squares with covariance structure. |
| `smf.glm(formula, data, family=...)` | Generalized linear models with families/links. |
| `smf.gee(formula, groups=..., data=..., cov_struct=...)` | Clustered/longitudinal GEE. |
| `smf.mixedlm(formula, data, groups=..., re_formula=..., vc_formula=...)` | Linear mixed effects models. |
| `smf.rlm(formula, data, M=...)` | Robust linear models. |
| `smf.quantreg(formula, data)` | Quantile regression. |
| `smf.glmgam(formula, data, smoother=..., alpha=...)` | Generalized additive model through GLMGam. |

Formula wrappers use patsy/formulaic-style processing. Use `C(var)` for categorical variables, `0` or `-1` to remove the intercept, and inspect design columns when categorical levels or interactions matter.

## Matrix/API classes

Import broad API with `import statsmodels.api as sm` or direct classes from modules. Verified constructor signatures include:

```python
sm.OLS(endog, exog=None, missing='none', hasconst=None, **kwargs)
sm.GLM(endog, exog, family=None, offset=None, exposure=None,
       freq_weights=None, var_weights=None, missing='none', **kwargs)
sm.Logit(endog, exog, offset=None, check_rank=True, **kwargs)
```

Linear-model families here include `OLS`, `WLS`, `GLS`, `GLSAR`, `RollingOLS`, `RollingWLS`, `RecursiveLS`, `QuantReg`, and `RLM`. GLM families are under `sm.families`, for example `Gaussian`, `Binomial`, `Poisson`, `Gamma`, `InverseGaussian`, `NegativeBinomial`, and `Tweedie` depending on installed version.

## Fit and result methods

Most workflows follow:

```python
model = sm.OLS(endog, exog, missing='raise')
result = model.fit()
print(result.summary())
params = result.params
ci = result.conf_int()
pred = result.predict(new_exog)
```

Frequently used result surfaces:

| Result surface | Meaning |
| --- | --- |
| `params` | Estimated coefficients. |
| `bse` | Standard errors for parameters. |
| `tvalues`, `zvalues` | Test statistics, model-dependent. |
| `pvalues` | Parameter-level p-values. |
| `conf_int(alpha=...)` | Confidence intervals. |
| `summary()` / `summary2()` | Presentation tables. |
| `predict(exog=...)` | Predicted mean/response; exact arguments vary by model. |
| `get_robustcov_results(cov_type=...)` | New results object with robust covariance for many linear models. |

## Robust covariance choices

Common covariance types include heteroskedasticity-consistent (`HC0`, `HC1`, `HC2`, `HC3`), clustered (`cluster` with groups), HAC/Newey-West (`HAC` with lag choices), and model-specific robust options. Always state the covariance choice and the grouping/time assumptions it implies.

## Missing data knobs

Many constructors default to `missing='none'`. Use:

- `missing='raise'` to fail fast during validation.
- `missing='drop'` to drop observations intentionally.
- formula/dataframe pre-cleaning when the missingness policy must be explicit and reproducible.
