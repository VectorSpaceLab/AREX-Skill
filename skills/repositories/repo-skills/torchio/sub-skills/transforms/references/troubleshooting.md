# Transform Troubleshooting

## `RandomFlip` or `RandomAffine` Is Missing

TorchIO 2.0 uses unified transform classes. Replace old `Random*` names with current class names and express randomness through parameter ranges and `p`.

```python
# TorchIO 2.0 style
tio.Flip(axes=(0, 1, 2), flip_probability=0.5, p=0.5)
tio.Affine(degrees=(-15, 15), translation=(-5, 5), p=0.8)
tio.Noise(std=(0.01, 0.05), p=0.5)
```

If old examples use `source=tensor`, construct in-memory images as `tio.ScalarImage(tensor)` or `tio.LabelMap(tensor)`.

## `TypeError` from Positional or Old Keyword Arguments

Many TorchIO 2.0 transform parameters are keyword-only. Common fixes:

- Use `tio.Normalize(out_min=0, out_max=1, in_min=-1000, in_max=1000)`, not positional min/max arguments.
- Use `tio.CropOrPad(target_shape=(128, 128, 128))` when clarity matters.
- Use `tio.Flip(axes=(0,), flip_probability=0.5)`, not `axis=` or old random-transform arguments.
- Use `tio.Affine(degrees=10, translation=5, scales=1.1)` for affine augmentation.

## Transform Runs but Nothing Changes

Likely causes:

- `p=0` or batch-level/per-element probability gates skipped every element.
- The parameter is identity: `Affine()` has no rotation/translation/scale change; `Gamma(log_gamma=0)` is identity; `Blur(std=0)` is identity.
- `include` names do not match any `Subject` image key.
- An intensity transform was applied to a subject containing only `LabelMap` images.
- `Flip(..., flip_probability=0)` sampled no axes to flip.
- `SomeOf(..., num_transforms=0)` or an empty `Compose([])` was used.

Check `subject.images.keys()`, inspect `out.applied_transforms`, and run a bundled smoke script with a known synthetic tensor.

## Include/Exclude Does Not Affect the Expected Image

`include` and `exclude` operate on exact image keys in a `Subject`, such as `"t1"`, `"t2"`, or `"seg"`. They are not modality names, filenames, image classes, or glob patterns.

Debug pattern:

```python
print(subject.images.keys())
transform = tio.Gamma(log_gamma=0.5, include=["t1"])
out = transform(subject)
print([trace.name for trace in out.applied_transforms])
```

If the selected set is empty, the transform can be a no-op while still returning a valid subject. Prefer positive `include` lists in multi-modal pipelines and assertions that protected images are unchanged.

## Label Maps Become Fractional or Blurry

Use label-safe interpolation for spatial transforms. Defaults generally use nearest-neighbor for `LabelMap`, but set it explicitly when debugging or when using low-level/general transforms:

```python
tio.Affine(
    degrees=(-10, 10),
    image_interpolation="linear",
    label_interpolation="nearest",
)
```

Do not apply scalar intensity transforms to label maps. If using `Lambda`, set `types_to_apply="label"` only for label-safe operations such as thresholding or remapping.

## Zero Intensity Range Warning

`Normalize`/`RescaleIntensity` warn when the computed input range is zero. This can happen with constant images, a mask selecting only constant voxels, or explicit `in_min == in_max`.

Fixes:

- Check the input image is not constant.
- Check `masking_method` selects enough non-constant voxels.
- Provide meaningful `in_min` and `in_max` values.
- Skip normalization for empty or sentinel modalities with `exclude`.

## Inverse or History Does Not Restore Data

History inversion only works for transforms that record enough information and implement `inverse()`. Common limitations:

- `Blur`, destructive label cleanup, and external adapters are not invertible.
- Noise/artifacts may be skipped during inverse, depending on transform support.
- `get_inverse_transform()` cannot represent per-element histories from batched `OneOf`/`SomeOf`; call `apply_inverse_transform()` on the batch or unbatch subjects.
- Use `ignore_intensity=True` when you want to restore geometry but not undo intensity augmentations.
- Applying inverse returns a new object when `copy=True`; do not expect the transformed input to mutate in place.

Inspect records:

```python
for trace in transformed.applied_transforms:
    print(trace.name, trace.params)
restored = transformed.apply_inverse_transform(ignore_intensity=True)
```

## Per-Instance Batch Errors

Per-instance augmentation is active by default on `SubjectsBatch` for supported transforms. It can fail when per-element branches return different keys or shapes.

Fixes:

- For `OneOf`/`SomeOf`, use child transforms that preserve shape and schema.
- Move shape-changing preprocessing (`CropOrPad`, `Resize`, label synthesis) before batching or use `per_instance=False`.
- If every batch element should receive the same operation, set `per_instance=False`.

## MONAI or Cornucopia Adapter Fails

Optional dependencies are not installed with the core package unless the environment includes the relevant extras.

- MONAI adapter: install/use an environment with the `monai` extra, then pass a callable MONAI transform to `tio.MonaiAdapter(...)`.
- Cornucopia adapter: install/use `cornucopia`, then pass a callable Cornucopia transform to `tio.CornucopiaAdapter(...)`.
- External adapters do not record TorchIO history and are not invertible through TorchIO.
- MONAI random array transforms can sample different parameters for each scalar image; use MONAI dictionary transforms when multi-modal alignment matters.

## Spatial Metadata or Shape Is Unexpected

- Prefer `Resample(target=spacing_or_reference)` for spacing changes.
- Use `CropOrPad(target_shape=...)` for fixed shapes after resampling.
- Use `Resize(target_shape=...)` only when changing tensor shape while accepting spacing changes to preserve field of view.
- After `CropOrPad` on `Subject`/`Image`, history may include `Pad`, `Crop`, and `CropOrPad` records because lazy operations are decomposed.

## Hydra Config Surprises

`to_hydra()` serializes current transform configuration, including non-default arguments. It does not serialize arbitrary Python callables safely. Avoid expecting `Lambda` functions or opaque external adapter objects to round-trip through Hydra without custom project code.
