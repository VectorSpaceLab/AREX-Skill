---
name: function-interface
description: "Use seaborn's classic plotting functions for relational,
  distribution, categorical, regression, and matrix statistical graphics."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# Function Interface

Use this sub-skill when the task asks for `sns.scatterplot`, `lineplot`, `histplot`, `catplot`, `regplot`, `heatmap`, `clustermap`, or another classic seaborn plotting function.

## Route Here For

- Relational plots: `scatterplot`, `lineplot`, and figure-level `relplot`.
- Distribution plots: `histplot`, `kdeplot`, `ecdfplot`, `rugplot`, and figure-level `displot`.
- Categorical plots: `stripplot`, `swarmplot`, `boxplot`, `violinplot`, `boxenplot`, `pointplot`, `barplot`, `countplot`, and figure-level `catplot`.
- Regression plots: `regplot`, `residplot`, and figure-level `lmplot`.
- Matrix plots: `heatmap` and `clustermap`.
- Choosing axes-level versus figure-level APIs and translating user intent into seaborn function parameters.

## Use Another Sub-skill For

- Declarative `seaborn.objects` composition: `../objects-interface/SKILL.md`.
- Direct `FacetGrid`, `PairGrid`, or `JointGrid` programming and layout/legend access: `../figure-grids/SKILL.md`.
- Themes, contexts, palettes, colormaps, and color utilities: `../themes-palettes/SKILL.md`.
- Data-shape checks, `load_dataset`, or cache/network issues: `../data-utilities/SKILL.md`.

## Start With

1. Identify the statistical relationship: relation, distribution, category summary, regression, or matrix.
2. Decide axes-level versus figure-level. Use axes-level functions when the caller has axes or needs subplot composition; use figure-level functions for faceting and automatic figure management.
3. Confirm data semantics: long-form `data=df, x="col", y="col"`; wide-form `data=wide_df` without `x`/`y`; vector arrays for small scripts.
4. Add semantic variables (`hue`, `size`, `style`, `row`, `col`) only when the data columns exist and the legend/facet behavior is useful.
5. Check optional dependencies before claiming `clustermap`, cumulative KDE, `lowess`, `logistic`, or `robust` regression support.

## References

- Function signatures and parameter groups: `references/api-reference.md`.
- No-network recipes and examples: `references/workflows.md`.
- Failure recovery for plot functions: `references/troubleshooting.md`.
- Shared package API map: `../../references/api-summary.md`.
- Shared data contracts: `../../references/data-semantics.md`.

## Quick Smoke Check

```bash
python sub-skills/function-interface/scripts/function_plot_smoke.py --output-dir /tmp/seaborn-function-smoke
```

The helper creates synthetic data, uses the Agg backend, renders representative axes-level plots, and conditionally checks SciPy/statsmodels-backed features when available.
