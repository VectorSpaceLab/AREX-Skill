# Squidpy Package Overview

Squidpy is a spatial molecular analysis toolkit in the scverse ecosystem. It combines AnnData tables, SpatialData objects, spatial coordinate graphs, image containers, and plotting utilities.

## Public Modules

| Module | Owns | Route |
| --- | --- | --- |
| `squidpy.datasets` | Download/cache helpers for curated AnnData, image, Visium, and SpatialData examples | `sub-skills/datasets-and-io/SKILL.md` |
| `squidpy.read` | Local Visium, Vizgen, and Nanostring/CosMx readers | `sub-skills/datasets-and-io/SKILL.md` |
| `squidpy.gr` | Spatial graph construction, graph statistics, point-pattern tests, ligand-receptor analysis, niches, Sepal, custom graph builders | `sub-skills/graph-analysis/SKILL.md` |
| `squidpy.im` | Stable `ImageContainer`, image processing, segmentation, image feature extraction | `sub-skills/image-analysis/SKILL.md` |
| `squidpy.pl` | Spatial, segmentation, graph/statistic, ligand-receptor, extraction, and variation-by-distance plots | `sub-skills/visualization/SKILL.md` |
| `squidpy.tl` | Sliding windows and variation-by-distance design matrices | `sub-skills/tools-workflows/SKILL.md` |
| `squidpy.experimental` | SpatialData image masks, tiles, QC, stain workflows, experimental features, tiling QC/stitching, experimental plots | `sub-skills/experimental-imaging/SKILL.md` |

## Installation Facts

- Package distribution and import name: `squidpy`.
- Current package metadata declares Python `>=3.12`.
- Public install commands are `pip install squidpy` or `conda install -c conda-forge squidpy`.
- Optional `leiden` dependencies (`leidenalg`, `spatialleiden`) are relevant for some niche workflows, not for ordinary data loading, graph construction, plotting, or stable image workflows.
- Interactive visualization previously associated with Squidpy has moved to `napari-spatialdata`; do not route new napari-plugin tasks to Squidpy unless the user explicitly asks about legacy behavior.

## Core Object Conventions

- `AnnData` inputs usually need coordinates in `adata.obsm['spatial']`.
- Squidpy image-aware plotting often expects `adata.uns['spatial'][library_id]['images']` and `['scalefactors']` entries.
- Graph constructors write connectivity and distance matrices to `.obsp`, usually `spatial_connectivities` and `spatial_distances`, plus parameters under `.uns['spatial']` unless `key_added` changes the prefix.
- Many graph statistics require categorical `adata.obs[cluster_key]` and an existing connectivity key.
- `SpatialData` workflows require explicit `table_key`, `image_key`, `labels_key`, `shapes_key`, `scale`, or `elements_to_coordinate_systems` when more than one candidate exists.
- Stable image workflows use `squidpy.im.ImageContainer`; experimental SpatialData image workflows use `squidpy.experimental` and store results in `sdata.images`, `sdata.labels`, `sdata.shapes`, or `sdata.tables`.

## Workflow Ownership

- Data loading/validation is upstream of every other route.
- Graph analysis owns computing graph/statistical outputs; visualization owns rendering those outputs.
- Stable image analysis owns `ImageContainer` transformations and feature extraction into AnnData; experimental imaging owns SpatialData tissue masks, tiles, QC, stain workflows, and tiling/stitch annotations.
- Tool workflows own design-matrix creation and sliding-window assignments; visualization owns plot styling after those outputs exist.

## Safe Smoke Strategy

Use the bundled scripts for lightweight validation in an environment where Squidpy is installed:

```bash
python scripts/squidpy_import_check.py --json
python sub-skills/datasets-and-io/scripts/check_spatial_adata.py --help
python sub-skills/graph-analysis/scripts/graph_smoke.py --quiet
python sub-skills/image-analysis/scripts/image_container_smoke.py --skip-features
python sub-skills/visualization/scripts/plotting_smoke.py --quiet
python sub-skills/tools-workflows/scripts/var_by_distance_smoke.py --quiet
python sub-skills/experimental-imaging/scripts/experimental_imaging_smoke.py --quiet
```

Prefer generated-data smokes for automation. Treat dataset downloads, full native test suites, image-baseline comparisons, and large slide workflows as verification activities rather than first-line runtime checks.
