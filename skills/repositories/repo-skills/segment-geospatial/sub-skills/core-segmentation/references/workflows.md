# SAM1 and SAM2 segmentation workflows

## Automatic mask generation with `SamGeo`

Use original SAM when the task names `vit_h`, `vit_l`, `vit_b`, or the user
wants the simplest SamGeo path.

```python
from samgeo import SamGeo

sam = SamGeo(
    model_type="vit_h",
    automatic=True,
    device="cuda",      # use "cpu" only for small experiments
    sam_kwargs={"points_per_side": 32},
)
sam.generate("image.tif", output="masks.tif", foreground=True, unique=True)
sam.tiff_to_gpkg("masks.tif", "masks.gpkg")
```

Notes:

- `checkpoint=` can be supplied to avoid a checkpoint download.
- `foreground=True` extracts foreground objects; `unique=True` assigns distinct
  object ids.
- Use a smaller crop, lower `points_per_side`, or tiled processing for large
  rasters.

## Prompt segmentation with `SamGeo`

Prompt mode must use `automatic=False`, then `set_image()` before `predict()`.

```python
from samgeo import SamGeo

sam = SamGeo(model_type="vit_h", automatic=False, device="cuda")
sam.set_image("image.tif", bands=[1, 2, 3])

sam.predict(
    point_coords=[[-122.1419, 37.6383]],
    point_labels=[1],
    point_crs="EPSG:4326",
    output="point-mask.tif",
    multimask_output=True,
)

sam.predict(
    boxes=[[-122.146, 37.631, -122.120, 37.646]],
    point_crs="EPSG:4326",
    output="box-mask.tif",
)
```

Use pixel coordinates instead when the prompts are already `[x, y]` image
positions. Do not pass a CRS for pixel prompts.

## SAM2 automatic and prompt workflows

Use `SamGeo2` for SAM2 Hiera model ids and improved batch/video paths.

```python
from samgeo import SamGeo2

sam = SamGeo2(
    model_id="sam2-hiera-large",
    device="cuda",
    automatic=True,
    points_per_side=32,
    pred_iou_thresh=0.8,
    stability_score_thresh=0.95,
)
sam.generate("image.tif", output="sam2-masks.tif", unique=True)
sam.raster_to_vector("sam2-masks.tif", "sam2-masks.gpkg")
```

Prompt mode mirrors SAM1 but defaults differ:

```python
sam = SamGeo2(model_id="sam2-hiera-large", device="cuda", automatic=False)
sam.set_image("image.tif")
sam.predict(
    point_coords=[[100, 200], [140, 220]],
    point_labels=[1, 0],
    output="sam2-prompt.tif",
    multimask_output=False,
)
```

## SAM2 batch and video patterns

Batch prompt prediction accepts lists for per-image prompts:

```python
masks, scores, logits = sam.predict_batch(
    point_coords_batch=[[[100, 200]]],
    point_labels_batch=[[1]],
    multimask_output=False,
)
```

Video workflow:

```python
sam = SamGeo2(model_id="sam2-hiera-large", device="cuda", video=True)
sam.set_video("video.mp4", output_dir="frames", frame_rate=2)
sam.predict_video(
    prompts={0: {"points": [[100, 200]], "labels": [1]}},
    output_dir="video-masks",
)
```

Run video workflows on a small clip first; full propagation can consume GPU
memory and disk space.

## Output conversion checklist

1. Inspect mask statistics before vectorization.
2. Prefer GeoPackage or GeoJSON for first output checks; Shapefile has stricter
   field/path limits.
3. Use `simplify_tolerance` only after confirming masks are spatially correct.
4. Convert with model convenience methods or `samgeo.common`:

```python
sam.tiff_to_geojson("masks.tif", "masks.geojson")
sam.tiff_to_gpkg("masks.tif", "masks.gpkg")
```

## Validation steps before scale-up

- Print raster CRS, transform, width/height, and band count.
- Verify coordinate type: pixel vs CRS.
- Run a tiny crop or low-resolution image before a large scene.
- Confirm that model weights are cached or downloadable before constructing the
  model in a long job.
- If the output is empty, decide whether the prompt/model truly found no
  foreground before treating it as a failure.
