---
name: fg-data-profiling
description: "Guides fg-data-profiling data profiling, report generation,
  configuration, CLI, comparison, privacy, and optional Spark/notebook
  integration workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# fg-data-profiling

Use this repo skill when a task involves the `fg-data-profiling` Python package
or its public import `data_profiling`: exploratory data analysis reports,
data-quality profiling, HTML/JSON export, command-line report generation,
comparison reports, sensitive-data-safe reports, configuration, or optional
Spark/notebook integrations.

Do not use this skill as proof that the original repository checkout is present.
All runnable helpers and operational references needed by future agents are
bundled in this skill tree.

## Install and import check

For normal package usage, install the public distribution and import the current
module name:

```bash
python -m pip install -U fg-data-profiling
python - <<'PY'
import data_profiling
from data_profiling import ProfileReport, compare
print(data_profiling.__version__)
print(ProfileReport)
print(compare)
PY
```

The repository also exposes a deprecated compatibility import named
`ydata_profiling` and a legacy CLI name `pandas_profiling`; prefer the
`data_profiling` import and `data_profiling` CLI for new work.

Run [scripts/check_environment.py](scripts/check_environment.py) when you need a
safe package/import/CLI diagnostic before deciding which sub-skill to read.
Read [references/repo-provenance.md](references/repo-provenance.md) before
refreshing this skill or comparing it with a new checkout.

## Route by task

- Read [sub-skills/profiling-workflows/SKILL.md](sub-skills/profiling-workflows/SKILL.md)
  for core pandas `ProfileReport` usage, `df.profile_report()`, HTML/JSON/notebook
  output calls, time-series mode, type schemas, supported file shapes, and a
  tiny report-generation smoke helper.
- Read [sub-skills/cli-and-automation/SKILL.md](sub-skills/cli-and-automation/SKILL.md)
  for `data_profiling` / `pandas_profiling` command-line usage, supported input
  extensions, parser flags, default output naming, and automation in DAGs or IDE
  tasks.
- Read [sub-skills/configuration-and-output/SKILL.md](sub-skills/configuration-and-output/SKILL.md)
  for `Settings`, YAML config files, `PROFILE_` environment variables,
  minimal/explorative section controls, HTML assets/themes, cache invalidation,
  and serialization.
- Read [sub-skills/comparison-and-quality/SKILL.md](sub-skills/comparison-and-quality/SKILL.md)
  for comparing profile reports, sensitive-data redaction, custom samples,
  dataset metadata, data dictionaries, type schema, quality output access, and
  Great Expectations caveats.
- Read [sub-skills/integrations-and-backends/SKILL.md](sub-skills/integrations-and-backends/SKILL.md)
  for optional Spark, notebook widgets, Bytewax/streaming snapshots, interactive
  app embedding, other DataFrame libraries, PyCharm integration, optional
  dependencies, and backend readiness checks.

## Shared references

- [references/package-overview.md](references/package-overview.md) summarizes
  package identity, primary APIs, extras, migration naming, and capability
  boundaries shared across sub-skills.
- [references/troubleshooting.md](references/troubleshooting.md) covers
  cross-cutting install/import, optional dependency, data, rendering, and stale
  version issues.
- [references/development-and-maintenance.md](references/development-and-maintenance.md)
  is for maintainers editing or testing a checkout; package users usually do
  not need it.
- [references/repo-routing-metadata.json](references/repo-routing-metadata.json)
  stores structured scenario metadata for future managed repo-skill imports.

## High-value entry points

- `from data_profiling import ProfileReport, compare`
- `ProfileReport(df, minimal=True, progress_bar=False).to_file("report.html")`
- `df.profile_report(...)` after importing `data_profiling`
- `data_profiling --minimal --silent data.csv report.html`
- `profile.to_json()`, `profile.to_html()`, `profile.get_description()`
- `profile_a.compare(profile_b)` or `compare([profile_a, profile_b])`

## Backend and optional dependency honesty

The verified core scope is CPU/Pandas package usage. Spark support is a
first-class optional workflow, but it requires Java plus PySpark and was not
verified in the production environment used to create this skill. Notebook
widgets require the notebook extra and active widget support. Great Expectations
support remains in source APIs, but the public docs state that current versions
no longer support that integration; treat it as a legacy/compatibility surface
unless the user pins compatible versions.

## Default response pattern

1. Identify whether the user wants API, CLI, configuration, comparison/privacy,
   or optional integration guidance.
2. Read the matching sub-skill and its nearest references/scripts.
3. Prefer tiny local fixtures and bundled helpers for validation before running
   expensive profiles on real data.
4. Avoid source-checkout dependencies: do not tell the user to open or run
   repository examples, docs, or tests unless they explicitly ask to maintain a
   repo checkout.
5. Preserve privacy: for sensitive datasets, route to `comparison-and-quality`
   before suggesting samples, duplicates, or numeric treatment of identifiers.
