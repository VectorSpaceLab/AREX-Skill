---
name: experimental-imaging
description: "Use Squidpy experimental SpatialData image APIs for tissue masks,
  tiling, image QC, stain normalization, feature extraction, and tiling-artifact
  QC/stitching."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# Squidpy Experimental Imaging

Use this sub-skill when a task needs `squidpy.experimental` image workflows on `SpatialData`: tissue detection, tile generation, tile-based image QC, experimental per-cell image features, stain normalization/decomposition, or tiling-artifact scoring and stitch-group annotation.

## Use This For

- Detecting tissue in `sdata.images[...]` and writing masks to `sdata.labels[...]` with `squidpy.experimental.im.detect_tissue`.
- Creating regular or Visium-spot-centered tile polygons in `sdata.shapes[...]` with `make_tiles` or `make_tiles_from_spots`.
- Computing tile-level image QC into `sdata.tables[...]` and `sdata.shapes[...]` with `experimental.im.qc_image`, then plotting with `experimental.pl.qc_image`.
- Extracting per-cell features from SpatialData images, labels, shapes, and tables with `experimental.im.calculate_image_features`.
- Fitting, applying, and validating H&E stain normalization/decomposition with `StainReference`, `ReinhardParams`, `MacenkoParams`, and `VahadaneParams`.
- Scoring segmentation tile-boundary artifacts with `experimental.tl.calculate_tiling_qc`, assigning stitch groups with `assign_stitch_groups`, and plotting with `experimental.pl.tiling_qc`.

## Route Elsewhere

- Use `image-analysis` for stable `squidpy.im.ImageContainer`, stable `sq.im.process`, stable segmentation, and stable image feature extraction.
- Use `datasets-and-io` for dataset downloads, `squidpy.datasets.*`, `squidpy.read.*`, and SpatialData sample acquisition.
- Use `visualization` for general `squidpy.pl` spatial plots and graph/statistics plotting.
- Use `graph-analysis` for spatial neighbor graphs and image-independent spatial statistics.

## Start Here

1. Read `references/experimental-workflows.md` for safe workflow order, SpatialData key contracts, and storage locations.
2. Read `references/api-reference.md` for signatures, defaults, parameter dataclasses, outputs, and plotting entry points.
3. Read `references/troubleshooting.md` when experimental API changes, scale/key ambiguity, masks, stain validation, Weka, tiling thresholds, or memory/parallelism fail.
4. Run `scripts/experimental_imaging_smoke.py --help` or the default smoke command to check imports, dataclass validation, signatures, and a tiny generated-data stain/reference path without downloads.

## Safe Minimal Pattern

```python
import squidpy as sq

sq.experimental.im.detect_tissue(
    sdata,
    image_key="image",
    scale="auto",
    new_labels_key="image_tissue",
    inplace=True,
)
sq.experimental.im.make_tiles(
    sdata,
    image_key="image",
    tissue_mask_key="image_tissue",
    tile_size=(224, 224),
    min_tissue_fraction=0.5,
    preview=False,
)
```

Treat `squidpy.experimental` APIs as volatile. Prefer explicit `image_key`, `labels_key`, `shapes_key`, `table_key`, `scale`, and `preview=False` in automation, and inspect `sdata.images`, `sdata.labels`, `sdata.shapes`, and `sdata.tables` after every in-place step.
