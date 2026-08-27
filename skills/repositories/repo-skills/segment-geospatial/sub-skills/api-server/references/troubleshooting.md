# API troubleshooting

## Startup failures

- `samgeo-api: command not found`: install `segment-geospatial[api]` or ensure
  the environment's scripts directory is on `PATH`.
- `FastAPI dependencies are required`: install `[api]`.
- Port already in use: pass a different `--port` or stop the existing service.
- CUDA/model construction fails at startup with `--preload`: remove `--preload`,
  verify imports/CUDA/model access, then preload again.

## Request validation failures

| Symptom | Recovery |
| --- | --- |
| `Invalid model_version` | Use `sam`, `sam2`, or `sam3`. |
| `Invalid model_id` | Choose an id from `/models`; SAM3.1 is `facebook/sam3.1`. |
| `/segment/predict` says prompts are missing | Send either `point_coords` or `boxes` as JSON strings. |
| `Invalid output_format` | Use `geojson`, `geotiff`, `png`, `json`, or `detections`. |
| Upload returns 422 | Ensure multipart field is named `file` and the request uses `-F`/multipart form data. |

## Model/cache failures

- The model cache separates automatic and prompt instances so a prompt request
  should not reuse an automatic generator.
- Cache keys include model-shaping kwargs. If thresholds/backend/options change,
  expect a separate model instance.
- Use `DELETE /models` to clear loaded models and free GPU memory.
- SAM3 image encoding is intentionally not skipped between same-image requests;
  this avoids stale-state dtype failures.

## Output interpretation

- `geojson` returns polygons/features where raster metadata is available.
- `json` returns pixel-coordinate detection boxes and is suitable for
  non-georeferenced images.
- `detections` returns geographic feature boxes when source georeferencing is
  available.
- `png` and `geotiff` responses are files, not JSON.

## Performance and safety

- First request pays model load and image encoding costs; repeated SAM/SAM2
  requests can be much faster due image cache.
- SAM3 still re-encodes and can be GPU-heavy.
- Do not expose the service publicly without external auth/rate-limit controls.
- Keep uploaded rasters bounded in size; API code streams uploads to temp files,
  but model inference can still exhaust memory.
