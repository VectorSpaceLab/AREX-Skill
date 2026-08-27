---
name: seaborn
description: "Use seaborn for statistical data visualization with the function
  API, objects interface, grids, themes, palettes, dataset utilities, and
  plotting troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# seaborn

Use this repo skill when a task involves `seaborn`, `import seaborn as sns`, `seaborn.objects`, statistical graphics, tidy/wide-form plotting, figure-level grids, themes, palettes, example datasets, or seaborn-specific errors around matplotlib, pandas, SciPy, or statsmodels.

Seaborn is a pure-Python statistical visualization library built on matplotlib and designed for pandas/NumPy-style data. It provides two user-facing APIs: the classic function interface (`sns.scatterplot`, `sns.catplot`, `sns.clustermap`, etc.) and the declarative `seaborn.objects` interface.

## Start Here

1. Confirm seaborn is installed in the active Python environment with the root check below.
2. Identify whether the user wants a classic function plot, declarative objects composition, multi-plot grid layout, aesthetics/palette work, or data-shape/dataset troubleshooting.
3. Route to the narrow sub-skill and use linked references/scripts there; keep this root file as a router.
4. Use synthetic or user-provided data for reusable examples. Treat `sns.load_dataset()` as a network-backed convenience, not a requirement for normal plotting.
5. Read [references/troubleshooting.md](references/troubleshooting.md) for cross-cutting install/import, display, optional dependency, and data-cache failures.

## Install And Import Check

For normal package use:

```bash
python -m pip install seaborn
python - <<'PY'
import seaborn as sns
import matplotlib
print('seaborn', sns.__version__)
print('matplotlib backend', matplotlib.get_backend())
PY
```

Optional statistical features use the documented `stats` extra:

```bash
python -m pip install 'seaborn[stats]'
```

Run the bundled diagnostic before debugging a local environment:

```bash
python scripts/check_seaborn_environment.py
```

The check imports seaborn, validates mandatory dependencies, reports optional SciPy/statsmodels/ipywidgets/fastcluster availability, and renders tiny noninteractive plots with the Agg backend when requested.

## Sub-skill Routes

- [function-interface](sub-skills/function-interface/SKILL.md): classic seaborn plotting functions for relational, distribution, categorical, regression, and matrix plots; axes-level versus figure-level function choice; optional SciPy/statsmodels behavior; no-network workflow recipes.
- [objects-interface](sub-skills/objects-interface/SKILL.md): declarative `seaborn.objects` workflows with `Plot`, marks, stats, moves, scales, layering, faceting, theme/label/scale methods, and save/show behavior.
- [figure-grids](sub-skills/figure-grids/SKILL.md): `FacetGrid`, `PairGrid`, `JointGrid`, `pairplot`, `jointplot`, figure-level return objects, legend movement, axes access, layout sizing, and matplotlib customization.
- [themes-palettes](sub-skills/themes-palettes/SKILL.md): `set_theme`, styles, contexts, palettes, colormaps, color utilities, dark mode, and optional interactive palette widgets.
- [data-utilities](sub-skills/data-utilities/SKILL.md): long-form/wide-form/vector data contracts, semantic mappings, example dataset cache/network behavior, `load_dataset`, `SEABORN_DATA`, and data validation helpers.

## Common Workflow Routing

- Exploratory tabular visualization: start with `data-utilities` for data shape, then `function-interface` for plot families, then `themes-palettes` for presentation style.
- Multi-panel statistical figure: use `function-interface` for figure-level functions (`relplot`, `displot`, `catplot`, `lmplot`) or `figure-grids` when direct grid programming/custom layout is needed.
- Layered declarative chart: use `objects-interface`; cross-route to `themes-palettes` for reusable theme/palette decisions.
- Publication polish: use `figure-grids` for figure size/axes/legends and `themes-palettes` for context/style/palette choices.
- Dataset/cache or data-shape errors: use `data-utilities`, then return to the plot-owning sub-skill once the input contract is clear.

## Shared References And Scripts

- Package-wide API map and return-object distinctions: [references/api-summary.md](references/api-summary.md).
- Shared data/semantic conventions: [references/data-semantics.md](references/data-semantics.md).
- Cross-cutting failure recovery: [references/troubleshooting.md](references/troubleshooting.md).
- Repository snapshot and refresh baseline: [references/repo-provenance.md](references/repo-provenance.md).
- Router import metadata: [references/repo-routing-metadata.json](references/repo-routing-metadata.json).
- Root environment diagnostic: [scripts/check_seaborn_environment.py](scripts/check_seaborn_environment.py).

## Boundaries

- Seaborn creates matplotlib figures and artists; use matplotlib APIs for very deep artist-level customization after seaborn returns an Axes, Grid, or Plotter object.
- Seaborn is not a statistical modeling package. Use SciPy/statsmodels/sklearn/pandas for extracting model results or statistics beyond what seaborn visualizes.
- Do not make runtime guidance depend on original repository examples, docs, notebooks, tests, or source paths. Use the bundled references/scripts in this skill.
