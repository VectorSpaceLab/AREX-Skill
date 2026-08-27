---
name: lux
description: "Use Lux/Lux API for Pandas-integrated visual exploratory data
  analysis, intent-driven recommendations, chart export, configuration, semantic
  data types, and optional SQL tables."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Lux repo skill

Use this skill when a task involves Lux/Lux API (`lux-api`), a Pandas dataframe with Lux recommendations, intent-driven visualization, `Clause`/`Vis`/`VisList`, Lux widget/display configuration, semantic data typing, or optional PostgreSQL-backed `LuxSQLTable` workflows.

## First decisions

1. **Install/import check**: Lux installs as `lux-api` but imports as `lux`.
2. **Import order**: import `lux` before creating or loading Pandas dataframes that should become `LuxDataFrame` objects.
3. **Workflow shape**: decide whether the user is asking about dataframe recommendations, direct visualization objects, configuration/actions, semantic data types, or SQL-backed tables.
4. **Environment shape**: base Lux workflows are CPU/Pandas/visualization workflows. SQL is optional and requires a PostgreSQL service plus connector packages.
5. **Staleness check**: read `references/repo-provenance.md` before refreshing or trusting this skill against a different Lux checkout/version.

Minimal public install and import check:

```bash
pip install lux-api
python - <<'PY'
import lux
import pandas as pd
print(lux.__version__)
print(pd.DataFrame.__module__)
PY
```

For a stronger offline check after installation, run `scripts/check_lux_environment.py` and `scripts/lux_recommendation_smoke.py`.

## Route map

| User task | Read next |
| --- | --- |
| Import Lux with Pandas, set `df.intent`, inspect recommendation tabs, explain `df.current_vis` or `df.exported`, reset stale recommendations | `sub-skills/pandas-intent-recommendations/SKILL.md` |
| Construct a `Clause`, one `Vis`, or a `VisList`; enumerate wildcards; refresh a visualization source; export Altair/Matplotlib/Vega-Lite/Python code | `sub-skills/visualization-export/SKILL.md` |
| Configure `lux.config`, plotting backend/style, sampling, top-k/sort, default display, custom actions, or widget/debug diagnostics | `sub-skills/configuration-actions/SKILL.md` |
| Fix or explain semantic data types, temporal/geographic/id columns, named row/column indexes, grouped dataframes, small/empty dataframe warnings | `sub-skills/special-data-types/SKILL.md` |
| Connect Lux to PostgreSQL tables with `LuxSQLTable`, `JoinedSQLTable`, `SQLExecutor`, or SQL connection troubleshooting | `sub-skills/sql-backend/SKILL.md` |

## Shared references and scripts

- `references/package-overview.md` summarizes public objects, versioned surfaces, optional dependencies, and recommendation vocabulary.
- `references/troubleshooting.md` covers cross-cutting install/import/widget/cache/version/SQL issues.
- `references/repo-provenance.md` records the source snapshot and refresh baseline.
- `references/repo-routing-metadata.json` contains structured router metadata for managed repo-skill import tooling.
- `scripts/check_lux_environment.py` verifies package imports, versions, Pandas patching, and Lux diagnostics.
- `scripts/lux_recommendation_smoke.py` runs an integrated offline dataframe/intent/export smoke check.

## Operating rules

- Do not tell users to run Lux repository tests, docs, examples, or upload scripts as part of normal package use. Use this skill's bundled references and scripts instead.
- Prefer in-memory or user-provided data over remote tutorial datasets for verification.
- If `df.recommendation` looks stale after changing config or data, call `df.expire_recs()`; if metadata or data types changed, also call `df.expire_metadata()` or recreate the dataframe.
- If an intent expands to multiple visualizations, use `VisList`, not `Vis`.
- Treat SQL support as optional/service-backed. Confirm connector, credentials, table existence, and privileges before constructing `LuxSQLTable`.
- Keep notebook/widget setup separate from terminal validation: terminal scripts should inspect recommendation objects and export code, not expect interactive widgets.
