---
name: analysis-visualization
description: "Routes PyPSA result analysis, statistics, plotting,
  NetworkCollection comparisons, and temporal or spatial clustering tasks."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Analysis and Visualization

Use this route when you need to inspect PyPSA networks, summarize results, compare scenarios, or present outputs as static or interactive charts and maps.

## Start here

- [references/statistics-reference.md](references/statistics-reference.md) — metrics, filters, custom groupers, solved-versus-unsolved behavior, and NetworkCollection statistics.
- [references/plotting-reference.md](references/plotting-reference.md) — static and interactive charts, `n.plot.map`, `n.plot.iplot`, and `n.plot.explore`.
- [references/clustering-collections.md](references/clustering-collections.md) — temporal resampling/downsampling/segmentation, spatial busmaps, and NetworkCollection comparison limits.
- [references/troubleshooting.md](references/troubleshooting.md) — empty statistics, plot backend issues, optional dependency skips, and collection alignment problems.
- [scripts/pypsa_analysis_smoke.py](scripts/pypsa_analysis_smoke.py) — tiny headless smoke for statistics, plots, and NetworkCollection comparison.
- [scripts/pypsa_clustering_smoke.py](scripts/pypsa_clustering_smoke.py) — tiny smoke for temporal clustering plus optional spatial clustering.

## Use this route for

- `n.stats` / `n.statistics` metrics, filters, groupers, and custom grouper registration.
- Static or interactive statistics plots.
- Static network maps with `n.plot.map` and interactive maps with `n.plot.iplot` or `n.plot.explore`.
- Temporal clustering via resample, downsample, or segment.
- Spatial clustering via busmaps and clustered-network aggregation.
- Scenario comparison with `NetworkCollection`.

## Do not use this route for

- Building or fixing the underlying network structure and component tables.
- Importing or exporting network data.
- Running optimization or power-flow setup.

## Quick rules of thumb

- If the network is unsolved, start with input-side metrics such as installed capacity; solve-dependent metrics can be empty until optimization or power-flow has run.
- For headless static plots, use the bundled smoke script or set Matplotlib to an off-screen backend.
- For missing optional dependencies, read the troubleshooting reference before trying to force-install extras.
- For collection comparisons, keep scenario names explicit and align snapshots or periods whenever you need direct time-series comparison.

## Typical questions this route answers

- "Why are my statistics empty?"
- "How do I group by carrier, bus carrier, country, or a custom grouper?"
- "How do I draw a headless bar, area, or map plot?"
- "How do I compare two scenario networks?"
- "How do I resample, downsample, or segment snapshots?"
- "How do I cluster buses with or without scikit-learn?"
