---
name: imagery-raster-analysis
description: "Route imagery layers, raster function chains, raster analytics,
  multidimensional rasters, and orthomapping workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# imagery-raster-analysis

Use this sub-skill for imagery and raster workflows that center on:
- `ImageryLayer` and image-service access
- raster functions and function chains
- raster analytics tools and persisted raster outputs
- multidimensional rasters
- orthomapping project, image collection, GCP, DSM, and orthomosaic workflows

Do not use this sub-skill for:
- learned model training or inference (`deep-learning`)
- map display basics or widget setup (`mapping-location-services`)
- feature layer / SEDF / spatial analysis (`features-dataframes-analysis`)

## Quick routing
1. If you already have an image-service URL or imagery item, start with `ImageryLayer`.
2. If you need on-the-fly visualization or band math, use raster functions.
3. If you need server-side processing, saved outputs, or large data, use raster analytics.
4. If you need UAV image collections, sensor models, seamlines, DSM/DTM, or orthomosaics, use orthomapping.
5. If the target GIS lacks raster analytics or orthomapping support, stop and explain the missing service.

## Preflight
- Confirm the target `GIS` or portal connection is authenticated.
- Check `arcgis.raster.analytics.is_supported(gis)` and `arcgis.raster.orthomapping.is_supported(gis)` before server-side work.
- Inspect `ImageryLayer.properties.rasterFunctionInfos` before applying a named function.
- Use unique `output_name` values for persisted raster jobs.
- Treat `future=True` and other async outputs as jobs or result objects, not immediate rasters.
- In credential-free environments, keep to imports, signatures, and static reasoning only.

## Read next
- [Workflow guide](references/imagery-raster-workflows.md)
- [API reference](references/raster-api-reference.md)
- [Troubleshooting](references/troubleshooting.md)
- [Import smoke](scripts/raster_import_smoke.py)
