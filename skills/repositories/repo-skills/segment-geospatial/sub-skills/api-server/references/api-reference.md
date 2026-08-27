# REST API reference

Install with:

```bash
pip install "segment-geospatial[api]"
```

Combine with model extras as needed, for example:

```bash
pip install "segment-geospatial[api,samgeo3]"
```

## CLI

```bash
samgeo-api --host 0.0.0.0 --port 8000
samgeo-api --preload sam2:sam2-hiera-large
samgeo-api --reload
uvicorn samgeo.api:app --host 0.0.0.0 --port 8000
```

Verified CLI options: `--host`, `--port`, `--reload`, and `--preload`.

## Model registry

- `model_version`: one of `sam`, `sam2`, `sam3`.
- Default ids: `sam -> vit_h`, `sam2 -> sam2-hiera-large`,
  `sam3 -> facebook/sam3`.
- SAM3 ids: `facebook/sam3` and `facebook/sam3.1`.

## Endpoints

### `GET /health`

Returns service status and package version.

### `GET /models`

Returns available model ids and currently loaded cache entries.

### `DELETE /models`

Clears the model cache and image hash cache. Use it to free GPU memory or force
fresh model construction.

### `POST /segment/automatic`

Multipart form parameters:

| Parameter | Default | Notes |
| --- | --- | --- |
| `file` | required | TIFF/PNG/JPEG upload |
| `model_version` | `sam3` | `sam`, `sam2`, or `sam3` |
| `model_id` | default by model version | Must be in registry |
| `output_format` | `geojson` | `geojson`, `geotiff`, `png`, `json`, `detections` |
| `foreground` | `true` | foreground extraction |
| `unique` | `true` | unique object ids |
| `min_size` | `0` | minimum mask area |
| `max_size` | none | `0` or negative normalizes to no max |
| `points_per_side` | `32` | automatic mask sampling density |
| `pred_iou_thresh` | `0.8` | mask quality filter |
| `stability_score_thresh` | `0.95` | stability filter |

### `POST /segment/predict`

Prompt-based segmentation. Parameters:

| Parameter | Default | Notes |
| --- | --- | --- |
| `file` | required | image upload |
| `model_version` | `sam3` | `sam`, `sam2`, or `sam3` |
| `model_id` | default by version | registry id |
| `output_format` | `geojson` | same valid formats as automatic |
| `point_coords` | none | JSON string like `[[100, 200]]` |
| `point_labels` | none | JSON string like `[1]`; foreground `1`, background `0` |
| `boxes` | none | JSON string like `[[xmin, ymin, xmax, ymax]]` |
| `point_crs` | none | CRS when prompts are geospatial |
| `multimask_output` | `false` | return/use multiple masks where supported |
| `min_size`, `max_size` | `0`, none | area filters |

At least `point_coords` or `boxes` is required.

### `POST /segment/text`

SAM3 text-prompt segmentation. Parameters:

| Parameter | Default | Notes |
| --- | --- | --- |
| `file` | required | image upload |
| `prompt` | required | object text, e.g. `building` |
| `model_id` | default SAM3 id | `facebook/sam3` or `facebook/sam3.1` |
| `backend` | `meta` | `meta` or supported `transformers`; SAM3.1 uses `meta` |
| `output_format` | `geojson` | valid output formats |
| `confidence_threshold` | `0.5` | detection confidence |
| `min_size`, `max_size` | `0`, none | area filters |

## Output formats

- `geojson`: mask polygons as GeoJSON FeatureCollection.
- `geotiff`: georeferenced mask raster when source metadata permits.
- `png`: image mask response.
- `json`: pixel-coordinate detections/bounding boxes.
- `detections`: geographic-coordinate bounding boxes/features where possible.

## Cache behavior

- Model cache key includes model version, model id, and model-shaping kwargs such
  as `automatic`, backend, thresholds, and `points_per_side`.
- Image hash cache skips repeated `set_image()` for SAM/SAM2 on identical
  images.
- SAM3 always re-encodes images for correctness because repeated generation can
  mutate encoded state and cause dtype mismatches.
