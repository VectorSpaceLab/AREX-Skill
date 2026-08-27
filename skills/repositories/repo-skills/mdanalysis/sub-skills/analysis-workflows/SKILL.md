---
name: analysis-workflows
description: "Run MDAnalysis analysis classes, custom AnalysisBase workflows,
  numerical distance analyses, and analysis backend validation."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# MDAnalysis Analysis Workflows

Use this sub-skill when the task is to run built-in `MDAnalysis.analysis` modules, interpret `analysis.results`, convert frame loops into `AnalysisBase`, or debug analysis backends and numerical outputs.

## Route First

- For loading files, building synthetic `Universe` objects, attaching trajectories, or writer setup, read `../universe-io/SKILL.md` first.
- For atom selection language, empty selections, updating selections, topology attributes, masses, charges, bonds, or custom attributes, read `../selections-topology/SKILL.md` first.
- For on-the-fly transformations, PBC unwrapping/centering before analysis, or writing transformed trajectories, read `../transformations-writing/SKILL.md` first.

## Use This For

- Running `AnalysisBase.run(start=..., stop=..., step=...)` or `run(frames=...)` and validating `frames`, `times`, `n_frames`, and `results`.
- Choosing and interpreting RMSD, RMSF, alignment, contacts, distance arrays, RDF, hydrogen bonds, PCA, MSD, leaflet, and density analyses.
- Writing a small custom `AnalysisBase` subclass with deterministic result arrays and optional split-apply-combine aggregation.
- Selecting safe analysis backends: default serial execution, supported multiprocessing or dask backends, and distance-function backends.
- Diagnosing analysis-specific failures such as empty selections, mass mismatches, missing charges/bonds, PBC boxes, deprecated result aliases, and result-shape confusion.

## References

- `references/analysis-api.md` summarizes verified signatures, result containers, result shapes, and backend rules.
- `references/recipes.md` gives practical workflows for built-in analyses and custom `AnalysisBase` implementations.
- `references/troubleshooting.md` maps common analysis symptoms to concrete recovery steps.
- `scripts/analysis_smoke_check.py` runs a tiny synthetic custom analysis and distance-array validation without repo test data.

## Safe Validation

Run the bundled smoke check in an environment where `MDAnalysis` is installed:

```bash
python scripts/analysis_smoke_check.py
```

Expected output includes `PASS custom AnalysisBase frames/results`, `PASS PBC distance_array preallocated result`, and `PASS frames/start conflict validation`.
