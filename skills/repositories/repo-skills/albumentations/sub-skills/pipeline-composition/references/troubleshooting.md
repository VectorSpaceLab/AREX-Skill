# Pipeline Composition Troubleshooting

Use this guide for `Compose` and composition-block failures. For bbox/keypoint format details, route to `../targets-and-formats/`; for replay/save/load, route to `../serialization-and-reproducibility/`.

## Quick Diagnosis

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `Key image_2 is not in available keys.` | `strict=True` with an undeclared custom key. | Add `additional_targets={"image_2": "image"}` or pass only supported keys. |
| `Height and Width of image, mask or masks should be equal...` | `is_check_shapes=True` and image/mask-like targets differ in H/W. | Resize/fix data before the pipeline, map custom keys correctly, or set `is_check_shapes=False` only when safe. |
| `Depth, Height and Width of volume... should be equal...` | Volume/mask3d targets differ in D/H/W. | Fix target construction or route volume format details to `../targets-and-formats/`. |
| `image must be numpy array type` | Required image-like key is `None` or not a NumPy array. | Pass `np.ndarray` values for `image`, `mask`, and image/mask additional targets. |
| `bbox_params must be specified...` | Bboxes are present but no bbox processor was configured. | Add `bbox_params=A.BboxParams(...)` and required `label_fields`. |
| Missing labels after bbox/keypoint augmentation | Label fields were not declared or did not match target lengths. | Route to `../targets-and-formats/` and declare `label_fields`. |
| Same `np.random.seed()` gives different augmentation | Compose ignores global NumPy/Python random seeds. | Use `A.Compose(..., seed=137)` or `pipeline.set_random_seed(137)`. |
| `All elements must be instances of BasicTransform...` | Operator `+` received a string, `None`, dict, number, or nested compose block. | Append/prepend only transform instances; rebuild explicitly for nested compose blocks. |
| `Can only remove BasicTransform classes...` | Operator `-` received an instance or non-transform type. | Use a transform class: `pipeline - A.HorizontalFlip`. |
| Masks/depth look blurred after resize/rotate | Mask-like target used image interpolation or transform-level override was not set as intended. | Map custom masks/depth to `mask` and set top-level `mask_interpolation` to nearest-neighbor when needed. |

## Invalid Keys Under Strict Mode

`strict=True` makes `Compose` validate input keys. This is useful during pipeline development because typos fail early.

Failing pattern:

```python
pipeline = A.Compose([A.HorizontalFlip(p=1)], strict=True)
pipeline(image=image, depth=depth)  # depth is unknown
```

Fix with an additional target:

```python
pipeline = A.Compose(
    [A.HorizontalFlip(p=1)],
    additional_targets={"depth": "mask"},
    strict=True,
)
pipeline(image=image, depth=depth)
```

Choose the mapped target type by semantics:

- Use `"image"` for another image that should receive image interpolation and image-only transforms.
- Use `"mask"` for segmentation masks, depth maps, or label rasters that should receive geometric transforms with mask interpolation.
- Route bbox/keypoint/volume questions to `../targets-and-formats/`.

## Shape Mismatches

By default, `Compose` checks matching H/W for image-like and mask-like targets. This catches common segmentation bugs before transforms run.

Common fixes:

1. Verify every `image`, `mask`, `masks`, `images`, and additional image/mask target is a NumPy array or valid list/array container.
2. Confirm additional targets are mapped to the right internal type before strict validation.
3. Resize or pad data before augmentation if targets are genuinely expected to align.
4. Use `is_check_shapes=False` only when the selected transforms do not require aligned shapes.

For identical geometry across `image`, `mask`, and `depth`, prefer:

```python
pipeline = A.Compose(
    [A.Resize(256, 256, p=1), A.Rotate(limit=10, p=1)],
    additional_targets={"depth": "mask"},
    is_check_shapes=True,
    mask_interpolation=0,
    strict=True,
)
result = pipeline(image=image, mask=mask, depth=depth)
```

## Single Transform Instead Of Sequence

`A.Compose(A.HorizontalFlip(p=1))` is accepted by wrapping the transform into a list, but it warns that a sequence is expected. Prefer:

```python
pipeline = A.Compose([A.HorizontalFlip(p=1)])
```

The same sequence convention applies to `OneOf`, `SomeOf`, `RandomOrder`, `Sequential`, and `SelectiveChannelTransform`.

## Missing Label Fields

When bboxes or keypoints are present, `Compose` needs target processors and label fields when labels are carried separately from coordinates. A pipeline that transforms `bboxes` but omits `bbox_params` fails before transforms run. A pipeline that omits `label_fields` can drop or desynchronize labels when filtering occurs.

Minimal pattern:

```python
pipeline = A.Compose(
    [A.HorizontalFlip(p=1)],
    bbox_params=A.BboxParams(format="pascal_voc", label_fields=["labels"]),
)
result = pipeline(image=image, bboxes=bboxes, labels=labels)
```

Route detailed bbox/keypoint format, clipping, filtering, and label-length repair to `../targets-and-formats/`.

## Seed And Reproducibility Confusion

Albumentations `Compose` owns its random state. These do not control a `Compose` instance:

```python
np.random.seed(137)
random.seed(137)
```

Use one of these instead:

```python
pipeline = A.Compose([...], seed=137)
pipeline.set_random_seed(137)
```

Debug checklist:

- If two separate pipelines should match, construct both with the same transform list and same `seed`.
- If the same pipeline should repeat the first result, call `set_random_seed(seed)` before each repeated call.
- If dataloader workers produce unexpected differences, remember that worker-aware seeding combines the base seed with `torch.initial_seed()` inside worker context.
- If exact transform parameters must be reused on another input, use `ReplayCompose`; route replay details to `../serialization-and-reproducibility/`.

## Operator Edit Failures

Valid edits:

```python
pipeline = A.Compose([A.HorizontalFlip(p=1)], strict=True, seed=137)
extended = pipeline + A.Blur(p=1)
prepended = A.Resize(256, 256, p=1) + pipeline
without_flip = pipeline - A.HorizontalFlip
```

Invalid edits and fixes:

| Invalid | Why | Fix |
| --- | --- | --- |
| `pipeline + "Blur"` | Not a transform instance. | `pipeline + A.Blur(p=1)`. |
| `pipeline + None` | Not a transform instance. | Build a filtered transform list before adding. |
| `pipeline + A.Sequential([...])` | Operators reject `BaseCompose` operands. | Rebuild explicitly with `A.Compose([*pipeline.transforms, A.Sequential([...])], ...)`. |
| `pipeline - A.HorizontalFlip()` | Subtraction expects a class. | `pipeline - A.HorizontalFlip`. |
| `pipeline - A.Blur` when no blur exists | No exact class match. | Inspect `type(t).__name__ for t in pipeline.transforms` before removing. |

Operator edits return new instances. If a later call still uses the original variable, assign the returned pipeline:

```python
pipeline = pipeline + A.Blur(p=1)
```

## Unexpected Mask Interpolation

Image interpolation and mask interpolation are separate. Many geometric transforms expose `interpolation` and `mask_interpolation`; `Compose(mask_interpolation=...)` overrides mask interpolation recursively when the value is not `None`.

Use top-level mask interpolation when a pipeline has nested choices and every mask-like target must use the same interpolation:

```python
pipeline = A.Compose(
    [A.OneOf([A.Resize(128, 128, p=1), A.Rotate(limit=15, p=1)], p=1)],
    additional_targets={"depth": "mask"},
    mask_interpolation=0,
)
```

If masks or depth maps become smooth after geometric transforms, verify:

- The custom target is mapped as `"mask"`, not `"image"`.
- Top-level `mask_interpolation` is set to a nearest-neighbor OpenCV flag when categorical values must remain discrete.
- The transform does not intentionally alter masks with a `fill_mask` or mask-specific parameter.
