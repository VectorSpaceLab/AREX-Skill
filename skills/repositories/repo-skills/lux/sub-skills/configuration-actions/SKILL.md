---
name: configuration-actions
description: "Configure Lux display, plotting, sampling, custom recommendation
  actions, and widget debugging."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# configuration-actions

Use this sub-skill when the task is about Lux session configuration rather than building individual visualizations or connecting to SQL tables.

## Route here

- Changing `lux.config` options for display, plotting backend, chart sizing, sampling, heatmaps, ranking, top-k selection, fallback/debug behavior, or executor selection.
- Registering, inspecting, or removing custom recommendation actions with `lux.config.register_action` and `lux.config.remove_action`.
- Diagnosing Lux widget setup with `lux.debug_info()` and notebook/lab extension commands.
- Forcing cached recommendations to refresh after configuration or action-manager changes.

## Route elsewhere

- For constructing `Clause`, `Vis`, `VisList`, or exporting a selected chart to Altair, Matplotlib, Vega-Lite, or code, use `visualization-export`.
- For `LuxSQLTable`, SQL connections, SQL table setup, PostgreSQL service checks, or `set_SQL_connection`, use `sql-backend`.
- For dataframe intent syntax, default recommendation categories, and `df.intent`, use `pandas-intent-recommendations`.
- For semantic data type overrides, temporal/geographic handling, and index/groupby caveats, use `special-data-types`.

## Bundled references

- `references/configuration.md` gives the `lux.config` option map, safe assignment patterns, refresh rules, and invalid-value behavior.
- `references/custom-actions.md` gives the custom action contract, validator semantics, removal behavior, and a self-contained recipe.
- `references/troubleshooting.md` maps common widget, stale recommendation, invalid config, and custom action failures to fixes.
- `scripts/config_action_smoke.py` is an offline smoke test that imports Lux, registers a validator-gated action on a tiny dataframe, and checks `lux.debug_info(return_string=True)`.

## Operating rules

1. Import `lux` before creating Pandas dataframes that should become `LuxDataFrame` objects.
2. Prefer setting configuration before the first dataframe display. If recommendations have already been generated, call `df.expire_recs()` before redisplaying the dataframe.
3. Keep examples offline and local. Do not depend on hosted datasets or the Lux source checkout.
4. Treat SQL executor configuration as a handoff to `sql-backend` unless the task only needs to switch back to `lux.config.set_executor_type("Pandas")`.
