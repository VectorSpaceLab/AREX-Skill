# Shared Scanpy Troubleshooting

Read this when a Scanpy task fails before the problem clearly belongs to one sub-skill. Prefer narrow fixes and inspect AnnData state before reinstalling broad optional stacks.

## Install and Import

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ModuleNotFoundError: scanpy` | Scanpy is not installed in the active Python | Install `scanpy`, then run `python -c "import scanpy as sc; print(sc.__version__)"`. |
| Python version resolution fails | Current Scanpy source metadata requires Python `>=3.12` | Use a Python version supported by the package metadata and reinstall in that environment. |
| `python -m scanpy --help` works but lacks analysis commands | Scanpy's built-in CLI is intentionally small | Use Python APIs from this skill for workflows; only install ecosystem CLI packages when the user explicitly needs them. |
| Clustering fails with missing `igraph`, `leidenalg`, or Louvain packages | Core Scanpy is installed without clustering extras | Install the narrow dependency: `scanpy[leiden]`, `scanpy[louvain]`, or matching conda packages. |
| `highly_variable_genes(..., flavor="seurat_v3")` fails | `scikit-misc` is missing or the input is not raw counts | Install `scanpy[skmisc]` or `scikit-misc`, and run Seurat v3 HVG on raw count data, often `layer="counts"`. |
| Optional external method fails to import | The specific external package is missing | Run `sub-skills/external-integrations/scripts/check_scanpy_optional_deps.py --feature FEATURE --json`, then install only the needed extra/package. |
| Plotting fails on a server or CI runner | Interactive Matplotlib backend is unavailable | Use the plotting sub-skill, set a non-interactive backend, call plotting functions with `show=False`, and save figures explicitly. |

## AnnData State Checks

- If later steps cannot find genes, groups, embeddings, neighbors, rank-gene results, or colors, inspect `.var_names`, `.obs`, `.var`, `.layers`, `.raw`, `.obsm`, `.obsp`, and `.uns`.
- If normalized data overwrote raw counts, restore counts from input or keep future raw counts in `adata.layers["counts"]` before `sc.pp.normalize_total` and `sc.pp.log1p`.
- If UMAP, PAGA, DPT, or graph metrics use the wrong graph, pass the same `neighbors_key` used in `sc.pp.neighbors(key_added=...)`.
- If `inplace=False` returns data frames or arrays but the AnnData object is unchanged, assign the returned values or call with the default mutating behavior.
- If a function unexpectedly consumes memory, check sparse/dense behavior and avoid operations that densify large matrices, especially `sc.pp.scale(zero_center=True)` and `sc.pp.regress_out`.

## Routing Checks

- IO/data layout problems belong in `sub-skills/io-data-access/SKILL.md`.
- Matrix transformation, QC, HVG, PCA-prep, and Scrublet preprocessing problems belong in `sub-skills/preprocessing-qc/SKILL.md`.
- Neighbor graph, clustering, trajectory, marker ranking, scoring, ingest, and metrics problems belong in `sub-skills/graph-embedding-analysis/SKILL.md`.
- Plot saving, headless rendering, color/palette, and visual layout problems belong in `sub-skills/plotting-reporting/SKILL.md`.
- Optional dependency, external wrapper, Dask, and RAPIDS/GPU questions belong in `sub-skills/external-integrations/SKILL.md`.

## Safe Validation

Run the root smoke orchestrator when an environment should support the generated skill:

```bash
python scripts/run_scanpy_skill_smokes.py
```

The smoke scripts use tiny synthetic AnnData fixtures, avoid downloads, and report optional-dependency skips separately from hard failures.
