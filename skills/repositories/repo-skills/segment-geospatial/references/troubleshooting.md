# Cross-cutting troubleshooting

## Import or install failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ImportError: To use SamGeo 2, install it as: pip install segment-geospatial[samgeo2]` | `sam2` extra missing | Install `segment-geospatial[samgeo2]` or the broad selected extras from the root skill. |
| `ImportError` for FastAPI or `samgeo-api` missing | API extra missing | Install `segment-geospatial[api]` and rerun `samgeo-api --help`. |
| FastSAM import prints an error about `pkg_resources` | New setuptools removed the deprecated `pkg_resources` module used by `segment-anything-fast`/ultralytics | Pin `setuptools<81` in that environment, then import `samgeo.fast_sam` again. |
| `osgeo` or GDAL missing while importing or using FER paths | `[fer]` extra / GDAL runtime not installed | Install a GDAL-compatible environment only if the FER workflow is explicitly required; otherwise route to normal raster/vector helpers. |
| `TreeCrownDelineator` says `detectree2` or Detectron2 is required | Optional tree-crown workflow not prepared | Install Detectron2 and `detectree2` following their own compatibility constraints, then rerun only that optional workflow. |
| `samgeo.caption` import or `ImageCaptioner` hangs/fails | Remote aerial-feature vocabulary, BLIP model, or spaCy model download blocked | Check network/Hugging Face access; for offline workflows avoid captioning or provide local model/cache assets. |

## CUDA and model backend failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `Torch not compiled with CUDA enabled` or `torch.cuda.is_available() == False` | CPU-only torch wheel, no GPU passthrough, or incompatible driver | Install a CUDA torch build compatible with the host driver; verify a tiny `torch.empty(..., device="cuda")`. |
| SAM3 or SAM3.1 fails on CPU-only machines | SAM3 runtime requires CUDA for real inference | Move the run to an NVIDIA GPU host, narrow the scope to CPU-safe tests, or use SAM1/SAM2 workflows with a documented CPU fallback. |
| `Invalid backend` for `SamGeo3` | Backend string is not `meta` or `transformers` | Use `SamGeo3(backend="meta")` or `SamGeo3(backend="transformers")`. |
| `facebook/sam3.1 is only supported with backend='meta'` | SAM3.1 checkpoint path is not a Transformers model id | Use `SamGeo3(backend="meta", model_id="facebook/sam3.1")`. |
| SAM3.1 checkpoint download error mentioning Hugging Face Hub or helper signature | Installed `sam3` helper cannot fetch versioned SAM3.1 assets and HF fallback is unavailable | Install `huggingface_hub`, authenticate if the asset is gated, or provide an explicit `checkpoint_path`. |
| `Got unsupported ScalarType BFloat16` or dtype mismatch | SAM3 backend tensors were converted without upcasting or reused stale encoded state | Use package methods that call the built-in conversion helpers; re-encode images for SAM3 requests instead of assuming image-cache reuse. |

## Data, CRS, and output failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Output looks distorted on a web map | Visualization CRS changed, not segmentation | SamGeo preserves input CRS; inspect `src.crs`, then explicitly reproject after segmentation if visualization requires EPSG:4326. |
| Point or box prompts hit the wrong object | Pixel coordinates confused with geographic coordinates, or wrong CRS passed | Confirm whether prompts are pixel `[x, y]` or CRS coordinates. Pass `point_crs` or `box_crs` when using geographic coordinates. |
| Multi-band imagery produces strange colors or failed image prep | Wrong band order or non-RGB source | Use `bands=[red, green, blue]` with one-based band indices through `read_image_for_sam` / model `set_image`. |
| Raster-to-vector crashes or writes no features | Mask is all zero, missing CRS metadata, invalid geometries, or output driver problem | For all-zero masks, expect an empty FeatureCollection. For real masks, inspect raster stats and CRS, then write GeoJSON/GPKG before Shapefile. |
| Tile download fails or returns unexpected imagery | Network/provider unavailable, zoom too high, provider permission issue | Retry with a smaller bounding box/zoom, a different tile source, or a local GeoTIFF. Do not bulk-download without provider permission. |
| Large GeoTIFF segmentation runs out of memory | Full-scene inference too large | Use tiled SAM3 segmentation, split rasters with overlap, lower `points_per_side`, use a smaller crop, or run on a larger GPU. |

## REST API failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `Invalid model_version` | Not one of `sam`, `sam2`, `sam3` | Use the model registry from the root overview. |
| `Invalid model_id` | Model id not in the registry for that version | Use `vit_h/vit_l/vit_b`, `sam2-hiera-*`, or `facebook/sam3` / `facebook/sam3.1` as appropriate. |
| `/segment/predict` says `point_coords or boxes` required | Prompt request omitted both prompt types | Provide JSON strings such as `point_coords=[[100,200]]` and `point_labels=[1]`, or `boxes=[[xmin,ymin,xmax,ymax]]`. |
| `Invalid output_format` | Format not recognized | Use `geojson`, `geotiff`, `png`, `json`, or `detections`. |
| Repeated API request reuses the wrong model settings | Cache key mismatch in older code or differing constructor kwargs | Version 1.4.1 keys the cache by model-shaping kwargs; include `automatic`, backend, thresholds, and `points_per_side` consistently. |
| GPU memory remains occupied | Model cache holds loaded models | Call `DELETE /models` or restart the service. |

## When to stop and ask for user/environment input

Stop before running expensive or side-effecting work when the workflow requires:

- Hugging Face access approval or authentication.
- Large map-tile/model/video downloads.
- A CUDA GPU not visible in the environment.
- QGIS plugin installation or modification of a QGIS profile directory.
- Detectron2/detectree2 installation.
- GDAL/FER runtime support.
- A long-running full-scene benchmark, training, or video propagation run.
