---
name: special-data-types
description: "Use Lux semantic data types, temporal and geographic handling, ID
  suppression, and index/grouped dataframe recommendations."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Lux Special Data Types

Use this sub-skill when a Lux workflow depends on the semantic meaning of columns rather than only Pandas dtypes: inferred or overridden data types, temporal columns, geographic columns, identifier suppression, named indexes, and grouped or crosstabbed dataframes.

## Route here for

- Inspecting `df.data_type` and correcting Lux semantic types with `df.set_data_type(...)`.
- Explaining `quantitative`, `nominal`, `geographical`, `temporal`, and `id` columns.
- Fixing date-like columns so Lux uses temporal line charts and time-aware recommendations.
- Preparing `state` or `country` columns for geographic recommendations.
- Understanding why ID-like fields are not visualized.
- Working with named row or column indexes, groupby aggregations, pivots, and crosstabs that produce `Row Groups` or `Column Groups` recommendations.
- Diagnosing empty, very small, or hierarchical-index dataframe messages.

## Route elsewhere

- For general Pandas import order, `df.intent`, recommendation keys, and default/intent action behavior, use `pandas-intent-recommendations`.
- For `Clause`, `Vis`, `VisList`, chart marks, Altair/Matplotlib/Vega-Lite export, or exported code, use `visualization-export`.
- For global Lux config, widget setup, plotting backend/style, or custom recommendation actions, use `configuration-actions`.
- For PostgreSQL-backed `LuxSQLTable` workflows, use `sql-backend`.

## Operating references

- Read `references/data-types.md` for the self-contained data-type, temporal, geographic, ID, and index/group workflow guide.
- Read `references/troubleshooting.md` when Lux gives a warning/message or when expected recommendations are missing.
- Run `scripts/data_type_smoke.py --help` or `scripts/data_type_smoke.py` in an environment with `lux-api` installed to verify the core offline data-type behaviors on tiny fixtures.

## Minimal workflow reminder

1. Import Lux before creating Pandas dataframes: `import lux; import pandas as pd`.
2. Inspect `df.data_type` after constructing or mutating a dataframe.
3. Convert real temporal columns with `pd.to_datetime(...)`; if a pre-existing `Vis` was built from the old source, refresh it with `vis.refresh_source(df)`.
4. Override semantic mistakes with `df.set_data_type({"column": "nominal"})`, using only Lux's accepted override values.
5. Flatten unsupported hierarchical indexes with `df.reset_index()` before asking Lux for recommendations.
