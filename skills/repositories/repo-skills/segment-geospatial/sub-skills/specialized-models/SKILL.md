---
name: specialized-models
description: "Routes SamGeo optional model integrations including FastSAM,
  HQ-SAM, LangSAM/GroundingDINO text prompts, BLIP captioning, detectree2 notes,
  and FER/GDAL gaps."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Specialized model integrations

Use this sub-skill for optional model families and auxiliary workflows that sit
outside the primary `SamGeo`, `SamGeo2`, and `SamGeo3` routes.

## Read this when

- The user asks for FastSAM (`samgeo.fast_sam`) speed-oriented segmentation.
- The user asks for HQ-SAM (`samgeo.hq_sam`) high-quality masks.
- The user asks for `LangSAM`, GroundingDINO, or text prompts with SAM1/SAM2.
- The user asks for BLIP image captioning or extracting aerial features from a
  caption/image.
- The user asks about detectree2 tree crowns or FER/GDAL feature edge
  reconstruction and needs to know why those are optional/gap paths.

## Route elsewhere

- Standard SAM1/SAM2 segmentation: [core-segmentation](../core-segmentation/SKILL.md).
- SAM3 text/prompt/video/tiled workflows: [samgeo3-workflows](../samgeo3-workflows/SKILL.md).
- Raster/vector/CRS utilities: [geospatial-utilities](../geospatial-utilities/SKILL.md).
- HTTP API text/automatic/predict endpoints: [api-server](../api-server/SKILL.md).

## Before using optional models

1. Install only the extra needed for the workflow: `[fast]`, `[hq]`, `[text]`,
   `[samgeo3]`, or a selected combined set.
2. Run [scripts/optional_model_imports.py](scripts/optional_model_imports.py)
   before constructing models.
3. Confirm whether the workflow downloads model weights, Hugging Face assets,
   spaCy models, map tiles, or detectree2/Detectron2 dependencies.
4. Use one image/crop and save a simple mask before scaling to batches.

## References and scripts

- [model-overview.md](references/model-overview.md) compares FastSAM, HQ-SAM,
  LangSAM, captioning, detectree2, and FER support.
- [workflows.md](references/workflows.md) gives focused recipes for the
  optional workflows.
- [troubleshooting.md](references/troubleshooting.md) covers optional import,
  model download, `pkg_resources`, GroundingDINO, BLIP/spaCy, detectree2, and
  GDAL issues.
- [scripts/optional_model_imports.py](scripts/optional_model_imports.py) checks
  optional imports without loading weights; caption import is opt-in because it
  performs a network vocabulary fetch.

## Validation candidates

- FastSAM, HQ-SAM, LangSAM, and captioning example notebooks are evidence and
  optional native candidates; they require model/network readiness.
- detectree2 and FER are documented as optional gaps in this skill because the
  prepared environment did not install Detectron2/detectree2 or GDAL.
