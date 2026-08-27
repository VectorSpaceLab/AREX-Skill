---
name: geospatial-utilities
description: "Guides SamGeo geospatial utility workflows for CRS checks, tile
  downloads, image preparation, raster/vector conversion, split/merge, region
  analysis, and UTM helpers."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Geospatial utilities

Use this sub-skill when the task is primarily raster/vector preparation,
coordinate handling, CRS troubleshooting, data conversion, or safe validation
around `samgeo.common` rather than direct model inference.

## Read this when

- The user needs `tms_to_geotiff`, `image_to_cog`, `reproject`,
  `raster_to_vector`, `split_raster`, `merge_rasters`, `regularize`,
  `smooth_vector`, or `region_groups`.
- The user asks how to prepare multi-band GeoTIFFs for SAM, choose `bands`, or
  inspect raster metadata/statistics.
- The task involves converting prompt coordinates or boxes from CRS coordinates
  to pixel coordinates.
- The user is debugging CRS distortion, empty vector outputs, out-of-bounds
  prompts, tile downloads, or vector driver issues.

## Route elsewhere

- Model-specific automatic/prompt segmentation: [core-segmentation](../core-segmentation/SKILL.md).
- SAM3 tiled, text, or video workflows: [samgeo3-workflows](../samgeo3-workflows/SKILL.md).
- Optional model wrappers and captioning: [specialized-models](../specialized-models/SKILL.md).
- HTTP API request/response details: [api-server](../api-server/SKILL.md).

## Utility workflow order

1. Inspect the raster first: CRS, transform, width/height, band count, dtype,
   nodata, and stats.
2. Normalize imagery to uint8 RGB for SAM with `read_image_for_sam` or
   `prepare_image_for_sam`.
3. For map-tile workflows, keep bounding boxes small and confirm provider terms.
4. After segmentation, inspect mask values before vectorization.
5. Convert masks to vector formats, then optionally simplify, regularize, or
   smooth geometries.
6. Reproject only when the user explicitly wants a different CRS for downstream
   visualization or analysis.

## References and scripts

- [workflows.md](references/workflows.md) gives data-preparation and conversion
  recipes for common SamGeo support tasks.
- [api-reference.md](references/api-reference.md) records verified helper
  signatures and input/output assumptions.
- [troubleshooting.md](references/troubleshooting.md) covers CRS, bands,
  all-zero masks, tile download, GDAL/vector, and large-raster failures.
- [scripts/mini_geotiff_roundtrip.py](scripts/mini_geotiff_roundtrip.py)
  creates a tiny GeoTIFF and empty mask, then validates image prep and vector
  conversion without network access.

## Native validation candidates

- `tests/test_utmconv.py` is the safe native case for UTM math.
- The local subset of `tests/test_common.py` validates image prep, multi-band
  reads, and empty-mask vectorization.
- Network examples such as map tile downloads are optional and should be run
  only when network/provider access is authorized.
