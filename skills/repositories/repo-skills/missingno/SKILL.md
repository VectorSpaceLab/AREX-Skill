---
name: missingno
description: "Guides missingno missing-data visualization, nullity filtering and
  sorting, package smoke checks, and troubleshooting for pandas DataFrames."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# missingno Repo Skill

Use this skill when a task involves the Python package `missingno`, missing-data
visualization, nullity plots, or DataFrame completeness filtering/sorting. It
is an operating guide for future Researcher sessions; it is not a maintainer
checkout dependency.

## First checks

For ordinary use, install the public package and verify imports:

```bash
python -m pip install missingno
python - <<'PY'
import missingno as msno
print(msno.__version__)
print([name for name in ["matrix", "bar", "heatmap", "dendrogram", "nullity_filter", "nullity_sort"] if hasattr(msno, name)])
PY
```

Expected public API in this snapshot:

- `msno.matrix(df, ...)`
- `msno.bar(df, ...)`
- `msno.heatmap(df, ...)`
- `msno.dendrogram(df, ...)`
- `msno.nullity_filter(df, ...)`
- `msno.nullity_sort(df, ...)`

There is no verified package CLI entry point and no verified `geoplot` export in
this repository snapshot.

## Route map

| User task | Read next |
| --- | --- |
| Choose or configure a nullity matrix, bar chart, heatmap, or dendrogram | [sub-skills/visualizations/SKILL.md](sub-skills/visualizations/SKILL.md) |
| Interpret nullity correlations, dendrogram clusters, time-index frequency ticks, labels, sparklines, or headless plotting | [sub-skills/visualizations/SKILL.md](sub-skills/visualizations/SKILL.md) |
| Filter to the most/least complete columns or sort rows/columns by completeness | [sub-skills/nullity-utilities/SKILL.md](sub-skills/nullity-utilities/SKILL.md) |
| Understand `filter`, `n`, `p`, `sort`, or `axis` behavior used by plot APIs | [sub-skills/nullity-utilities/SKILL.md](sub-skills/nullity-utilities/SKILL.md) |
| Diagnose installation, import, dependency, headless plotting, no-CLI, stale-docs, or smoke-check failures | [references/troubleshooting.md](references/troubleshooting.md) |
| Edit or test the upstream repository rather than just use the package | [references/maintainer-notes.md](references/maintainer-notes.md) |
| Decide whether this generated skill is stale for a checkout | [references/repo-provenance.md](references/repo-provenance.md) |

## Shared smoke helper

Run the bundled smoke helper when an environment should be checked without
network downloads or a notebook display:

```bash
python scripts/missingno_smoke_check.py --skip-plots
MPLBACKEND=Agg python scripts/missingno_smoke_check.py --plot all --output-dir /tmp/missingno-smoke
```

The helper uses a synthetic pandas DataFrame, validates `nullity_filter` and
`nullity_sort`, then optionally renders matrix/bar/heatmap/dendrogram plots via
a headless matplotlib backend. Read the helper before adapting it:
[scripts/missingno_smoke_check.py](scripts/missingno_smoke_check.py).

## Operating boundaries

- Prefer small synthetic DataFrames for examples and diagnostics. The public
  README's collision dataset example is useful conceptually but uses network
  data and is not required for package operation.
- Keep `SKILL.md` files as routers. Use the linked references for API tables,
  examples, and troubleshooting details.
- Do not claim `inline=` or `geoplot` support for this snapshot: installed
  signatures and exports did not verify those capabilities even though older
  documentation text mentions them.
- Plotting APIs return matplotlib `Axes` objects. In scripts or CI, set
  `MPLBACKEND=Agg`, save figures explicitly, and close figures after checks.

## Public provenance and router metadata

- [references/repo-provenance.md](references/repo-provenance.md) records the
  source commit/tag, package version, dirty-state summary, and evidence paths.
- [references/repo-routing-metadata.json](references/repo-routing-metadata.json)
  contains structured metadata for a future managed repo-skill import. This run
  intentionally does not import the skill.
