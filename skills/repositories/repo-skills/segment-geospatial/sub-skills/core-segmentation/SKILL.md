---
name: core-segmentation
description: "Routes SamGeo SAM1 and SAM2 geospatial segmentation workflows
  including automatic masks, point and box prompts, batch or video prediction,
  and raster/vector outputs."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Core segmentation with `SamGeo` and `SamGeo2`

Use this sub-skill for original SAM and SAM2 package workflows: GeoTIFF or image
segmentation, automatic mask generation, prompt-based masks, SAM2 batches or
videos, and converting masks to geospatial vectors.

## Read this when

- The user names `SamGeo`, `samgeo.SamGeo`, `samgeo.samgeo.SamGeo`, SAM1,
  `vit_h`, `vit_l`, or `vit_b`.
- The user names `SamGeo2`, SAM2, `sam2-hiera-*`, SAM2 video prediction, or
  batch prompt prediction.
- The task starts with an existing GeoTIFF, PNG/JPEG, map tile bounding box, or
  vector prompt file and needs masks or vector outputs.
- The user is confused about `point_crs`, band selection, foreground/unique
  masks, or when to call `set_image()` before `predict()`.

## Route elsewhere

- SAM3/SAM3.1 text, tiled, instance, or video tracking workflows: read
  [samgeo3-workflows](../samgeo3-workflows/SKILL.md).
- Mostly CRS/raster/vector helper work without model inference: read
  [geospatial-utilities](../geospatial-utilities/SKILL.md).
- FastSAM, HQ-SAM, LangSAM, captioning, detectree2, or FER notes: read
  [specialized-models](../specialized-models/SKILL.md).
- HTTP serving or curl requests: read [api-server](../api-server/SKILL.md).

## Core decision sequence

1. Verify the environment with the root `scripts/check_install.py`; include
   `--require-cuda` if the user expects GPU inference.
2. Decide `SamGeo` vs `SamGeo2`:
   - `SamGeo`: original SAM checkpoints (`vit_h`, `vit_l`, `vit_b`), simple
     automatic or prompt workflows.
   - `SamGeo2`: SAM2 Hiera model ids, batch prompt prediction, video workflows,
     or newer SAM2 mask generation.
3. Prepare imagery and prompts. For GeoTIFFs, inspect CRS and bands first. For
   multi-band imagery, pass `bands=[r, g, b]` when reading or setting images.
4. For automatic masks, construct the model with `automatic=True` and call
   `generate(source, output=...)`.
5. For prompt masks, construct with `automatic=False`, call `set_image(...)`,
   then `predict(...)` with points, boxes, labels, and optional CRS parameters.
6. Convert or validate outputs with `tiff_to_gpkg`, `tiff_to_geojson`, or the
   utilities sub-skill after masks are written.

## References and scripts

- [workflows.md](references/workflows.md) has step-by-step SAM1/SAM2 recipes,
  including automatic masks, prompts, video, outputs, and validation steps.
- [api-reference.md](references/api-reference.md) records verified signatures,
  model ids, and key parameter meanings.
- [troubleshooting.md](references/troubleshooting.md) covers checkpoint,
  coordinate, CRS, empty-mask, and SAM2 dependency failures.
- [scripts/core_smoke.py](scripts/core_smoke.py) safely imports `SamGeo` and
  `SamGeo2`, prints method signatures, and reports device availability without
  downloading model weights.

## Native validation candidates

Use these after full skill integration, not during planning:

- `tests/test_samgeo3.py` belongs to the SAM3 sub-skill, not here.
- `tests/test_common.py` local raster/image-prep cases validate shared helpers
  used by this sub-skill.
- `tests/test_samgeo.py` is realistic evidence for SAM1 automatic/prompt masks
  but downloads map tiles and needs model checkpoints; run only if network and
  model assets are explicitly authorized.

## Output expectations

- Mask raster outputs should exist at the requested path and preserve geospatial
  metadata when the source is georeferenced.
- Vector outputs should be valid GPKG, Shapefile, or GeoJSON. Empty masks should
  become valid empty vector layers rather than crashes.
- Prompt outputs should be checked visually or by mask statistics before running
  simplification, smoothing, or large batch/vector conversion.
