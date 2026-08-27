# Squidpy Troubleshooting

Use this root guide for cross-cutting issues. For workflow-specific failures, read the nearest sub-skill troubleshooting reference.

## Install Or Import Fails

- Check the runtime Python version against Squidpy package metadata. Current metadata requires Python `>=3.12`.
- Prefer `pip install squidpy` or `conda install -c conda-forge squidpy` in a fresh environment when compiled scientific dependencies conflict.
- Run `python -m pip check` after installation when imports fail or compiled dependencies were upgraded.
- If `import squidpy` raises errors from `spatialdata`, `scikit-image`, `numba`, `imagecodecs`, `tifffile`, or `matplotlib`, resolve the dependency stack first; most Squidpy APIs import several scientific packages eagerly.
- Optional `leidenalg`/`spatialleiden` packages are only needed for workflows that explicitly use niche flavors requiring them.

## Dataset Download Or Cache Problems

- Treat `sq.datasets.*` helpers as network/cache operations unless files are already present.
- Pass explicit `path`, `base_dir`, or `folderpath` values for reproducible cache behavior.
- For offline workflows, prefer `sq.read.*`, `anndata.read_h5ad`, or `spatialdata.read_zarr` over curated dataset helpers.
- Do not depend on repository CI data-download helpers in runtime workflows; use user-supplied files or documented public dataset loaders.

## AnnData And SpatialData Keys Do Not Match

- Confirm `AnnData` has numeric `adata.obsm['spatial']` with one row per observation.
- Confirm categorical columns before graph statistics: `adata.obs[cluster_key]` should be `category` for many group-based functions.
- For image-aware plotting, confirm `adata.uns['spatial'][library_id]['images']` and `['scalefactors']` exist; graph-only workflows can run without image metadata.
- For `SpatialData`, inspect available `sdata.tables`, `sdata.images`, `sdata.labels`, and `sdata.shapes`; pass explicit keys instead of relying on defaults in multi-element objects.
- Use `sub-skills/datasets-and-io/scripts/check_spatial_adata.py` for local structure checks before graph, plotting, image, or experimental routes.

## Plotting Fails In Automation

- Set a noninteractive Matplotlib backend before importing plotting libraries in headless jobs, for example `MPLBACKEND=Agg`.
- Compute required analysis outputs before plotting them: graph plots need `.uns`/`.obsp` results created by `squidpy.gr`, and `sq.pl.var_by_distance` needs a design matrix from `squidpy.tl.var_by_distance`.
- If figure comparisons differ across machines, check Matplotlib version and rendering backend; visual baselines are often version-sensitive.
- Use `return_ax=True` when you need programmatic assertions and `save=` when writing figures from scripts.

## Stable Versus Experimental Image APIs

- Use stable `squidpy.im` for `ImageContainer`, `process`, `segment`, and AnnData image-feature extraction.
- Use `squidpy.experimental` for SpatialData tissue detection, tiling, QC, stain normalization/decomposition, tiling QC, and stitch grouping.
- Experimental APIs should be called with explicit keys and conservative parameters such as `preview=False`, `n_jobs=1`, and small generated fixtures during automation.

## Deprecated Or Moved Surfaces

- Prefer mode-specific graph constructors over deprecated `sq.gr.spatial_neighbors` in new code.
- The original Squidpy napari plugin has moved to `napari-spatialdata`; route interactive visualization tasks there unless the user is maintaining legacy Squidpy code.
