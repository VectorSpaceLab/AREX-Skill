# Function Interface Workflows

## No-network EDA Figure

```python
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

rng = np.random.default_rng(4)
df = pd.DataFrame({
    "time": np.tile(np.arange(12), 3),
    "signal": np.r_[rng.normal(0, .4, 12).cumsum(), rng.normal(.2, .5, 12).cumsum(), rng.normal(-.1, .3, 12).cumsum()],
    "group": np.repeat(["control", "drug-a", "drug-b"], 12),
    "score": rng.normal(size=36),
})
fig, axs = plt.subplots(2, 2, figsize=(8, 6))
sns.lineplot(data=df, x="time", y="signal", hue="group", errorbar=None, ax=axs[0, 0])
sns.histplot(data=df, x="score", hue="group", element="step", stat="density", common_norm=False, ax=axs[0, 1])
sns.boxplot(data=df, x="group", y="signal", ax=axs[1, 0])
corr = df.pivot_table(index="time", columns="group", values="signal").corr()
sns.heatmap(corr, vmin=-1, vmax=1, center=0, cmap="vlag", annot=True, ax=axs[1, 1])
fig.tight_layout()
fig.savefig("seaborn_eda.png")
```

## Figure-level Faceting

Use figure-level functions when the user asks for small multiples:

```python
g = sns.relplot(data=df, x="time", y="signal", hue="group", col="group", kind="line", height=3, aspect=1.2)
g.set_axis_labels("Time", "Signal")
g.figure.savefig("faceted_signal.png")
```

Do not pass `ax=` to `relplot`, `displot`, `catplot`, or `lmplot`. Customize the returned grid.

## Categorical Axis With Numeric Labels

If a categorical plot must preserve real numeric spacing:

```python
sns.stripplot(data=df, x="dose", y="response", native_scale=True)
```

If a seaborn categorical function does not support the desired overlay semantics, either use `pointplot` for categorical summaries or map category levels to integer positions before drawing a line overlay.

## Regression With Optional statsmodels

```python
try:
    import statsmodels  # noqa: F401
except ImportError:
    ax = sns.regplot(data=df, x="x", y="y")
else:
    ax = sns.regplot(data=df, x="x", y="y", lowess=True)
```

Use ordinary `regplot` when optional regression backends are missing or the request only needs a simple trend.

## Matrix Workflow

- Use `heatmap` for any 2D numeric table, correlation matrix, confusion matrix, or pivot table.
- Use `clustermap` when row/column ordering by hierarchical clustering is meaningful and SciPy is installed.
- Validate mask and annotation shapes before plotting.
