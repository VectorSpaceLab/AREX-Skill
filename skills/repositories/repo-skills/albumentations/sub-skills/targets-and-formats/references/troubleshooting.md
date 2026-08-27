# Troubleshooting Targets and Formats

Use this reference when Albumentations rejects target data, silently filters annotations, or produces outputs whose labels no longer match annotations.

## Quick Triage

1. Print the exact `Compose(...)` contract: `bbox_params`, `keypoint_params`, `additional_targets`, `strict`, and `is_check_shapes`.
2. Print input keys and shapes before augmentation.
3. Confirm every target key is named, not positional.
4. Confirm `bboxes` has `bbox_params` and `keypoints` has `keypoint_params`.
5. Confirm every `label_fields` item exists and has the same length as the target array.
6. Run `scripts/validate_targets.py` on a tiny JSON fixture if the problem is format/shape related.

## Wrong Bbox Format

Symptoms:

- Error says bbox coordinates must be in `[0.0, 1.0]`.
- Boxes appear in the wrong image locations after augmentation.
- YOLO boxes are treated as corners or Pascal VOC boxes are treated as centers.

Fix:

- Use `format="pascal_voc"` for pixel corners `[x_min, y_min, x_max, y_max]`.
- Use `format="coco"` for pixel `[x_min, y_min, width, height]`.
- Use `format="albumentations"` for normalized corners `[x_min, y_min, x_max, y_max]`.
- Use `format="yolo"` for normalized center boxes `[x_center, y_center, width, height]`.
- Do not normalize Pascal VOC/COCO pixel boxes manually unless you also switch to a normalized format.

Validator command example:

```bash
python skills/albumentations/sub-skills/targets-and-formats/scripts/validate_targets.py \
  --image-shape 480,640 \
  --bbox-format yolo \
  --bboxes '[[0.5, 0.5, 0.2, 0.3]]' \
  --labels '[1]'
```

## Normalized vs Pixel Coordinate Confusion

Symptoms:

- Pixel boxes such as `[50, 40, 100, 120]` fail in `yolo` or `albumentations` mode.
- Normalized boxes such as `[0.1, 0.2, 0.4, 0.5]` become tiny when declared as `pascal_voc`.
- COCO boxes with normalized width/height behave like near-zero pixel boxes.

Fix:

- Decide units before building `BboxParams`; Albumentations does not infer bbox units.
- Use image `height,width` only for conversion between pixel and normalized formats.
- For YOLO, all four numbers are normalized and represent center/size.
- For Albumentations format, all four numbers are normalized and represent corners.

## Labels Do Not Match Boxes or Keypoints

Symptoms:

- Error says lengths of target and label field do not match.
- Labels are missing after augmentation.
- The wrong class is attached to a transformed box.

Fix:

- Put side arrays in `label_fields`, not in unrelated custom keys.
- Ensure `len(class_labels) == len(bboxes)` before augmentation.
- Ensure `len(keypoint_labels) == len(keypoints)` before augmentation.
- Include all side arrays that must be filtered together, such as `class_labels`, `scores`, `track_ids`, or `joint_names`.
- Do not mutate label arrays separately after augmentation; use the labels returned by the transform.

Good pattern:

```python
bbox_params=A.BboxParams(format="pascal_voc", label_fields=["class_labels", "scores"])
```

## Invisible Keypoints Removed Unexpectedly

Symptoms:

- Keypoint count decreases after crop, rotate, pad, or resize.
- Skeleton indices no longer match a fixed model output layout.
- Label arrays are shorter after augmentation.

Cause:

- `KeypointParams(remove_invisible=True)` is the default. It filters points outside `[0,width)`, `[0,height)`, and for 3D `[0,depth)` after transforms.

Fix:

- If a fixed skeleton length is required, set `remove_invisible=False` and handle visibility flags downstream.
- If filtering is desired, always put joint names/labels in `label_fields` so labels are filtered in sync.
- For 3D, remember keypoints are `[x,y,z]` while volume indexing is `[z,y,x]`; an apparently valid point can have swapped axes and be filtered.

## Shape Mismatches

Symptoms:

- Error says height and width of image, mask, or masks should be equal.
- Error says depth, height, and width of volume, mask3d, volumes, and masks3d should be equal.
- Error says a target must be a 3D/4D/5D array.

Fix:

- For `image`, `mask`, and each item in `masks`/`images`, align `H,W` before augmentation.
- For `volume` and `mask3d`, align `D,H,W` before augmentation.
- For `volumes` and `masks3d`, use `N,D,H,W` or `N,D,H,W,C`.
- Use `is_check_shapes=False` only when shape mismatch is intentional and every transform in the pipeline can handle it safely.
- Do not pass a 2D segmentation mask as `mask3d`; use `mask` for `H,W` data.

## 3D Target Keys Omitted

Symptoms:

- A 3D mask is not transformed with a volume.
- 3D transforms run on `volume` but not on a companion target.
- A transform complains that no image or volume was found.

Fix:

- Pass the 3D image-like array as `volume` or `volumes`.
- Pass the 3D mask as `mask3d` or `masks3d`.
- For 3D keypoints, pass `keypoints` plus `keypoint_params=A.KeypointParams(format="xyz", ...)`.
- Do not use arbitrary names like `ct` or `seg3d` unless they are declared through `additional_targets` and mapped to a built-in target type.

## Empty Arrays

Symptoms:

- A no-object sample crashes while object samples work.
- Empty bboxes or keypoints produce shape errors.
- Label fields are nonempty while target arrays are empty.

Fix:

- Use empty lists consistently: `bboxes=[]`, `class_labels=[]`, `keypoints=[]`, `keypoint_labels=[]`.
- For arrays, use explicit zero-row shapes such as `(0,4)` for boxes and `(0,2)` or `(0,3)` for keypoints depending on format.
- Keep all label fields empty when the target is empty.
- Avoid `None`; it means missing data, not an empty annotation set.

## Additional Target Misrouting

Symptoms:

- A depth map or segmentation mask receives brightness/color transforms.
- A paired image does not receive the same crop/flip.
- Strict mode rejects a custom key.

Fix:

- Map image-like paired inputs to `"image"`: `additional_targets={"right_image": "image"}`.
- Map dense labels/depth/masks to `"mask"`: `additional_targets={"depth": "mask"}`.
- Map extra bbox/keypoint collections to `"bboxes"`/`"keypoints"` only when they share the main parameter object and label strategy.
- With `strict=True`, every nonstandard target key must be known through `additional_targets` or be a supported built-in key.

## Boxes Disappear After Crops

Symptoms:

- Detection samples lose most or all boxes after augmentation.
- Labels become empty because all boxes are filtered.

Fix:

- Lower `min_visibility` or `min_area` if the filtering is too aggressive.
- Prefer bbox-aware crop transforms for detection workflows; route transform selection to `../transform-catalog/`.
- Keep `clip=True` for boxes near image boundaries.
- Use `save_applied_params=True` or replay tooling from `../serialization-and-reproducibility/` if you need to inspect the exact crop that removed a box.

## Keypoint Angle Problems

Symptoms:

- Angles look wrapped or unexpectedly converted.
- A keypoint format with angle is accepted but downstream angle units are wrong.

Fix:

- By default, `KeypointParams(angle_in_degrees=True)` treats input angles as degrees and returns degrees.
- Set `angle_in_degrees=False` for radians.
- Internally Albumentations normalizes angles to `[0, 2π)` radians, so negative or large angles may wrap.

## Minimal Known-Good Smoke Tests

2D detection smoke:

```python
result = transform(
    image=np.zeros((100, 100, 3), dtype=np.uint8),
    bboxes=[[10, 10, 30, 30]],
    class_labels=["object"],
)
assert len(result["bboxes"]) == len(result["class_labels"])
```

3D segmentation smoke:

```python
result = transform(
    volume=np.zeros((8, 64, 64), dtype=np.uint8),
    mask3d=np.zeros((8, 64, 64), dtype=np.uint8),
)
assert result["volume"].shape[:3] == result["mask3d"].shape[:3]
```
