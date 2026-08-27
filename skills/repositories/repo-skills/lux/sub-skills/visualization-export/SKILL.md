---
name: visualization-export
description: "Construct and export Lux Clause, Vis, and VisList visualizations."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Lux visualization export router

Use this sub-skill when the user needs to construct Lux `Clause`, `Vis`, or `VisList` objects directly; enumerate wildcard visualization collections; refresh a visualization against a new dataframe; or export chart code/specifications from an individual `Vis`.

## Route here for

- Creating a single visualization with `lux.vis.Vis.Vis` and intent strings or `Clause` objects.
- Creating a collection with `lux.vis.VisList.VisList`, including wildcard `"?"`, list-valued attributes, and manually composed lists of `Vis` objects.
- Exporting a single `Vis` with `to_altair(standalone=False)`, `to_matplotlib()`, `to_vegalite(prettyOutput=True)`, or `to_code(language=...)`.
- Handling special-character columns, long labels, and the difference between `df.exported[0]` as a `Vis` and multiple exported widget selections as a `VisList`.
- Explaining `VisList.sort`, `showK`, `normalize_score`, `refresh_source`, `map`, `get`, and the present-but-not-implemented `set` method.

## Route elsewhere

- Pandas import-hook basics, dataframe intent, recommendations, `df.recommendation`, and `df.current_vis`: use `pandas-intent-recommendations`.
- Global plotting backend, plot style, chart scale, label length, top-k, sort, widget setup, and custom recommendation actions: use `configuration-actions`.
- Semantic data types, datetime/geographic/id behavior, groupby/index views, and type overrides: use `special-data-types`.
- PostgreSQL-backed `LuxSQLTable` or SQL export workflows: use `sql-backend`.

## Required references

Read these bundled references before giving detailed guidance:

1. `references/api-reference.md` for verified Lux 0.5.1 signatures and method behavior.
2. `references/workflows.md` for construction, wildcard, refresh, export, standalone-data, and `df.exported` workflows.
3. `references/troubleshooting.md` for multi-visualization errors, export failures, special-character columns, long labels, stale sources, and unsupported code-export languages.

A safe offline smoke script is bundled at `scripts/vis_export_smoke.py`. Use it to verify that the installed Lux package can construct `Clause`, `Vis`, and `VisList` objects and emit Altair, Matplotlib, and Vega-Lite export tokens on a tiny local dataframe.
