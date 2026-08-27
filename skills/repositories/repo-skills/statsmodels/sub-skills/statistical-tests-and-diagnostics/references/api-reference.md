# Statistical tests and diagnostics API reference

Common modules:

| Module | Typical content |
| --- | --- |
| `statsmodels.stats.diagnostic` | Residual diagnostics, heteroskedasticity, serial correlation, specification tests. |
| `statsmodels.stats.outliers_influence` | Influence measures, leverage, variance inflation factor. |
| `statsmodels.stats.anova` | ANOVA tables for fitted models. |
| `statsmodels.stats.multitest` | P-value correction and multiple-testing procedures. |
| `statsmodels.stats.contingency_tables` | Table analysis, McNemar, stratified tables. |
| `statsmodels.stats.weightstats` | t tests, z tests, descriptive comparisons. |
| `statsmodels.stats.proportion` | Binomial/proportion tests and confidence intervals. |
| `statsmodels.stats.power` | Power and sample-size calculations. |
| `statsmodels.stats.meta_analysis` | Effect-size combination/meta-analysis utilities. |
| `statsmodels.stats.mediation` and `statsmodels.treatment` | Mediation and treatment-effect workflows. |

Common fitted-result diagnostics:

```python
from statsmodels.stats.diagnostic import het_breuschpagan, acorr_ljungbox
from statsmodels.stats.outliers_influence import OLSInfluence, variance_inflation_factor
from statsmodels.stats.anova import anova_lm
```

Always record the null hypothesis and test assumptions. Many statsmodels functions return tuples, arrays, DataFrames, or small result objects; unpack deliberately and label outputs.
