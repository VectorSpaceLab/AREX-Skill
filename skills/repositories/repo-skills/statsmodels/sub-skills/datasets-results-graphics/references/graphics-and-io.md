# Graphics and I/O workflows

## Headless plotting

In CI, servers, and notebooks without a GUI, set an Agg backend before importing `pyplot`:

```python
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
```

Then create figures through statsmodels graphics functions and save them:

```python
import statsmodels.api as sm
fig = sm.graphics.qqplot(res.resid, line="45")
fig.savefig("qqplot.png", dpi=150, bbox_inches="tight")
```

## Common graphics surfaces

| Surface | Use |
| --- | --- |
| `sm.graphics.qqplot`, `qqplot_2samples`, `ProbPlot` | Distribution and residual normality plots. |
| `statsmodels.graphics.regressionplots` | Regression fit, partial regression, influence, CCPR/CERES plots. |
| `statsmodels.graphics.tsaplots.plot_acf`, `plot_pacf` | Time-series autocorrelation diagnostics. |
| `statsmodels.graphics.gofplots` | Goodness-of-fit plotting helpers. |
| `statsmodels.graphics.factorplots`, `boxplots`, `mosaicplot` | Specialized exploratory/statistical plots. |

Graphics usually require matplotlib. Some plotting examples need pandas and model-specific fitted results.

## Summary export

Use result summaries for display:

```python
summary = res.summary()
text = summary.as_text()
html = summary.as_html()
latex = summary.as_latex()
```

For structured tables, collect attributes into a DataFrame:

```python
import pandas as pd
coef_table = pd.DataFrame({
    "coef": res.params,
    "std_err": res.bse,
    "pvalue": res.pvalues,
})
coef_table.to_csv("coefficients.csv")
```

## `webdoc`

`statsmodels.tools.web.webdoc` can open online documentation for an object. Treat it as a convenience, not a required runtime dependency, because it may need a browser or network access.
