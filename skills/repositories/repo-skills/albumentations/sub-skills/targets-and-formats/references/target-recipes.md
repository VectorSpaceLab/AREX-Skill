# Target Recipes

Use these recipes as starting points when a request is about target keys, annotation formats, and shape preservation. Choose transforms separately in `../transform-catalog/`; use this file to wire targets correctly.

## Object Detection with Pascal VOC Boxes

```python
import albumentations as A

transform = A.Compose(
    [
        A.RandomCrop(height=512, width=512, p=1.0),
        A.HorizontalFlip(p=0.5),
    ],
    bbox_params=A.BboxParams(
        format="pascal_voc",
        label_fields=["class_labels"],
        clip=True,
        filter_invalid_bboxes=True,
        min_visibility=0.1,
    ),
    strict=True,
)

augmented = transform(
    image=image,
    bboxes=[[24, 40, 180, 220], [300, 100, 360, 150]],
    class_labels=["person", "car"],
)
```

Checks before using this recipe:

- Confirm bbox coordinates are pixel corners, not COCO width/height and not YOLO center format.
- Confirm each label field length equals `len(bboxes)`.
- Expect filtered boxes to also remove matching labels.
- Keep `clip=True` if source boxes can slightly exceed image boundaries.

## Repair Invalid YOLO Boxes and Labels

YOLO bboxes are normalized `[x_center, y_center, width, height]`, not corner coordinates. Albumentations expects all four YOLO values to be in `(0, 1]` during validity checks.

```python
import albumentations as A

transform = A.Compose(
    [A.HorizontalFlip(p=0.5), A.RandomCrop(height=416, width=416, p=1.0)],
    bbox_params=A.BboxParams(
        format="yolo",
        label_fields=["class_ids"],
        clip=True,
        filter_invalid_bboxes=True,
        min_visibility=0.05,
        max_accept_ratio=20.0,
    ),
)

augmented = transform(image=image, bboxes=yolo_boxes, class_ids=class_ids)
```

Repair workflow:

1. Remove rows where label count and bbox count disagree; do not pad labels to hide the mismatch.
2. Ensure each YOLO row is `[x_center, y_center, width, height]`; convert corner boxes before declaring `format="yolo"`.
3. Reject or fix rows with zero/negative width or height.
4. For boxes partly outside the image, use `clip=True, filter_invalid_bboxes=True`; if the center or size is wildly outside `[0,1]`, correct the upstream converter first.
5. If too many objects disappear after crops, reduce `min_visibility`, choose bbox-safe crop transforms, or route crop selection to `../transform-catalog/`.

Small converter from Pascal VOC pixels to YOLO normalized:

```python
def pascal_voc_to_yolo(box, width, height):
    x_min, y_min, x_max, y_max = box
    return [
        ((x_min + x_max) / 2) / width,
        ((y_min + y_max) / 2) / height,
        (x_max - x_min) / width,
        (y_max - y_min) / height,
    ]
```

## COCO Boxes with Multiple Label Fields

```python
transform = A.Compose(
    [A.Resize(height=640, width=640, p=1.0)],
    bbox_params=A.BboxParams(
        format="coco",
        label_fields=["category_id", "iscrowd", "area"],
        min_area=4,
    ),
)

result = transform(
    image=image,
    bboxes=[[x, y, w, h] for x, y, w, h in coco_boxes],
    category_id=category_ids,
    iscrowd=iscrowd_flags,
    area=areas,
)
```

Notes:

- COCO boxes are pixel `[x_min, y_min, width, height]`.
- `area` supplied as a label field is kept aligned with the original object; Albumentations does not recompute semantic COCO metadata for you.
- If a downstream exporter needs updated area values after augmentation, recompute them from `result["bboxes"]`.

## Keypoints with Visibility Labels

```python
transform = A.Compose(
    [A.RandomCrop(height=256, width=256, p=1.0), A.Rotate(limit=15, p=0.5)],
    keypoint_params=A.KeypointParams(
        format="xy",
        label_fields=["joint_names", "visibility"],
        remove_invisible=True,
    ),
)

result = transform(
    image=image,
    keypoints=[[120, 80], [200, 140]],
    joint_names=["left_eye", "right_eye"],
    visibility=[2, 2],
)
```

Use `remove_invisible=False` when:

- The model target format requires fixed keypoint count.
- The target encoder has its own visibility flags.
- You will clip or mask off-image points yourself after augmentation.

If `remove_invisible=True`, labels are filtered with the keypoints, so fixed-index skeleton formats need a postprocessing step to reinsert missing joints or should keep invisible keypoints instead.

## 3D Keypoints in Volumes

```python
transform = A.Compose(
    [A.Pad3D(padding=(2, 8, 8), fill=0, fill_mask=0, p=1.0)],
    keypoint_params=A.KeypointParams(format="xyz", label_fields=["point_labels"]),
)

result = transform(
    volume=volume,          # shape D,H,W or D,H,W,C
    mask3d=mask3d,          # shape D,H,W or D,H,W,C
    keypoints=[[20, 30, 5]], # x,y,z point, not z,y,x
    point_labels=["lesion"],
)
```

Remember the two coordinate orders:

- Keypoint rows are `[x, y, z]`.
- NumPy volume indexing is `[z, y, x]`.
- Padding config is depth, height, width; explicit padding side order is `(front, back, top, bottom, left, right)`.

## 2D Segmentation with Image and Mask

```python
transform = A.Compose(
    [A.RandomCrop(height=384, width=384, p=1.0), A.HorizontalFlip(p=0.5)],
    strict=True,
)
result = transform(image=image, mask=mask)
```

Segmentation target rules:

- Use `mask` for one mask and `masks` for multiple masks.
- Keep masks as integer/label arrays where possible; transforms use mask interpolation for mask targets.
- Do not pass masks as `image` or `images`, or image-only intensity transforms can corrupt class ids.
- If `image` and `mask` shapes differ, fix preprocessing first or explicitly disable `is_check_shapes` only when the difference is intentional and safe.

## Extend a 2D Segmentation Pipeline to Volumes and Masks3D

Start from the 2D contract, then add 3D target keys and 3D-capable transforms:

```python
transform = A.Compose(
    [
        A.PadIfNeeded3D(min_zyx=(16, 256, 256), fill=0, fill_mask=0, p=1.0),
        A.RandomCrop3D(size=(16, 224, 224), p=1.0),
    ],
    strict=True,
)

result = transform(volume=volume, mask3d=mask3d)
```

Migration checklist:

- Rename the image-like 3D input to `volume`, not `image`.
- Rename the 3D mask to `mask3d`, not `mask`.
- Shape single samples as `D,H,W` or `D,H,W,C`; batch samples as `N,D,H,W` or `N,D,H,W,C` for `volumes`/`masks3d`.
- Use 3D transforms for depth-changing operations; many 2D geometric transforms operate slice-wise or target only `H,W` semantics.
- If using 3D keypoints, use `KeypointParams(format="xyz")` and label fields.

## Paired Images or Modalities

For paired image-like arrays that should receive the same geometry:

```python
transform = A.Compose(
    [A.RandomCrop(height=256, width=256, p=1.0), A.HorizontalFlip(p=0.5)],
    additional_targets={"right_image": "image", "nir_image": "image"},
)
result = transform(image=rgb, right_image=right_rgb, nir_image=nir)
```

For non-image dense labels such as depth maps or segmentation masks:

```python
transform = A.Compose(
    [A.RandomCrop(height=256, width=256, p=1.0)],
    additional_targets={"depth": "mask"},
)
result = transform(image=image, mask=segmentation, depth=depth_map)
```

Choose the mapping deliberately:

- `"image"` receives image-like processing, including image-only intensity/color transforms when supported.
- `"mask"` receives mask-like processing and avoids image-only photometric corruption.

## Multiple Images and Masks

Use built-in sequence keys when the target is naturally a stack or list:

```python
result = transform(
    image=image,
    images=[frame0, frame1, frame2],
    masks=[instance_mask0, instance_mask1],
)
```

Preflight checks:

- Nonempty `images` lists must contain NumPy arrays of compatible `H,W`.
- `masks` may be an empty list, a list of `H,W[,C]` arrays, or an array `N,H,W[,C]`.
- If transform output type matters, remember `images`/`masks` lists are restored as lists when supplied as lists.

## Empty Arrays

Empty bboxes and keypoints are supported when shaped consistently:

```python
empty_bboxes = []
empty_keypoints = []
result = transform(
    image=image,
    bboxes=empty_bboxes,
    class_labels=[],
    keypoints=empty_keypoints,
    keypoint_labels=[],
)
```

Practical rules:

- Keep empty label fields empty too.
- If using NumPy arrays, prefer shape `(0, 4)` for bboxes and `(0, len(format))` for keypoints.
- Do not pass `None` for `bboxes` or `keypoints`; use empty sequences when the sample has no annotations.
