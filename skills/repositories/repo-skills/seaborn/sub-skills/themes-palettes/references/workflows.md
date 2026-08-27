# Theme and Palette Workflows

## Temporary Publication Style

```python
with sns.axes_style("whitegrid"), sns.plotting_context("paper", font_scale=1.2), sns.color_palette("colorblind"):
    ax = sns.lineplot(data=df, x="time", y="value", hue="group")
    ax.figure.savefig("styled_plot.png", bbox_inches="tight")
```

## Categorical Hue Palette

```python
levels = sorted(df["group"].unique())
palette = dict(zip(levels, sns.color_palette("colorblind", n_colors=len(levels))))
sns.scatterplot(data=df, x="x", y="y", hue="group", palette=palette)
```

Using a dict makes color-level assignment explicit and reproducible.

## Continuous Heatmap Palette

```python
cmap = sns.diverging_palette(240, 10, as_cmap=True)
sns.heatmap(corr, vmin=-1, vmax=1, center=0, cmap=cmap)
```

Use `center=` with diverging data and `as_cmap=True` for continuous color mapping.

## Dark Background

```python
import matplotlib.pyplot as plt
sns.set_theme(style="ticks", rc=plt.style.library["dark_background"])
sns.set_palette("bright")
```

Apply or reset the palette after dark style changes so colors keep enough contrast.
