# Core segmentation API reference

Verified from installed `segment-geospatial` 1.4.1.

## `SamGeo` (original SAM)

```python
SamGeo(
    model_type="vit_h",
    automatic=True,
    device=None,
    checkpoint_dir=None,
    sam_kwargs=None,
    **kwargs,
)
```

- `model_type`: one of `vit_h`, `vit_l`, `vit_b`.
- `automatic=True`: constructs an automatic mask generator.
- `automatic=False`: constructs a prompt predictor and requires `set_image()`
  before `predict()`.
- `checkpoint=` may be supplied through `**kwargs`; otherwise the package can
  download or locate model weights.
- `device`: `cuda` or `cpu`; `None` auto-selects CUDA when available.

Important methods:

```python
SamGeo.generate(
    source,
    output=None,
    foreground=True,
    batch=False,
    batch_sample_size=(512, 512),
    batch_nodata_threshold=1.0,
    nodata_value=None,
    erosion_kernel=None,
    mask_multiplier=255,
    unique=True,
    min_size=0,
    max_size=None,
    bands=None,
    **kwargs,
)

SamGeo.set_image(image, image_format="RGB", bands=None)

SamGeo.predict(
    point_coords=None,
    point_labels=None,
    boxes=None,
    point_crs=None,
    mask_input=None,
    multimask_output=True,
    return_logits=False,
    output=None,
    index=None,
    mask_multiplier=255,
    dtype="float32",
    return_results=False,
    **kwargs,
)

SamGeo.save_masks(output=None, foreground=True, unique=True, erosion_kernel=None,
                  mask_multiplier=255, min_size=0, max_size=None, **kwargs)
SamGeo.tiff_to_vector(tiff_path, output, simplify_tolerance=None, **kwargs)
SamGeo.tiff_to_gpkg(tiff_path, output, simplify_tolerance=None, **kwargs)
SamGeo.tiff_to_shp(tiff_path, output, simplify_tolerance=None, **kwargs)
SamGeo.tiff_to_geojson(tiff_path, output, simplify_tolerance=None, **kwargs)
```

## `SamGeo2` (SAM2)

```python
SamGeo2(
    model_id="sam2-hiera-large",
    device=None,
    empty_cache=True,
    automatic=True,
    video=False,
    mode="eval",
    hydra_overrides_extra=None,
    apply_postprocessing=False,
    points_per_side=32,
    points_per_batch=64,
    pred_iou_thresh=0.8,
    stability_score_thresh=0.95,
    stability_score_offset=1.0,
    mask_threshold=0.0,
    box_nms_thresh=0.7,
    crop_n_layers=0,
    crop_nms_thresh=0.7,
    crop_overlap_ratio=512 / 1500,
    crop_n_points_downscale_factor=1,
    point_grids=None,
    min_mask_region_area=0,
    output_mode="binary_mask",
    use_m2m=False,
    multimask_output=False,
    max_hole_area=0.0,
    max_sprinkle_area=0.0,
    **kwargs,
)
```

Allowed model ids are `sam2-hiera-tiny`, `sam2-hiera-small`,
`sam2-hiera-base-plus`, and `sam2-hiera-large`; the constructor normalizes them
to `facebook/...` ids.

Important methods:

```python
SamGeo2.generate(source, output=None, foreground=True, erosion_kernel=None,
                 mask_multiplier=255, unique=True, min_size=0, max_size=None,
                 bands=None, **kwargs)
SamGeo2.set_image(image, bands=None)
SamGeo2.predict(point_coords=None, point_labels=None, boxes=None, mask_input=None,
                multimask_output=False, return_logits=False, normalize_coords=True,
                point_crs=None, output=None, index=None, mask_multiplier=255,
                dtype="float32", return_results=False, **kwargs)
SamGeo2.predict_batch(point_coords_batch=None, point_labels_batch=None,
                      box_batch=None, mask_input_batch=None,
                      multimask_output=False, return_logits=False,
                      normalize_coords=True)
SamGeo2.set_video(video_path, output_dir=None, frame_rate=None, prefix="")
SamGeo2.predict_video(prompts=None, point_crs=None, output_dir=None, img_ext="png")
SamGeo2.region_groups(image, connectivity=1, min_size=10, max_size=None,
                      threshold=None, properties=None, intensity_image=None,
                      out_csv=None, out_vector=None, out_image=None, **kwargs)
```

## Parameter gotchas

- `point_labels`: use `1` for foreground and `0` for background.
- `multimask_output=True` can return multiple candidate masks; choose `index`
  when saving a single preferred mask.
- `point_crs` applies only when prompt coordinates are geospatial. Leave it
  unset for pixel coordinates.
- `bands` is for selecting RGB bands from multi-band imagery; public examples
  use one-based band numbers.
- `min_size` and `max_size` filter mask areas after prediction/generation.
- `output_mode="binary_mask"` is memory-heavy for large resolutions; use crops,
  lower point density, or tiled workflows when needed.
