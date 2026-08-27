# Objects Interface Workflows

## Layered Dot and Trend Plot

```python
import matplotlib
matplotlib.use("Agg")
import numpy as np
import pandas as pd
import seaborn.objects as so

rng = np.random.default_rng(7)
df = pd.DataFrame({
    "x": np.tile(np.arange(20), 2),
    "y": np.r_[rng.normal(0, 1, 20).cumsum(), rng.normal(.2, 1, 20).cumsum()],
    "group": np.repeat(["baseline", "variant"], 20),
})
(
    so.Plot(df, x="x", y="y", color="group")
    .add(so.Dot(alpha=.45), so.Jitter(width=.15))
    .add(so.Line(linewidth=2), so.Agg())
    .label(title="Objects layered trend")
    .save("objects_layered.png")
)
```

## Faceting

```python
p = so.Plot(df, x="x", y="y", color="group").add(so.Line()).facet(col="group")
p.save("objects_facets.png")
```

Use `.pair(x=[...], y=[...])` for pairwise variable combinations; route to `figure-grids` if the user specifically wants `PairGrid` or `pairplot` behavior.

## Scales and Themes

```python
p = (
    so.Plot(df, x="x", y="y", color="group")
    .add(so.Dot())
    .scale(color=so.Nominal())
    .theme({"axes.facecolor": ".95"})
)
```

Use `themes-palettes` when choosing palette values, global rc settings, or reusable style contexts.

## Choosing Objects vs Function API

Choose `objects` when the task asks for layered grammar-like composition, per-layer stats/moves, custom property mappings, or a chainable plot specification. Choose `function-interface` when a named high-level plot function directly expresses the desired output.
