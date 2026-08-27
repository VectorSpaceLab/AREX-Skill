---
name: scanpy
description: "Use for Scanpy single-cell analysis workflows: AnnData IO,
  preprocessing/QC, graph embeddings, clustering, marker genes,
  plotting/reporting, optional integrations, and Scanpy package
  troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# Scanpy Repo Skill

Use this skill when a task names Scanpy, `scanpy`, scverse single-cell analysis, AnnData-based analysis, or Scanpy APIs such as `sc.pp`, `sc.tl`, `sc.pl`, `sc.get`, `sc.datasets`, `sc.queries`, `sc.metrics`, or `sc.external`.

Scanpy is a Python toolkit for single-cell gene-expression analysis built around `anndata.AnnData`. It covers data access, preprocessing, quality control, graph construction, dimensionality reduction, clustering, trajectory inference, marker-gene testing, and visualization.

## Install and Import

- Standard import: `import scanpy as sc`.
- Current source metadata requires Python `>=3.12`.
- Base install: `pip install scanpy` or `conda install -c conda-forge scanpy`.
- Common clustering install: `pip install 'scanpy[leiden]'` or `conda install -c conda-forge scanpy python-igraph leidenalg`.
- Minimal import check: `python -c "import scanpy as sc; print(sc.__version__)"`.
- CLI check: `python -m scanpy --help`; Scanpy's built-in CLI is intentionally small and primarily exposes `settings`, while broader ecosystem commands may live in separate packages.

Read `references/troubleshooting.md` before recommending broad dependency changes. Install only the optional extra or package needed by the requested method.

## Route by Workflow

| User need | Route |
| --- | --- |
| Read/write `.h5ad`, 10x HDF5/MTX, Visium output, backed data, built-in datasets, annotation queries, or extract values from AnnData | `sub-skills/io-data-access/SKILL.md` |
| Filter cells/genes, compute QC, normalize/log transform, select HVGs, scale/regress, run PCA prep, detect doublets, or manage raw/layer/inplace behavior | `sub-skills/preprocessing-qc/SKILL.md` |
| Build neighbor graphs, run UMAP/t-SNE/diffmap/draw_graph, cluster with Leiden/Louvain, PAGA/DPT trajectories, marker ranking, gene scoring, ingest, or graph metrics | `sub-skills/graph-embedding-analysis/SKILL.md` |
| Produce Scanpy plots, save figures headlessly, customize dot/matrix/violin/embedding/spatial plots, or debug color/layout/Matplotlib settings | `sub-skills/plotting-reporting/SKILL.md` |
| Choose optional extras, use `scanpy.external`, diagnose missing optional dependencies, Dask-backed arrays, or RAPIDS/GPU handoffs | `sub-skills/external-integrations/SKILL.md` |

## Cross-Workflow Order

1. Start with `io-data-access` to load data into an `AnnData` object and preserve important `obs`, `var`, `layers`, `.raw`, `.obsm`, `.obsp`, and `.uns` fields.
2. Use `preprocessing-qc` for QC, filtering, normalization, HVG selection, scaling/regression, PCA, and other matrix transformations.
3. Use `graph-embedding-analysis` after preprocessing to build neighbors and compute embeddings, clusters, trajectories, markers, scores, and graph metrics.
4. Use `plotting-reporting` after the relevant annotations exist; plotting functions usually expect keys in `.obs`, `.var`, `.obsm`, `.uns`, `.raw`, or `.layers` created by earlier steps.
5. Use `external-integrations` whenever a method requires optional packages, Dask support, RAPIDS/GPU acceleration, or external wrappers.

## Shared Rules

- Keep raw counts before normalization, commonly in `adata.layers["counts"]`; use `.raw` deliberately for downstream marker plotting or differential expression.
- Prefer public APIs documented under `scanpy.pp`, `scanpy.tl`, `scanpy.pl`, `scanpy.get`, `scanpy.datasets`, `scanpy.queries`, `scanpy.metrics`, and `scanpy.external`.
- Check `inplace`, `copy`, `layer`, `use_raw`, `neighbors_key`, `key_added`, and output keys before debugging missing results.
- Avoid installing all optional extras. Choose narrow extras such as `leiden`, `louvain`, `skmisc`, `scrublet`, `scanorama`, `magic`, `dask`, or `plotting` only when the workflow needs them.
- For reproducible agent checks, run `scripts/run_scanpy_skill_smokes.py` or the nearest sub-skill smoke script instead of broad upstream test suites.

## References and Helpers

- `references/repo-provenance.md` records the source snapshot and evidence paths used to create this skill; read it before deciding whether a checkout needs refresh.
- `references/troubleshooting.md` covers shared install/import, optional dependency, AnnData state, and workflow-routing failures.
- `scripts/run_scanpy_skill_smokes.py` runs the safe bundled smoke scripts in the current Python environment.
