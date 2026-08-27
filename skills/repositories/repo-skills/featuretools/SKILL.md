---
name: featuretools
description: "Build, inspect, and reuse Featuretools automated feature
  engineering workflows for EntitySets, DFS, feature matrices, primitive
  authoring, feature inspection, and selection."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# Featuretools Repo Skill

Use this skill when a coding agent needs to work with the `featuretools` package as a library for automated feature engineering. The core flows are EntitySet modeling, Deep Feature Synthesis, feature-matrix generation, feature inspection, primitive authoring, and feature selection.

This generated skill is self-contained. It does not depend on the original checkout at runtime.

## Install And Sanity Check

Install the base package:

```bash
python -m pip install featuretools
```

Add optional extras only when the task needs them:

- `python -m pip install "featuretools[dask]"` for parallel feature-matrix calculation.
- `python -m pip install "featuretools[premium]"` for premium primitives.
- `python -m pip install "featuretools[nlp]"` for NLP primitives.
- `python -m pip install "featuretools[sql]"` for the external SQL add-on.
- `python -m pip install "featuretools[complete]"` for the bundled convenience meta-extra.

For graph rendering, install the Graphviz Python package and the system Graphviz binary separately.

Quick import check:

```bash
python - <<'PY'
import featuretools as ft
print(ft.__version__)
PY
```

For a broader smoke test, run `scripts/featuretools_smoke.py`.

## Route By Task

- Use `sub-skills/entitysets-and-data/` for `EntitySet`, `Relationship`, demo datasets, relationships, time indexes, serialization, and `EntitySet.plot`.
- Use `sub-skills/deep-feature-synthesis/` for `dfs`, `DeepFeatureSynthesis`, `calculate_feature_matrix`, cutoff times, training windows, `encode_features`, and optional Dask-backed matrix generation.
- Use `sub-skills/feature-inspection-and-selection/` for `show_info`, primitive catalog discovery, primitive recommendations, and feature-matrix pruning helpers.
- Use `sub-skills/primitives-and-feature-definitions/` for custom primitives, feature objects, `describe_feature`, `graph_feature`, and `save_features` / `load_features`.

## Shared References

- `references/installation-and-compatibility.md`: supported Python versions, base dependencies, extras, and optional system requirements.
- `references/workflows.md`: high-level route map and end-to-end workflow order.
- `references/api-reference.md`: grouped public API signatures and parameter notes.
- `references/troubleshooting.md`: cross-cutting install/import, Graphviz, Dask, parquet, network, and add-on issues.
- `references/repo-provenance.md`: source snapshot and staleness baseline.
- `references/repo-routing-metadata.json`: router placement metadata for the managed repo skill registry.

## Shared Script

- `scripts/featuretools_smoke.py`: run this small cross-cutting smoke when you need a quick install/import/DFS/selection/serialization sanity check.

## Common Decisions

- Use `load_mock_customer(return_entityset=True)` as the default demo dataset; treat the other demo loaders as optional or network-backed.
- Treat `graph_feature` and `EntitySet.plot` as optional visualization workflows when Graphviz is not installed.
- Treat `n_jobs > 1` and `dask_kwargs` as optional Dask-backed flows; base CPU DFS remains the default path.
- Treat `to_parquet` as optional and pyarrow-gated; use `to_pickle` or `to_csv` when parquet support is unavailable.
- Treat the SQL, premium, NLP, autonormalize, and sklearn extras as separate add-on surfaces unless the user explicitly asks for them.
- There is no separate CLI entry point to memorize; the package is used through Python APIs and bundled smoke scripts.

## Safety And Self-Containment

Do not reference the original repository checkout from runtime guidance. Keep instructions, examples, and helper scripts inside this skill tree so future agents can use it after the source checkout is gone.
