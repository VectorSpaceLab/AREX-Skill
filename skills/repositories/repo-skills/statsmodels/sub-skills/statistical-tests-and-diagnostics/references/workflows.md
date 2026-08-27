# Statistical tests and diagnostics workflows

## Residual diagnostics after OLS

```python
import statsmodels.api as sm
from statsmodels.stats.diagnostic import het_breuschpagan
from statsmodels.stats.outliers_influence import OLSInfluence

res = sm.OLS(y, X).fit()
bp_stat, bp_pvalue, f_stat, f_pvalue = het_breuschpagan(res.resid, res.model.exog)
influence = OLSInfluence(res)
leverage = influence.hat_matrix_diag
```

Pair diagnostic output with interpretation: Breusch-Pagan tests heteroskedasticity; influence/leverage identifies observations that can dominate the fit.

## ANOVA and contrasts

For formula-fitted models, ANOVA can use design metadata:

```python
import statsmodels.api as sm
import statsmodels.formula.api as smf

res = smf.ols("y ~ C(group) + x", data=df).fit()
table = sm.stats.anova_lm(res, typ=2)
```

For custom hypotheses, use result methods such as `t_test`, `f_test`, or `wald_test` and write the contrast matrix or formula explicitly.

## Multiple testing

```python
from statsmodels.stats.multitest import multipletests
reject, p_adj, _, _ = multipletests(p_values, alpha=0.05, method="fdr_bh")
```

Name the correction method (`bonferroni`, `holm`, `fdr_bh`, etc.) and report both raw and adjusted p-values when possible.

## Contingency tables and proportions

Use `statsmodels.stats.contingency_tables.Table` or specific tests for categorical data. For proportions, use functions in `statsmodels.stats.proportion` and state whether the test is one-sample, two-sample, paired, or stratified.

## Power and effect sizes

Power utilities require assumptions about effect size, alpha, sample size, and sidedness. Make these assumptions explicit and avoid presenting power calculations as data-derived proof.
