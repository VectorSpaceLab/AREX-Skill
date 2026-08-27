# Figure Grid Workflows

## Customize a Figure-level Plot

```python
g = sns.relplot(data=df, x="time", y="value", hue="group", col="group", kind="line", height=3, aspect=1.1)
g.set_axis_labels("Time", "Value")
g.set_titles("Group: {col_name}")
sns.move_legend(g, "upper center", bbox_to_anchor=(.5, 1.05), ncol=3)
g.figure.set_size_inches(8, 3.2)
g.figure.savefig("facets.png", bbox_inches="tight")
```

## FacetGrid With a Custom Function

```python
def annotate_mean(data, color, **kws):
    ax = plt.gca()
    ax.axhline(data["value"].mean(), color=color, ls="--")

g = sns.FacetGrid(df, col="group", height=3)
g.map_dataframe(sns.scatterplot, x="time", y="value")
g.map_dataframe(annotate_mean)
```

Use `map_dataframe` when the plotting function accepts `data=` and named variables.

## PairGrid Customization

```python
g = sns.PairGrid(df, vars=["x", "y", "z"], hue="group", corner=True)
g.map_lower(sns.scatterplot, s=20)
g.map_diag(sns.histplot, element="step")
g.add_legend()
```

## JointGrid Customization

```python
g = sns.JointGrid(data=df, x="x", y="y", height=5)
g.plot_joint(sns.scatterplot, alpha=.6)
g.plot_marginals(sns.histplot, bins=20)
g.refline(x=0, y=0)
```
