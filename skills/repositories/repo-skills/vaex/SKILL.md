---
name: vaex
description: "Use Vaex for lazy out-of-core DataFrames, file conversion,
  expressions, analytics, visualization, ML pipelines, servers, and CLI/settings
  workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Vaex Repo Skill

Use this repo skill when a task names Vaex, `vaex`, out-of-core Python DataFrames, lazy tabular analytics, memory-mapped HDF5/Arrow/Parquet data, Vaex expressions, virtual columns, fast groupby/statistics, Vaex visualization/Jupyter widgets, `vaex-ml`, `vaex server`, or the `vaex` CLI/settings surface.

## Start Here

- Read [references/repo-provenance.md](references/repo-provenance.md) before deciding whether this skill is current for a Vaex checkout or whether `refresh-repo-skill` is needed.
- Read [references/source-evidence-map.md](references/source-evidence-map.md) to see which source, docs, tests, scripts, and optional surfaces informed this self-contained skill.
- Read [references/installation-and-packages.md](references/installation-and-packages.md) when choosing between the Vaex meta package and component packages such as `vaex-core`, `vaex-hdf5`, `vaex-ml`, `vaex-server`, `vaex-viz`, `vaex-jupyter`, and `vaex-astro`.
- Read [references/performance-and-execution.md](references/performance-and-execution.md) for lazy/out-of-core execution, memory mapping, caches, progress, and thread settings that affect several workflows.
- Read [references/troubleshooting.md](references/troubleshooting.md) for cross-cutting install/import, optional dependency, source-build, cache/example-data, and version-specific issues.
- Run [scripts/check_vaex_environment.py](scripts/check_vaex_environment.py) to inspect an installed Vaex package set without depending on a source checkout.

## Installation and Import

Prefer a package-manager install for ordinary use:

```bash
python -m pip install vaex
# or
conda install -c conda-forge vaex
python - <<'PY'
import vaex
print(vaex.__version__)
df = vaex.from_arrays(x=[1, 2, 3])
print(df.sum('x'))
PY
```

Install component packages only when you intentionally want a narrower environment, for example `vaex-core vaex-hdf5 vaex-viz vaex-ml vaex-server`. Avoid source builds unless the task is specifically about contributing to Vaex or diagnosing compiled-extension build failures.

## Route by Task

| User task | Read this sub-skill |
| --- | --- |
| Create or inspect a Vaex DataFrame, write filters/selections, add virtual columns, debug non-identifier column names, avoid accidental materialization | [dataframe-core](sub-skills/dataframe-core/SKILL.md) |
| Open, convert, export, and validate CSV, Arrow, Parquet, Feather, HDF5, Pandas/Arrow tables, local astro formats, or cloud/TAP paths | [io-conversion](sub-skills/io-conversion/SKILL.md) |
| Use expressions, selections, string/datetime/struct/geo accessors, statistics, groupby/binby grids, joins, sorting, uniques, and analytic validation | [expressions-analytics](sub-skills/expressions-analytics/SKILL.md) |
| Build `vaex-ml` transformations, train/test splits, sklearn wrappers, pipelines, state transfer, PCA/KMeans, or optional model integrations | [ml-pipelines](sub-skills/ml-pipelines/SKILL.md) |
| Plot histograms, heatmaps, scatter plots, expression plots, static Matplotlib outputs, Jupyter widgets, or progress displays | [visualization-jupyter](sub-skills/visualization-jupyter/SKILL.md) |
| Start or inspect `vaex server`, REST or PNG plot endpoints, WebSocket remote DataFrames, tokens, base URLs, local TestClient checks, or optional GraphQL | [serving-remote](sub-skills/serving-remote/SKILL.md) |
| Use the `vaex` console, `vaex open`/`stat` checks, aliases, settings YAML/JSON/env vars, or command-side risk flags | [cli-settings](sub-skills/cli-settings/SKILL.md) |

## Core Rules

- Treat Vaex as lazy and out-of-core by default. Prefer expressions, virtual columns, selections, filters, aggregations, and chunked evaluation over full `.values`, `to_pandas_df`, or NumPy conversion.
- Use bracket access for non-identifier column names: `df['column with spaces']` rather than attribute access or fragile expression strings.
- Convert repeat-query CSV workflows to Vaex-friendly HDF5/Arrow/Parquet when the data is large or repeatedly analyzed; validate row counts, columns, and a small aggregate after conversion.
- Keep plotting separate from analytics: compute/count/group in `expressions-analytics`, then render in `visualization-jupyter`.
- Treat `vaex server` as a service boundary. Use explicit `name=path` dataset names, prefer loopback for tests, and do not start public listeners without approval.
- Treat optional cloud, TAP, GraphQL, TensorFlow, Jupyter frontend, GUI, and benchmark workflows as opt-in; do not install broad extras or run network/credentialed checks unless the user asks.

## Source Build Guardrails

For normal Vaex API work, do not build from source. Source builds need recursive submodules, compiled C++ extensions, PCRE headers/libraries, Python-version-compatible NumPy/build tools, and often conda-forge-style dependencies. If a user explicitly needs source development or build repair, read [references/installation-and-packages.md](references/installation-and-packages.md) and ask before mutating host build tools or a user-owned environment.

## Self-Containment

This skill distills Vaex repository docs, source, tests, scripts, and installed-package inspection into bundled references and scripts. Runtime instructions here do not require access to the original Vaex checkout.
