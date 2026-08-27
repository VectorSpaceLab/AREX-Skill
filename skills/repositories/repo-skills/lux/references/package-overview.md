# Lux package overview

## When to read

Read this when you need a compact map of Lux API surfaces before choosing a sub-skill. Lux 0.5.1 is distributed as `lux-api`, imports as `lux`, and augments Pandas objects after `import lux`.

## Core behavior

- Install users with `pip install lux-api`; import with `import lux`.
- Import `lux` before creating or loading dataframes that should be patched. After import, Pandas dataframe/series constructors and many `pd.read_*` loaders produce Lux subclasses.
- The installed package inspection verified that `pd.DataFrame` resolves to `lux.core.frame.LuxDataFrame` after `import lux`.
- Lux keeps Pandas semantics for ordinary operations while adding recommendation metadata, widget display, intent, and chart export properties.
- `lux-widget` is installed as part of the package dependency set, but notebook/lab extension activation may still be needed in a user's Jupyter frontend.

## Public objects and routes

| Object or concept | Verified surface | Use |
| --- | --- | --- |
| `lux.Clause` | `Clause(description='', attribute='', value='', filter_op='=', channel='', data_type='', data_model='', aggregation='', bin_size=0, weight=1, sort='', timescale='', exclude='')` | Structured intent clauses and constraints. Use `visualization-export` for details. |
| `lux.core.frame.LuxDataFrame` | `set_intent`, `clear_intent`, `set_intent_as_vis`, `set_data_type`, `to_pandas`, `expire_recs`, `expire_metadata`, `save_as_html`, `head`, `tail`, `groupby` | Pandas-integrated recommendations and metadata. Use `pandas-intent-recommendations` and `special-data-types`. |
| `lux.vis.Vis.Vis` | `Vis(intent, source=None, title='', score=0.0)` plus `to_altair`, `to_matplotlib`, `to_vegalite`, `to_code`, `refresh_source` | Construct and export one visualization. Use `visualization-export`. |
| `lux.vis.VisList.VisList` | `VisList(input_lst, source=None)` plus `sort`, `showK`, `normalize_score`, `refresh_source`, `map`, `get`, `set` | Enumerate or manipulate collections of visualizations. Use `visualization-export`. |
| `lux.config` | Display, sampling, plotting, fallback, top-k, sorting, custom action, executor, and SQL connection settings | Configure a session. Use `configuration-actions`; route SQL details to `sql-backend`. |
| `lux.LuxSQLTable` | `LuxSQLTable(table_name='')`, `set_SQL_table(t_name)` | Optional PostgreSQL-backed table exploration. Use `sql-backend`. |
| `lux.JoinedSQLTable` | `JoinedSQLTable(joins=[])` | Optional view creation from explicit join conditions. Use `sql-backend` and confirm service permissions first. |

## Recommendation vocabulary

- Default dataframe recommendations include action categories such as `Correlation`, `Distribution`, `Occurrence`, and `Temporal`, depending on dataframe columns and metadata.
- Intent-driven recommendations include tabs such as `Enhance`, `Filter`, `Generalize`, `Current Vis`, and `Similarity`, depending on the intent shape.
- `df.recommendation` is a dictionary of action names to `VisList` values.
- `df.current_vis` is the visualization or list of visualizations compiled directly from the current intent.
- `df.exported` is populated by widget selection/export interactions; in non-widget contexts it can warn or be empty.

## Optional services and dependencies

- Base Pandas/visualization workflows do not require GPU hardware.
- SQL workflows are optional and require a PostgreSQL service plus a connector such as `psycopg2` or a SQLAlchemy PostgreSQL engine.
- Many upstream examples use remote datasets; the bundled scripts in this skill use only in-memory data so future agents can validate Lux without network access.

## Validation helpers

- Run `scripts/check_lux_environment.py` to check imports, versions, Pandas patching, and Lux diagnostics.
- Run `scripts/lux_recommendation_smoke.py` for an integrated offline dataframe/intent/export check.
- Use sub-skill-specific scripts when the user task is focused on intent, export, config/custom actions, semantic data types, or SQL connectivity.
