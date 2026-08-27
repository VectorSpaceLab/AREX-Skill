---
name: image-analysis
description: "Use stable Squidpy image APIs for ImageContainer storage,
  processing, segmentation, and AnnData image-feature extraction."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# Squidpy Image Analysis

Use this sub-skill for stable `squidpy.im` workflows: create `ImageContainer` objects, manage image layers, process images, segment masks, crop around AnnData observations, and calculate image-derived features.

## Use This For

- Constructing `sq.im.ImageContainer` from arrays, dask arrays, image files, Zarr/NetCDF stores, or AnnData spatial image metadata.
- Applying `sq.im.process` with smoothing, grayscale conversion, custom callbacks, lazy execution, chunks, and explicit output layer names.
- Running `sq.im.segment` with watershed, `SegmentationWatershed`, `SegmentationCustom`, or custom callables.
- Computing image-derived AnnData features with `sq.im.calculate_image_features`, including summary, histogram, texture, segmentation, and custom features.
- Debugging layer names, `(y, x, z, channels)` dimensions, channel selection, crop geometry, image scale, lazy arrays, chunks, and memory behavior.

## Route Elsewhere

- Use `datasets-and-io` for `squidpy.datasets`, `squidpy.read.*`, Visium/Vizgen/Nanostring loading, and AnnData spatial metadata setup.
- Use `experimental-imaging` for `squidpy.experimental.im`, SpatialData tiling, tissue detection, stain normalization, image QC, stitching, and tile-level feature extraction.
- Use `visualization` for image overlays, segmentation overlays, `sq.pl.spatial_scatter`, and `sq.pl.spatial_segment`.
- Use `graph-analysis` for spatial neighbor graphs and image-independent spatial statistics.

## Start Here

1. Read `references/image-workflows.md` for practical image-layer, processing, segmentation, crop, and feature recipes.
2. Read `references/api-reference.md` for stable signatures, copy behavior, feature storage, and model contracts.
3. Read `references/troubleshooting.md` when dimensions, layers, channel axes, segmentation masks, crops, features, chunks, or memory fail.
4. Run `scripts/image_container_smoke.py --help` or the default smoke command to check a local Squidpy install with generated in-memory data only.

## Safe Minimal Pattern

```python
import numpy as np
import squidpy as sq

arr = np.zeros((32, 32, 3), dtype=np.float32)
arr[8:20, 10:22, 0] = 1.0
img = sq.im.ImageContainer(arr, layer="image", lazy=False, scale=1.0)
sq.im.process(img, layer="image", method="smooth", sigma=[1, 1, 0, 0], layer_added="image_smooth")
sq.im.segment(img, layer="image_smooth", method="watershed", channel=0, thresh=0.2, layer_added="segmentation")
```

Keep reusable code explicit: name `layer` and `layer_added`, validate `list(img)` after each mutation, select a single watershed channel, and use `copy=True` when the caller needs a returned container or feature table instead of in-place mutation.
