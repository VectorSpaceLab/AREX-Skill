# SAM3 API reference

Verified from installed `segment-geospatial` 1.4.1.

## Model ids and backends

- Default SAM3 model id: `facebook/sam3`.
- SAM3.1 id: `facebook/sam3.1`.
- Allowed `backend` values: `meta` and `transformers`.
- SAM3.1 is supported with `backend="meta"`; passing SAM3.1 to the transformers
  backend raises a user-facing `ValueError`.

## `SamGeo3`

```python
SamGeo3(
    backend="meta",
    model_id="facebook/sam3",
    bpe_path=None,
    device=None,
    eval_mode=True,
    checkpoint_path=None,
    load_from_HF=True,
    enable_segmentation=True,
    enable_inst_interactivity=False,
    compile_mode=False,
    resolution=1008,
    confidence_threshold=0.5,
    mask_threshold=0.5,
    **kwargs,
)
```

Constructor notes:

- `device=None` auto-selects through package helpers; pass `"cuda"` explicitly
  for production SAM3 runtime when CUDA is required.
- `checkpoint_path` overrides Hugging Face checkpoint download.
- `load_from_HF=True` controls Meta-backend loading from Hugging Face.
- `enable_inst_interactivity=True` loads additional components for point/box
  instance prompts and `predict_inst()`.
- `confidence_threshold` affects SAM3 detection filtering.

Important methods:

```python
SamGeo3.set_image(image, state=None, bands=None)
SamGeo3.generate_masks(prompt, min_size=0, max_size=None, quiet=False, **kwargs)
SamGeo3.generate_masks_tiled(source, prompt, output, tile_size=1024,
                             overlap=128, min_size=0, max_size=None,
                             unique=True, dtype="uint32", bands=None,
                             batch_size=1, verbose=True, **kwargs)
SamGeo3.generate_masks_by_boxes(boxes, box_labels=None, box_crs=None,
                                min_size=0, max_size=None, **kwargs)
SamGeo3.generate_masks_by_points(point_coords, point_labels=None, point_crs=None,
                                 multimask_output=True, min_size=0,
                                 max_size=None, **kwargs)
SamGeo3.predict_inst(point_coords=None, point_labels=None, box=None,
                     mask_input=None, multimask_output=True,
                     return_logits=False, normalize_coords=True,
                     point_crs=None, box_crs=None)
SamGeo3.save_masks(output=None, unique=True, min_size=0, max_size=None,
                   dtype="uint8", save_scores=None, **kwargs)
```

Visualization helpers include `show_masks`, `show_anns`, `show_boxes`,
`show_points`, `plot_bbox`, `draw_box_on_image`, and `plot_mask`.

## `SamGeo3Video`

```python
SamGeo3Video(gpus_to_use=None, bpe_path=None, **kwargs)
SamGeo3Video.set_video(video_path, output_dir=None, frame_rate=None, prefix="", bands=None)
SamGeo3Video.generate_masks(prompt, frame_idx=0, propagate=True)
SamGeo3Video.add_point_prompts(points, labels, obj_id, frame_idx=0, point_crs=None)
SamGeo3Video.add_box_prompt(box, obj_id, frame_idx=0, box_crs=None)
SamGeo3Video.add_mask_prompt(mask, obj_id, frame_idx=0)
SamGeo3Video.remove_object(obj_id)
SamGeo3Video.propagate()
SamGeo3Video.save_masks(output_dir, img_ext="png", dtype="uint8")
SamGeo3Video.save_video(output_path, fps=30, alpha=0.6, dpi=200,
                        frame_stride=1, show_ids=True)
```

## Test-backed behavior

Repository tests verify these logic paths without downloading models:

- Invalid SAM3 backend strings fail before dependency checks.
- `facebook/sam3.1` with `backend="transformers"` is rejected as a user error.
- Custom Meta backend model ids are preserved.
- SAM3.1 checkpoint download prefers a version-aware `download_ckpt_from_hf`;
  older helper signatures fall back to Hugging Face Hub.
- Explicit `checkpoint_path` and `SAM3_CHECKPOINT_PATH` override downloads.
- The API image-cache skip is disabled for SAM3 because repeated generation can
  mutate encoded state and cause dtype mismatches.
