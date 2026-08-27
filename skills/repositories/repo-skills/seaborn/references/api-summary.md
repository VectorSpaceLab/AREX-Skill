# seaborn API Summary

## Purpose

Read this for a package-wide map before choosing a sub-skill. Detailed signatures and recipes live in the nearest sub-skill reference.

## Import Conventions

```python
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import seaborn.objects as so
```

Use `matplotlib.use("Agg")` before importing `pyplot` in headless scripts that only need to save files.

## Public API Families

| Family | Public APIs | Route |
| --- | --- | --- |
| Relational plots | `relplot`, `scatterplot`, `lineplot` | `sub-skills/function-interface/` |
| Distribution plots | `displot`, `histplot`, `kdeplot`, `ecdfplot`, `rugplot`, deprecated `distplot` | `sub-skills/function-interface/` |
| Categorical plots | `catplot`, `stripplot`, `swarmplot`, `boxplot`, `violinplot`, `boxenplot`, `pointplot`, `barplot`, `countplot` | `sub-skills/function-interface/` |
| Regression plots | `lmplot`, `regplot`, `residplot` | `sub-skills/function-interface/` |
| Matrix plots | `heatmap`, `clustermap` | `sub-skills/function-interface/` |
| Grid objects | `FacetGrid`, `PairGrid`, `JointGrid`, `pairplot`, `jointplot` | `sub-skills/figure-grids/` |
| Objects API | `so.Plot`, marks, stats, moves, scales | `sub-skills/objects-interface/` |
| Themes/styles | `set_theme`, `axes_style`, `plotting_context`, `set_style`, `set_context`, `set_palette`, `reset_defaults`, `reset_orig`, `set` | `sub-skills/themes-palettes/` |
| Palettes/colors | `color_palette`, `hls_palette`, `husl_palette`, `cubehelix_palette`, `dark_palette`, `light_palette`, `diverging_palette`, `blend_palette`, `xkcd_palette`, `crayon_palette`, `mpl_palette`, `palplot` | `sub-skills/themes-palettes/` |
| Utilities | `despine`, `move_legend`, `load_dataset`, `get_dataset_names`, `get_data_home`, color helpers | `sub-skills/figure-grids/`, `sub-skills/data-utilities/`, `sub-skills/themes-palettes/` |

## Axes-level, Figure-level, and Object APIs

| API style | Examples | Returns | Can draw on existing `ax`? | Best for |
| --- | --- | --- | --- | --- |
| Axes-level functions | `scatterplot`, `histplot`, `boxplot`, `regplot`, `heatmap` | matplotlib `Axes` | Yes, pass `ax=` | Composing inside caller-created figures/subplots. |
| Figure-level functions | `relplot`, `displot`, `catplot`, `lmplot`, `pairplot`, `jointplot`, `clustermap` | seaborn grid object or `ClusterGrid` | No, they create/manage their own figure | Facets, pair/joint layouts, automatic figure sizing. |
| Grid classes | `FacetGrid`, `PairGrid`, `JointGrid` | seaborn grid object | The grid owns axes after construction | Custom multi-axes mapping and layout control. |
| Objects interface | `so.Plot(...).add(...).facet(...)` | `Plot` until rendered; `Plotter` from `.plot()` | Use `.on(ax_or_figure)` for explicit target | Declarative layering and composable grammar-like plots. |

Do not pass `ax=` to figure-level functions. If a user already created axes, use the corresponding axes-level function or move to `figure-grids` for grid-owned customization after plotting.

## Optional Dependencies

| Dependency | Needed for | Failure signal |
| --- | --- | --- |
| SciPy | `clustermap`, `dendrogram`, faster/complete KDE features such as cumulative KDE in stats APIs | `RuntimeError: clustermap requires scipy to be available`, `Cumulative KDE evaluation requires scipy` |
| statsmodels | `regplot`/`lmplot` options `logistic=True`, `lowess=True`, `robust=True`; selected residual lowess workflows | Optional dependency error mentioning statsmodels |
| fastcluster | Optional acceleration for large hierarchical clustering | clustermap still works through SciPy for ordinary cases; only fastcluster-specific paths are skipped |
| ipywidgets | Interactive palette chooser widgets | `ImportError: Interactive palettes require ipywidgets` |

## Return-object Rule of Thumb

- If the return is an `Axes`, use `ax.set(...)`, `ax.figure.savefig(...)`, `sns.move_legend(ax, ...)`, or matplotlib artist methods.
- If the return is a grid object, use `g.figure`, `g.axes`, `g.axes_dict`, `g.set(...)`, `g.set_axis_labels(...)`, and `sns.move_legend(g, ...)`.
- If using `so.Plot`, keep chaining methods until `.plot()`, `.show()`, or `.save(...)`.
