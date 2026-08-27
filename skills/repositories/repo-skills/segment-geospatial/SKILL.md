---
name: segment-geospatial
description: "Guides segment-geospatial/SamGeo workflows for geospatial SAM
  segmentation, SAM2/SAM3 model variants, REST API serving, raster/vector IO,
  and optional text or caption model integrations."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# segment-geospatial (SamGeo)

Use this repo skill when a task involves the `segment-geospatial` package, the
`samgeo` Python import, or geospatial image segmentation with SAM-family models.
It is self-contained operating guidance distilled from package code, docs,
examples, tests, and installed-package inspection for version 1.4.1.

## First choose the route

| User task | Read |
| --- | --- |
| Segment a GeoTIFF or image with SAM1/SAM2, automatic masks, point prompts, box prompts, or SAM2 video | [core-segmentation](sub-skills/core-segmentation/SKILL.md) |
| Use SAM3/SAM3.1, text prompts, point/box instance prompts, tiled large-image segmentation, batch images, or SAM3 video tracking | [samgeo3-workflows](sub-skills/samgeo3-workflows/SKILL.md) |
| Download map tiles, handle CRS, prepare multi-band imagery, convert raster masks to vectors, split/merge rasters, inspect raster metadata, or use UTM helpers | [geospatial-utilities](sub-skills/geospatial-utilities/SKILL.md) |
| Use FastSAM, HQ-SAM, LangSAM/GroundingDINO text prompts, BLIP image captioning, or optional detectree2/FER notes | [specialized-models](sub-skills/specialized-models/SKILL.md) |
| Serve segmentation over HTTP, call `samgeo-api`, validate API parameters, handle output formats, or troubleshoot model/image caches | [api-server](sub-skills/api-server/SKILL.md) |

Read [model-and-workflow-overview.md](references/model-and-workflow-overview.md)
for the package map and [installation-and-dependencies.md](references/installation-and-dependencies.md)
before choosing extras or CUDA packages. Read [troubleshooting.md](references/troubleshooting.md)
for cross-cutting install, GPU, model-download, CRS, and optional-dependency failures.

## Minimal install and import checks

Use a fresh environment. Python 3.10-3.12 is exercised by the repository CI;
Python 3.11 is a safe default for ML/geospatial dependencies.

```bash
pip install "segment-geospatial[samgeo2,samgeo3,fast,hq,text,api]"
python - <<'PY'
import samgeo
from samgeo.model_registry import AVAILABLE_MODELS
print(samgeo.__version__)
print(AVAILABLE_MODELS)
PY
```

For SAM3 runtime work, verify CUDA before promising a run:

```python
import torch
print(torch.__version__, torch.version.cuda)
print(torch.cuda.is_available(), torch.cuda.device_count())
```

Run the bundled safe diagnostic when an environment looks questionable:

```bash
python scripts/check_install.py --check-optional
python scripts/check_install.py --require-cuda
```

The scripts only import modules and inspect lightweight API state; they do not
download model weights or start a service.

## Package entry points and outputs

- Python import: `samgeo`.
- Distribution: `segment-geospatial`.
- CLI entry point: `samgeo-api` for the FastAPI service.
- Main classes: `SamGeo`, `SamGeo2`, `SamGeo3`, `SamGeo3Video`, `LangSAM`,
  FastSAM/HQ-SAM wrappers, and `ImageCaptioner`.
- Typical inputs: GeoTIFF, PNG/JPEG, NumPy arrays, URLs, point coordinates,
  bounding boxes, GeoJSON/vector prompts, and videos/time-series frames.
- Typical outputs: mask GeoTIFF/PNG, vector GeoPackage/Shapefile/GeoJSON,
  JSON/detections from the API, caption/feature lists, and blended videos.

## Operating rules

- Do not tell users to open notebooks, scripts, tests, or docs from the original
  checkout. Use the bundled references and scripts in this skill.
- Distinguish pixel coordinates from geographic coordinates. If points or boxes
  are in a CRS, pass `point_crs` or `box_crs` where the selected API supports it.
- SamGeo preserves the source raster CRS during segmentation; it does not
  automatically reproject masks to EPSG:4326.
- SAM3/SAM3.1 guidance should be treated as CUDA-backed unless the task is only
  inspecting imports or mock-backed tests. CPU import checks are not proof of
  real SAM3 runtime capability.
- Model-weight downloads, Hugging Face authentication, map-tile downloads,
  long-running inference, notebooks, QGIS plugin operations, and detectree2 or
  GDAL-specific paths require explicit user/environment readiness.
- The user requested `not import` for this generated skill run; do not run the
  repo-skill import helper unless a later instruction explicitly approves it.

## Provenance and refresh

Read [repo-provenance.md](references/repo-provenance.md) before deciding this
skill matches a new checkout. If the commit, package version, public APIs, or
major example/test paths differ, refresh the skill before relying on stale
routing or API details.
