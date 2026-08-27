---
name: squidpy
description: "Use Squidpy for spatial omics data loading, graph statistics,
  image analysis, visualization, tool workflows, and experimental SpatialData
  imaging."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# Squidpy

Use this repo skill when a task involves Squidpy, the scverse toolkit for spatial molecular and spatial single-cell analysis in Python. Squidpy builds on AnnData, Scanpy, SpatialData, scikit-image, and Matplotlib to load spatial data, build spatial neighbor graphs, compute spatial statistics, work with tissue images, and render spatial plots.

## Start Here

1. Confirm Squidpy is importable with `python -c "import squidpy as sq; print(sq.__version__)"` or run `scripts/squidpy_import_check.py --json`.
2. Choose the nearest sub-skill from the route map below.
3. Use the linked sub-skill references for API signatures, required data layout, validation checks, and troubleshooting.
4. Keep workflows explicit: name `spatial_key`, `library_id`, `table_key`, `image_key`, `labels_key`, `connectivity_key`, and output keys when ambiguity is possible.

## Route Map

- Use `sub-skills/datasets-and-io/SKILL.md` for `squidpy.datasets`, `squidpy.read.*`, `.h5ad`/SpatialData validation, Visium/Vizgen/Nanostring layouts, cache behavior, and download avoidance.
- Use `sub-skills/graph-analysis/SKILL.md` for `squidpy.gr` graph builders, spatial neighbor graphs, graph statistics, ligand-receptor analysis, Moran/Geary autocorrelation, Ripley statistics, Sepal, niches, and custom graph builders.
- Use `sub-skills/image-analysis/SKILL.md` for stable `squidpy.im` `ImageContainer` workflows, image processing, segmentation, and AnnData image-feature extraction.
- Use `sub-skills/visualization/SKILL.md` for `squidpy.pl` spatial overlays, segmentation plots, graph/statistic plots, ligand-receptor heatmaps, and variation-by-distance plots.
- Use `sub-skills/tools-workflows/SKILL.md` for `squidpy.tl.sliding_window`, `squidpy.tl.var_by_distance`, design-matrix outputs, and plotting handoffs.
- Use `sub-skills/experimental-imaging/SKILL.md` for `squidpy.experimental` SpatialData tissue detection, tiling, image QC, stain workflows, experimental feature extraction, tiling QC, stitching, and experimental plots.

## Common Workflow Order

- Load or validate data first with `datasets-and-io`; graph, plotting, image, and experimental workflows all depend on correct coordinate/table/image keys.
- Build graph outputs with `graph-analysis` before using graph plot functions in `visualization`.
- Use stable `image-analysis` for `ImageContainer` tasks; use `experimental-imaging` only when the task is explicitly SpatialData-based or needs experimental tissue/tiling/stain/QC APIs.
- Use `tools-workflows` to create sliding-window assignments or distance-to-anchor design matrices, then route plot styling to `visualization`.

## What To Read

- `references/package-overview.md` for public modules, object conventions, package requirements, and workflow ownership.
- `references/troubleshooting.md` for install/import issues, optional dependencies, dataset downloads, AnnData/SpatialData key mismatches, plotting backends, and deprecated napari-plugin guidance.
- `references/repo-provenance.md` for the repository snapshot and evidence paths used to generate this skill.
- `references/repo-routing-metadata.json` for structured managed-router scenario placement.

## Safe Defaults

- Prefer explicit local paths and keys over global settings or inferred defaults.
- Treat `sq.datasets.*` as potentially networked; local `sq.read.*` and saved `.h5ad`/SpatialData reads are safer for offline work.
- Prefer mode-specific graph constructors such as `sq.gr.spatial_neighbors_knn`, `sq.gr.spatial_neighbors_radius`, `sq.gr.spatial_neighbors_delaunay`, and `sq.gr.spatial_neighbors_grid`; avoid new code built around deprecated `sq.gr.spatial_neighbors`.
- Use `n_jobs=1`, small permutation counts, `preview=False`, and noninteractive Matplotlib backends for smoke tests and automation.
- Route experimental APIs carefully; `squidpy.experimental` surfaces can change faster than stable `sq.im`, `sq.gr`, `sq.tl`, and `sq.pl` APIs.
