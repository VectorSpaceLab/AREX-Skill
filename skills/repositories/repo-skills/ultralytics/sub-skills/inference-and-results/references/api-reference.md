# Results API Reference

Ultralytics prediction returns one `Results` object per image or frame. The object always carries context fields such as `orig_img`, `orig_shape`, `path`, `names`, `speed`, and optional `save_dir`; task payload fields are optional and must be checked before use.

## Common Result Methods

| Method | Use |
| --- | --- |
| `len(result)` | Count the first available payload among boxes, masks, probs, keypoints, OBB, or semantic mask. Empty detection results can be `0`. |
| `result[i]` | Slice/index payload tensors into a new `Results` object. |
| `result.cpu()` | Return a copy with tensor payloads moved to CPU. |
| `result.numpy()` | Return a copy with tensor payloads converted to NumPy arrays. |
| `result.cuda()` | Return a copy on CUDA, when available. |
| `result.to(device=..., dtype=...)` | Return a copy converted with PyTorch `.to(...)`. |
| `result.plot(...)` | Return an annotated image array or PIL image with configurable boxes, masks, keypoints, labels, and probabilities. |
| `result.save(filename=...)` | Save the annotated image and return the filename. |
| `result.save_txt(path, save_conf=False)` | Append text output for supported tasks. Semantic segmentation is not supported. |
| `result.save_crop(save_dir=..., file_name=...)` | Save object crops for box-based outputs. Classification, OBB, and semantic segmentation are not supported. |
| `result.summary(normalize=False, decimals=5)` | Convert task output to a list of dictionaries, including semantic per-class pixel ratios. |
| `result.to_df()`, `to_csv()`, `to_json()` | Export summarized results through the data-export mixin. |

## Task Payload Matrix

| Task | Primary fields | Do not assume |
| --- | --- | --- |
| Detect | `result.boxes` | `masks`, `keypoints`, `probs`, `obb`, `semantic_mask` |
| Segment | `result.boxes`, `result.masks` | Semantic dense maps; masks are per-instance polygons/tensors |
| Semantic | `result.semantic_mask` | `boxes`, instance `masks`, confidence per object |
| Classify | `result.probs` | `boxes`, crops, object counts |
| Pose | `result.boxes`, `result.keypoints` | `masks`, `probs`, `obb`, semantic maps |
| OBB | `result.obb` | `result.boxes` as the primary rotated geometry |
| Track | `result.boxes` or `result.obb` with optional IDs | Tracking setup and tracker configs belong to tracking guidance |

## Detection Boxes

```python
if result.boxes is not None:
    boxes = result.boxes
    xyxy = boxes.xyxy          # shape (N, 4), pixel [x1, y1, x2, y2]
    xywhn = boxes.xywhn        # shape (N, 4), normalized [x, y, w, h]
    conf = boxes.conf          # shape (N,)
    cls = boxes.cls.int()      # shape (N,)
    names = [result.names[int(c)] for c in cls]
    track_ids = boxes.id if boxes.is_track else None
```

Raw `boxes.data` has shape `(N, 6)` for `[x1, y1, x2, y2, conf, cls]`, or `(N, 7)` when a tracking ID column is present.

## Instance Segmentation Masks

```python
if result.masks is not None:
    mask_tensor = result.masks.data  # shape (N, H, W)
    pixel_polygons = result.masks.xy
    normalized_polygons = result.masks.xyn
```

Segment predictors can keep boxes and masks aligned. If `retina_masks=True`, masks are processed at original image resolution. Empty segmentation predictions can have boxes with no masks or `masks is None`; guard both fields.

## Semantic Segmentation Mask

```python
if result.semantic_mask is not None:
    semantic = result.semantic_mask.data  # shape (H, W), integer class IDs
    per_class = result.summary(normalize=False)
```

A semantic mask is a dense class-ID map for the full image, not one mask per object. It intentionally lacks `Masks.xy`/`xyn` polygon helpers and does not support `save_txt` or `save_crop`.

## Classification Probabilities

```python
if result.probs is not None:
    probs = result.probs
    top1_id = probs.top1
    top1_name = result.names[top1_id]
    top1_conf = float(probs.top1conf)
    top5 = [(result.names[i], float(probs.data[i])) for i in probs.top5]
```

Classification results usually have `len(result) == number_of_probability_values`, not number of detected objects. Do not call box/crop logic for classification.

## Pose Keypoints

```python
if result.keypoints is not None:
    keypoints = result.keypoints
    xy = keypoints.xy       # shape (N, K, 2), pixel coordinates
    xyn = keypoints.xyn     # shape (N, K, 2), normalized coordinates
    conf = keypoints.conf   # shape (N, K) or None
```

Pose results commonly also include `result.boxes`; keep checks independent because synthetic or custom `Results` can contain keypoints without boxes.

## Oriented Bounding Boxes

```python
if result.obb is not None:
    obb = result.obb
    xywhr = obb.xywhr          # shape (N, 5), center/size/rotation
    corners = obb.xyxyxyxy     # shape (N, 4, 2), rotated corners
    corners_n = obb.xyxyxyxyn  # normalized rotated corners
    axis_aligned = obb.xyxy    # enclosing rectangle, not the rotated box itself
    conf = obb.conf
    cls = obb.cls.int()
```

Raw OBB data has shape `(N, 7)` or `(N, 8)` when tracking IDs are present. Use `xyxyxyxy` or `xywhr` for rotated geometry; use `xyxy` only for tools that require an axis-aligned approximation.

## Plotting and Export

```python
image_bgr = result.plot(conf=True, boxes=True, masks=True, probs=True)
result.save("outputs/prediction.jpg", conf=False)
rows = result.summary(normalize=True, decimals=4)
json_text = result.to_json(normalize=True)
```

`plot()` accepts `line_width`, `font_size`, `font`, `pil`, `img`, `im_gpu`, `kpt_radius`, `kpt_line`, `labels`, `boxes`, `masks`, `probs`, `show`, `save`, `filename`, `color_mode`, and `txt_color`. `color_mode` must be `"class"` or `"instance"`.

## Download-Free Contract Inspection

Run the bundled helper to print the public result fields and extraction snippets without loading weights:

```bash
python sub-skills/inference-and-results/scripts/inspect_results_contract.py --snippets
```

Use it when you need a quick reminder of which result attribute belongs to which task or when writing tests that should not trigger model downloads.
