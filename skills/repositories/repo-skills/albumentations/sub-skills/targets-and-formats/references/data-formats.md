# Data Formats and Target Contracts

This reference summarizes the Albumentations 2.0.8 target contracts that matter when geometry must stay synchronized across images, masks, bboxes, keypoints, labels, and 3D volumes.

## Compose Target Keys

Call pipelines with named arguments only, for example `transform(image=image, mask=mask, bboxes=bboxes, class_labels=labels)`. Positional data is rejected.

| Key | Expected shape | Notes |
| --- | --- | --- |
| `image` | `H,W` or `H,W,C` NumPy array | Main 2D image target. |
| `images` | list of images or array `N,H,W[,C]` | Geometric transforms use the same sampled params across the sequence. Lists are stacked internally and returned as lists. |
| `mask` | `H,W` or `H,W,C` NumPy array | Uses mask interpolation/fill behavior, not image interpolation. |
| `masks` | list of masks or array `N,H,W[,C]` | Empty list is allowed. Nonempty lists must contain 2D/3D NumPy arrays. |
| `bboxes` | sequence/array `N,4+` | Requires `bbox_params`. First four columns are coordinates; extra columns can carry inline labels/scores, but `label_fields` is usually clearer. |
| `keypoints` | sequence/array `N,2+` | Requires `keypoint_params`. Number/order of coordinate columns must match the declared keypoint format. |
| `volume` | array `D,H,W[,C]` | Single 3D volume; spatial order is depth, height, width, optional channels last. |
| `volumes` | array `N,D,H,W[,C]` | Batch of 3D volumes. |
| `mask3d` | array `D,H,W[,C]` | Single 3D mask; checked against `volume` on `D,H,W`. |
| `masks3d` | array `N,D,H,W[,C]` | Batch of 3D masks. |

With `is_check_shapes=True`, 2D targets must share `H,W`. Volume-like targets must share `D,H,W`, and their `H,W` also participates in the common 2D shape check when mixed with `image`/`mask`.

## Bounding Boxes

Declare bbox processing on `A.Compose`:

```python
transform = A.Compose(
    [A.HorizontalFlip(p=0.5), A.RandomCrop(height=256, width=256)],
    bbox_params=A.BboxParams(
        format="pascal_voc",
        label_fields=["class_labels"],
        clip=True,
        filter_invalid_bboxes=True,
        min_visibility=0.1,
    ),
)
```

Supported `BboxParams` signature:

```python
A.BboxParams(
    format,                    # "coco", "pascal_voc", "albumentations", or "yolo"
    label_fields=None,
    min_area=0.0,
    min_visibility=0.0,
    min_width=0.0,
    min_height=0.0,
    check_each_transform=True,
    clip=False,
    filter_invalid_bboxes=False,
    max_accept_ratio=None,
)
```

### Bbox Formats

| Format | Coordinates | Units | Validity reminders |
| --- | --- | --- | --- |
| `pascal_voc` | `[x_min, y_min, x_max, y_max]` | pixels | `x_max > x_min`, `y_max > y_min`; image shape converts to normalized internals. |
| `coco` | `[x_min, y_min, width, height]` | pixels | `width > 0`, `height > 0`; converted to corners internally. |
| `albumentations` | `[x_min, y_min, x_max, y_max]` | normalized `[0,1]` | Same corner order as Pascal VOC, but normalized. |
| `yolo` | `[x_center, y_center, width, height]` | normalized `(0,1]` for each value | Not corners. Values outside `(0,1]` are invalid during checked conversion. |

Albumentations converts all bbox formats to normalized Pascal VOC internally, clips if `clip=True`, optionally filters invalid boxes when `filter_invalid_bboxes=True`, validates, applies transforms, filters by `min_area`, `min_visibility`, `min_width`, `min_height`, and `max_accept_ratio`, then converts back to the requested format.

### Filtering and Clipping

- `clip=True` clips normalized internal corners to image boundaries before transforms.
- `filter_invalid_bboxes=True` removes boxes with invalid dimensions after optional clipping at the pipeline start.
- `min_area` is evaluated in pixels for visible area after transforms.
- `min_visibility` removes boxes whose visible area fraction after transform is below the threshold.
- `min_width` and `min_height` filter small boxes; the threshold is interpreted in the current processed coordinate basis documented by `BboxParams`.
- `max_accept_ratio` removes boxes whose aspect ratio `max(width/height, height/width)` exceeds the threshold; if provided it must be at least `1.0`.
- `check_each_transform=True` validates after each dual transform, which catches bad geometry early but can surface failures inside a long pipeline.

## Keypoints

Declare keypoint processing on `A.Compose`:

```python
transform = A.Compose(
    [A.Rotate(limit=20, p=1.0)],
    keypoint_params=A.KeypointParams(
        format="xy",
        label_fields=["keypoint_labels"],
        remove_invisible=True,
    ),
)
```

Supported `KeypointParams` signature:

```python
A.KeypointParams(
    format,                    # "xy", "yx", "xya", "xys", "xyas", "xysa", or "xyz"
    label_fields=None,
    remove_invisible=True,
    angle_in_degrees=True,
    check_each_transform=True,
)
```

### Keypoint Formats

| Format | Columns | Notes |
| --- | --- | --- |
| `xy` | `[x, y]` | 2D pixel coordinates. |
| `yx` | `[y, x]` | Same coordinates reversed. |
| `xya` | `[x, y, angle]` | Angle uses degrees by default; set `angle_in_degrees=False` for radians. |
| `xys` | `[x, y, scale]` | Scale is preserved/transformed where supported. |
| `xyas` | `[x, y, angle, scale]` | Angle then scale. |
| `xysa` | `[x, y, scale, angle]` | Scale then angle. |
| `xyz` | `[x, y, z]` | 3D keypoints with volume depth checks when a `volume` is present. |

Internally keypoints are `[x, y, z, angle, scale]`. For 2D formats `z=0`; missing angle/scale are set to `0`; extra columns beyond the declared format are preserved after the internal five columns.

### Keypoint Filtering

- Keypoint coordinates are absolute, not normalized.
- Valid 2D ranges are `0 <= x < width` and `0 <= y < height`.
- With volume shape information, valid 3D range also includes `0 <= z < depth`.
- Angles are normalized internally to `[0, 2π)` radians.
- `remove_invisible=True` removes keypoints outside the target bounds after transforms and also filters `label_fields` to match.
- `remove_invisible=False` keeps off-image/off-volume keypoints; use this only when downstream code explicitly accepts them.

## Label Fields

`label_fields` names side arrays that must follow bbox/keypoint filtering. The lengths must match the corresponding `bboxes` or `keypoints` array before augmentation.

```python
result = transform(
    image=image,
    bboxes=[[10, 20, 80, 120], [100, 30, 140, 90]],
    class_labels=["cat", "dog"],
    scores=[0.95, 0.87],
)
```

Use `bbox_params=A.BboxParams(format="pascal_voc", label_fields=["class_labels", "scores"])` to keep both `class_labels` and `scores` aligned. Albumentations can encode and restore string labels, numeric labels, lists, tuples, and arrays through its label manager.

Important label rules:

- Every listed `label_fields` key must be present in the call.
- Every listed label field must have the same length as the associated target.
- Labels are removed from input data internally, appended to the processed target array, then restored as separate outputs.
- If all boxes/keypoints are filtered out, matching label fields are restored as empty containers of the original style where possible.

## Additional Targets

Use `additional_targets` when a custom key should be processed like a built-in target:

```python
transform = A.Compose(
    [A.HorizontalFlip(p=1.0)],
    additional_targets={"right_image": "image", "depth_mask": "mask"},
)
result = transform(image=left, right_image=right, depth_mask=depth)
```

Common mappings:

- Map another image-like array to `"image"` when it should receive image interpolation and color/intensity transforms.
- Map another mask-like array to `"mask"` when it should receive mask interpolation and avoid image-only intensity changes.
- Map another bbox collection to `"bboxes"` only when it should share the main `bbox_params` contract.
- Map another keypoint collection to `"keypoints"` only when it should share the main `keypoint_params` contract.
- Use built-in `images`, `masks`, `volume`, `volumes`, `mask3d`, and `masks3d` keys when the data naturally fits those batched/3D contracts.

## 3D Volumes and 3D Masks

Albumentations 2.0.8 includes 3D transforms such as `Pad3D`, `PadIfNeeded3D`, `CenterCrop3D`, `RandomCrop3D`, `CoarseDropout3D`, and `CubicSymmetry`. These operate on `volume`, `mask3d`, and in some cases `keypoints`.

Shape conventions:

- Single volume: `D,H,W` or `D,H,W,C`.
- Batch of volumes: `N,D,H,W` or `N,D,H,W,C`.
- Single 3D mask: `D,H,W` or `D,H,W,C`.
- Batch of 3D masks: `N,D,H,W` or `N,D,H,W,C`.
- 3D keypoints use `KeypointParams(format="xyz")`; the point order is `[x, y, z]`, while volume indexing is `[z, y, x]`.
- 3D padding parameters use depth, height, width ordering; explicit side padding is `(depth_front, depth_back, height_top, height_bottom, width_left, width_right)`.

Example:

```python
transform = A.Compose(
    [A.PadIfNeeded3D(min_zyx=(16, 128, 128), fill=0, fill_mask=0, p=1.0)],
    keypoint_params=A.KeypointParams(format="xyz", label_fields=["point_labels"]),
)
result = transform(volume=volume, mask3d=mask3d, keypoints=points_xyz, point_labels=labels)
```
