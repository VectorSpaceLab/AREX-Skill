# Model and workflow overview

## Purpose

Use this reference to pick the right SamGeo class, model family, output format,
and sub-skill before writing code or API calls.

## Package map

| Surface | Import / command | Main tasks | Read next |
| --- | --- | --- | --- |
| Core SAM1 | `from samgeo import SamGeo` or `from samgeo.samgeo import SamGeo` | Automatic masks, point/box prompts, GeoTIFF/vector outputs | `sub-skills/core-segmentation/` |
| SAM2 | `from samgeo import SamGeo2` | SAM2 automatic masks, prompts, batch prediction, videos, region groups | `sub-skills/core-segmentation/` |
| SAM3 / SAM3.1 | `from samgeo import SamGeo3, SamGeo3Video` | Text prompts, point/box prompts, tiled large GeoTIFFs, batch images, video/object tracking | `sub-skills/samgeo3-workflows/` |
| Geospatial helpers | `from samgeo import common` or `from samgeo.common import ...` | Tile downloads, CRS, image prep, raster/vector conversion, COG, split/merge, UTM | `sub-skills/geospatial-utilities/` |
| FastSAM / HQ-SAM | `from samgeo.fast_sam import SamGeo`; `from samgeo.hq_sam import SamGeo` | Alternative fast or high-quality SAM-style segmentation | `sub-skills/specialized-models/` |
| LangSAM text prompts | `from samgeo.text_sam import LangSAM` | GroundingDINO + SAM text-prompt masks | `sub-skills/specialized-models/` |
| Captioning | `from samgeo.caption import ImageCaptioner` | BLIP caption generation and aerial feature extraction | `sub-skills/specialized-models/` |
| REST API | `samgeo-api`; `samgeo.api` | HTTP segmentation endpoints and model/image caches | `sub-skills/api-server/` |

## Model registry

Verified registry constants in version 1.4.1:

```python
DEFAULT_MODEL_IDS = {
    "sam": "vit_h",
    "sam2": "sam2-hiera-large",
    "sam3": "facebook/sam3",
}
AVAILABLE_MODELS = {
    "sam": ["vit_h", "vit_l", "vit_b"],
    "sam2": [
        "sam2-hiera-tiny",
        "sam2-hiera-small",
        "sam2-hiera-base-plus",
        "sam2-hiera-large",
    ],
    "sam3": ["facebook/sam3", "facebook/sam3.1"],
}
EXTRAS_MAP = {"sam": "samgeo", "sam2": "samgeo2", "sam3": "samgeo3"}
```

## Workflow selection heuristics

- Start with `SamGeo` when the user names original SAM, `vit_h/vit_l/vit_b`, or
  wants the simplest automatic/prompt GeoTIFF mask workflow.
- Use `SamGeo2` when the user names SAM2, Hiera models, batch prompt prediction,
  video segmentation, or `sam2-hiera-*` identifiers.
- Use `SamGeo3` when the user names SAM3/SAM3.1, wants text prompts with SAM3,
  asks for tiled large GeoTIFF segmentation, or needs point/box instance
  interactivity with `enable_inst_interactivity=True`.
- Use `SamGeo3Video` when the input is a video or a frame sequence and the user
  wants object tracking, propagation, prompt refinement, mask frames, or blended
  videos.
- Use `LangSAM` when the user specifically wants GroundingDINO-style text
  prompts with SAM1/SAM2 instead of SAM3.
- Use FastSAM when speed is the primary trade-off; use HQ-SAM when higher mask
  quality is more important than dependency size or model load time.
- Use `samgeo.common` utilities whenever the task is mostly data preparation,
  CRS, raster/vector conversion, or validation rather than model inference.
- Use `samgeo-api` when the user needs HTTP access, non-Python clients,
  repeated requests, or cacheable model serving.

## Inputs and coordinate conventions

- GeoTIFF inputs preserve raster transform/CRS in mask outputs.
- PNG/JPEG inputs can be segmented, but non-georeferenced outputs do not gain a
  CRS unless the workflow supplies one through a georeferenced source.
- Point prompts usually use pixel coordinates unless a `point_crs` parameter is
  provided; then SamGeo converts to pixel coordinates using the source raster.
- Box prompts are `[xmin, ymin, xmax, ymax]`. SAM3 methods accept `box_crs` when
  the box is geospatial rather than pixel-based.
- Multi-band GeoTIFFs should be reduced to RGB with `bands=[r, g, b]` using
  one-based band indices for public helper calls.

## Output conventions

- Raster masks: GeoTIFF/PNG depending on method and output path.
- Unique masks: object ids are encoded as unique values when `unique=True`.
- Foreground masks: binary foreground/background masks when `foreground=True`.
- Vector masks: GeoPackage (`.gpkg`), Shapefile (`.shp`), or GeoJSON via
  `raster_to_vector`, `tiff_to_gpkg`, `tiff_to_shp`, or `tiff_to_geojson`.
- REST API outputs: `geojson`, `geotiff`, `png`, `json`, or `detections`.
- Video outputs: mask frame files and optional blended videos.

## Validation before expensive runs

1. Import the selected module and print its signature or version.
2. Verify the image path, raster CRS, dimensions, bands, and whether the points
   or boxes are pixel or CRS coordinates.
3. Verify CUDA for SAM3 or large model runs.
4. Confirm model weights and Hugging Face access before constructing models that
   download assets.
5. Use a tiny crop, low `points_per_side`, or small prompt set before running a
   full satellite scene.
6. Convert a small mask to vector and inspect feature counts before applying
   simplification, regularization, or smoothing at scale.
