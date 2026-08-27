# Linear and formula workflows

## Formula OLS with categorical data

```python
import pandas as pd
import statsmodels.formula.api as smf

df = pd.DataFrame({
    "y": [1.0, 2.0, 2.8, 4.2, 4.9, 6.1],
    "x": [0, 1, 2, 3, 4, 5],
    "group": ["a", "a", "b", "b", "a", "b"],
})
res = smf.ols("y ~ x + C(group)", data=df, missing="raise").fit()
print(res.params)
print(res.summary())
```

Use formulas when column names, transformations, interactions, or categorical terms are central. Inspect `res.model.exog_names` before constructing prediction inputs.

## Matrix OLS/GLM

```python
import numpy as np
import statsmodels.api as sm

endog = np.asarray([1.0, 2.0, 2.8, 4.2, 4.9, 6.1])
exog = sm.add_constant(np.arange(endog.size))
ols = sm.OLS(endog, exog, missing="raise").fit()
glm = sm.GLM(endog, exog, family=sm.families.Gaussian()).fit()
```

Matrix APIs are better for production code and already-engineered design matrices. Add a constant explicitly unless the model's documentation says otherwise.

## Prediction with new data

For formula models, use a DataFrame with the original variable names and compatible categorical levels:

```python
new = pd.DataFrame({"x": [2.5, 6.0], "group": ["a", "b"]})
pred = res.get_prediction(new).summary_frame()
```

For matrix models, build `exog` with the same columns and intercept convention:

```python
new_x = sm.add_constant([2.5, 6.0], has_constant="add")
pred = ols.get_prediction(new_x).summary_frame()
```

## Robust covariance

```python
base = smf.ols("y ~ x + C(group)", data=df).fit()
hc3 = base.get_robustcov_results(cov_type="HC3")
clustered = base.get_robustcov_results(cov_type="cluster", groups=df["group"])
```

Report the covariance estimator and why it fits the design. Clustered covariance needs enough clusters to be meaningful.

## MixedLM and repeated measures

Use `MixedLM` when observations are grouped and the task needs random intercepts/slopes:

```python
res = smf.mixedlm("y ~ x", data=df, groups=df["group"]).fit()
```

Mixed models are sensitive to small group counts, starting values, and singular random-effect covariance estimates. If a variance component is estimated near zero, consider whether a simpler fixed-effect model is more appropriate.

## GLM families

```python
poisson_like = smf.glm("count ~ x + C(group)", data=df, family=sm.families.Poisson()).fit()
logistic_glm = smf.glm("success ~ x", data=df, family=sm.families.Binomial()).fit()
```

Use the discrete/count sub-skill when the user needs Logit/Probit classes, count-model-specific overdispersion, zero inflation, hurdle models, or marginal effects.
