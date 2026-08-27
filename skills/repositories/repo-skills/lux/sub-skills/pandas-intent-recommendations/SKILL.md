---
name: pandas-intent-recommendations
description: "Use Lux's Pandas-integrated DataFrame and Series intent workflow
  to generate and inspect recommendations."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Pandas Intent Recommendations

Use this sub-skill when the task is about Lux's Pandas integration: creating `LuxDataFrame` or `LuxSeries` objects through Pandas, setting or clearing dataframe intent, inspecting recommendation tabs, understanding `current_vis` and `exported`, or preserving Pandas behavior while using Lux recommendations.

## Route here for

- Import order and Pandas monkeypatch behavior for `pd.DataFrame`, `pd.Series`, and `pd.read_*` loaders.
- `LuxDataFrame` and `LuxSeries` basics, including `to_pandas()` and recommendation access.
- `df.intent`, `df.set_intent(...)`, `df.clear_intent()`, and `df.set_intent_as_vis(...)` workflows.
- Programmatic inspection of `df.recommendation`, `df.current_vis`, and the basic meaning of `df.exported`.
- Default recommendation tabs and intent-specific tabs.
- Local dataframe caveats for `head()`, `tail()`, `groupby()`, stale recommendations, and offline smoke validation.

## Route away

- Detailed `Clause`, `Vis`, `VisList`, wildcard enumeration, or chart code export: use `visualization-export`.
- `lux.config`, plotting backend/style, custom action registration, sampling, or widget setup: use `configuration-actions`.
- Semantic data type fixes, temporal/geographic/id behavior, index/group recommendations, or hierarchical-index repair: use `special-data-types`.
- PostgreSQL, `LuxSQLTable`, `JoinedSQLTable`, or SQL executor behavior: use `sql-backend`.

## Operating checklist

1. Import `lux` before creating or loading the dataframe that should receive Lux behavior.
2. Confirm the object is a `LuxDataFrame` or `LuxSeries` before using Lux-only attributes.
3. If no intent is set, inspect default recommendation tabs through `df.recommendation` or by displaying the dataframe in a supported notebook frontend.
4. Set intent with a list, not a bare string. Use attribute names such as `"sales"`, filters such as `"region=West"`, or a small number of `lux.Clause` objects for constraints.
5. Treat `df.current_vis` as the compiled visualization(s) for the intent and `df.recommendation` as the next-step recommendation dictionary.
6. If recommendations appear stale after dataframe mutation, call `df.expire_recs()`; if data types or metadata changed, also call `df.expire_metadata()`.
7. For non-notebook validation, run the bundled offline smoke script in `scripts/intent_recommendation_smoke.py`.

## Bundled references

- `references/workflows.md` — recommended Pandas + Lux workflows and caveats.
- `references/api-reference.md` — concise API and behavior reference for this sub-skill.
- `references/troubleshooting.md` — symptom-to-fix guide for import, intent, recommendation, and export-selection issues.
