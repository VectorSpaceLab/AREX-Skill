---
name: figure-grids
description: "Use seaborn grid objects and figure-level plot returns for facets,
  pair/joint layouts, legend movement, axes access, and layout customization."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# Figure Grids

Use this sub-skill when a task involves `FacetGrid`, `PairGrid`, `JointGrid`, `pairplot`, `jointplot`, or customizing a grid returned by `relplot`, `displot`, `catplot`, or `lmplot`.

## Route Here For

- Mapping functions over facets with `FacetGrid.map()` or `FacetGrid.map_dataframe()`.
- Pairwise variable grids with `PairGrid`, `pairplot`, and lower/upper/diagonal mappings.
- Joint and marginal plots with `JointGrid` and `jointplot`.
- Accessing `g.figure`, `g.axes`, `g.axes_dict`, `g.ax`, or `g.legend`.
- Resizing figure-level outputs, setting axis labels/titles, adding reference lines, and moving legends.
- Debugging `ax=` misuse with figure-level functions.

## Use Another Sub-skill For

- Choosing statistical plot function parameters: `../function-interface/SKILL.md`.
- Data shape/variable validation: `../data-utilities/SKILL.md`.
- Theme/palette decisions: `../themes-palettes/SKILL.md`.

## Start With

1. If the user names a figure-level function, capture its return (`g = sns.relplot(...)`) and customize `g`, not a preexisting `ax`.
2. Use `height` and `aspect` for seaborn figure-level sizing; use `g.figure.set_size_inches(...)` when exact final size matters.
3. Use `g.axes_dict` when facets have semantic keys and `g.axes.flat` for bulk axis iteration.
4. Use `sns.move_legend(g_or_ax, ...)` to recreate legends safely.
5. Save through `g.figure.savefig(...)` or `g.savefig(...)` when available.

## References

- Grid class and convenience API map: `references/api-reference.md`.
- Layout and customization recipes: `references/workflows.md`.
- Failure recovery: `references/troubleshooting.md`.

## Quick Smoke Check

```bash
python sub-skills/figure-grids/scripts/grid_smoke.py --output-dir /tmp/seaborn-grid-smoke
```
