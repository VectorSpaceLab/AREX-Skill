# SAM3 workflows

## Basic text-prompt segmentation

```python
from samgeo import SamGeo3

sam = SamGeo3(
    backend="meta",
    model_id="facebook/sam3",
    device="cuda",
    confidence_threshold=0.5,
)
sam.set_image("image.tif", bands=[1, 2, 3])
sam.generate_masks("building", min_size=20, max_size=None)
sam.save_masks("buildings.tif", unique=True, dtype="uint32")
sam.raster_to_vector("buildings.tif", "buildings.gpkg")
```

Use `model_id="facebook/sam3.1"` only with `backend="meta"`. For SAM3.1,
ensure Hugging Face access or provide an explicit checkpoint path if available.

## Point prompts and box prompts

For SAM3 point/box prompts, enable instance interactivity in the constructor.

```python
sam = SamGeo3(
    backend="meta",
    enable_inst_interactivity=True,
    device="cuda",
)
sam.set_image("image.tif")

sam.generate_masks_by_points(
    point_coords=[[500, 300]],
    point_labels=[1],
    point_crs=None,
    multimask_output=True,
)
sam.save_masks("point-mask.tif")

sam.generate_masks_by_boxes(
    boxes=[[100, 100, 500, 500]],
    box_crs=None,
)
sam.save_masks("box-mask.tif")
```

If prompts are geospatial, pass `point_crs` or `box_crs` and confirm the source
GeoTIFF CRS first.

## Tiled large-GeoTIFF segmentation

Use tiled segmentation when a raster is too large for one encoder pass.

```python
sam = SamGeo3(backend="meta", device="cuda")
sam.generate_masks_tiled(
    source="large.tif",
    prompt="tree",
    output="tree-masks.tif",
    tile_size=1024,
    overlap=128,
    min_size=25,
    unique=True,
    dtype="uint32",
    bands=[1, 2, 3],
    batch_size=1,
)
```

Tune `tile_size`, `overlap`, and `batch_size` to GPU memory. Always test one
small crop or a few tiles before processing a full scene.

## Batch images

`SamGeo3.set_image_batch()` and `generate_masks_batch()` support repeated image
workflows. Keep batch size conservative until model memory is known. Save each
mask with `save_masks_batch()` or iterate over results and call single-image
save helpers.

## Video and object tracking

```python
from samgeo import SamGeo3Video

sam = SamGeo3Video(gpus_to_use=[0])
sam.set_video("video.mp4", output_dir="frames", frame_rate=2)

sam.add_point_prompts(points=[[200, 180]], labels=[1], obj_id=1, frame_idx=0)
sam.propagate()
sam.save_masks("video-masks", img_ext="png")
sam.save_video("tracked.mp4", fps=10, alpha=0.6)
```

Video workflows can consume a lot of GPU memory and disk. Use a short clip and
low frame rate first.

## Output and vector conversion

- `save_masks(..., unique=True)` creates object-id masks.
- `save_scores=` can save confidence scores where supported.
- Use `raster_to_vector()` after confirming the mask raster is non-empty and
  spatially aligned.
- For API tasks, route to the API sub-skill rather than reimplementing FastAPI
  request handling in direct Python code.
