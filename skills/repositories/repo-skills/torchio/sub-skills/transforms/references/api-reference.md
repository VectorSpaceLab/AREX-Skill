# Transform API Reference

## Base Transform Contract

All public TorchIO transforms subclass `tio.Transform`, a `torch.nn.Module`. They accept `Subject`, `Image`, 4D `torch.Tensor`, NumPy arrays, SimpleITK/NiBabel images, MONAI-style dictionaries, `ImagesBatch`, or `SubjectsBatch`, and return the same type.

Common keyword-only base arguments:

| Argument | Meaning |
| --- | --- |
| `p=1.0` | Probability that the transform applies. For supported batched transforms with `per_instance=True`, this gates each batch element independently. |
| `copy=True` | Deep-copy the input before applying. `Compose`, `OneOf`, and `SomeOf` copy once and temporarily run children with `copy=False`. |
| `per_instance=True` | For real batches, sample independent parameters and/or gates per element when the transform supports it. Set `False` for one shared parameter set across the whole batch. |
| `include=None` | Exact image keys to transform. |
| `exclude=None` | Exact image keys to skip. |

TorchIO 2.0 transform names are not the older `Random*` names. Use `tio.Flip`, `tio.Affine`, `tio.Noise`, `tio.Blur`, `tio.Gamma`, etc.; random behavior comes from parameter ranges, `Choice`, distributions, and `p`.

## Parameter Ranges and Choices

Transform parameters that represent strengths or geometry support these forms:

- `0.5`: deterministic value, usually broadcast over axes.
- `(0.1, 0.3)`: uniform range sampled each call.
- `(1.0, 2.0, 3.0)`: deterministic per-axis values when the parameter is 3D.
- `(0, 1, 10, 20, 100, 200)`: per-axis ranges for some 3D parameters.
- `tio.Choice([-90, 0, 90])`: discrete random value.
- `torch.distributions.Uniform(...)` or another distribution: custom random sampling.

Augmentation transforms whose strength defaults to identity may warn that they are no-ops when constructed without meaningful parameters, e.g. `Affine()` with identity defaults or `Blur(std=0)`.

## Composition Classes

| Class | Use |
| --- | --- |
| `tio.Compose([...])` | Apply every transform sequentially. Also available with operator sugar: `t1 + t2`. |
| `tio.OneOf([...])` | Choose exactly one transform with equal weights. |
| `tio.OneOf({transform: weight, ...})` | Choose exactly one transform using relative weights. |
| `tio.SomeOf([...], num_transforms=2)` | Choose a fixed number of transforms. |
| `tio.SomeOf([...], num_transforms=(1, 3), replace=False)` | Choose a random subset count, optionally with replacement. |
| `t1 | t2` | Build a `OneOf` from transforms. |

For `SubjectsBatch` inputs with `per_instance=True`, `OneOf` and `SomeOf` choose independently per batch element. This requires child transforms to preserve shape and schema so elements can be stacked again. Pass `per_instance=False` for one shared choice/subset across the batch.

## Intensity Transforms

Intensity transforms affect `ScalarImage` data and leave `LabelMap` data untouched unless a specific transform is label-oriented.

| Transform | Main purpose | Notes |
| --- | --- | --- |
| `Normalize` / `RescaleIntensity` | Clip and linearly map intensity values. | Constructor uses keyword-only `out_min`, `out_max`, `in_min`, `in_max`, percentile, and `masking_method` arguments. Inverse-capable when history contains ranges. |
| `Standardize` / `ZNormalization` | Z-score standardization. | Supports masking; inverse records mean/std. |
| `HistogramStandardization` | Map intensities with landmarks. | Use `include` for modality-specific landmark sets. |
| `Clamp` | Clamp values to a min/max. | Useful before normalization. |
| `Mask` | Mask scalar intensities using a label map or tensor mask. | Labels select included voxels. |
| `Noise` | Add Gaussian noise. | Supports per-instance parameters/probability. |
| `Blur` | Gaussian smoothing. | Not invertible. |
| `Gamma` | Gamma intensity transform. | Supports per-instance parameters/probability and inverse replay. |
| `BiasField` | Multiplicative MRI bias field. | Supports per-instance parameters/probability and inverse replay. |
| `Motion`, `Ghosting`, `Spike` | MRI artifact simulations. | Useful in augmentation `OneOf` groups. |
| `Anisotropy` | Simulate low-resolution acquisition along an axis. | Spatial-like artifact that preserves target shape. |
| `Swap` | Self-supervised patch swapping. | Supports per-instance parameters/probability. |
| `PCA` | PCA-based intensity augmentation. | Requires fitted components/parameters. |
| `LabelsToImage` | Synthesize scalar image from label map. | Use `label_key` to choose the label source. |

## Spatial Transforms

Spatial transforms affect all selected images, points, and bounding boxes consistently. `ScalarImage` interpolation defaults to linear-like interpolation; `LabelMap` interpolation defaults to nearest-neighbor.

| Transform | Main purpose | Notes |
| --- | --- | --- |
| `Flip(axes=..., flip_probability=...)` | Flip along spatial or anatomical axes. | `axes` accepts `0/1/2` or labels such as `"LR"`; invertible. |
| `Spatial(...)` | General affine + elastic transform. | Exposes affine matrix, elastic control points, interpolation, padding, and output-space options. |
| `Affine(...)` | Rotation, scaling, shearing, translation. | Convenience wrapper around `Spatial`; use `degrees`, `translation`, `scales`, `isotropic`, `center`. |
| `ElasticDeformation(...)` | Dense elastic deformation. | Uses control points or random displacement grid. |
| `Resample(target=...)` | Change voxel spacing or match reference space. | Prefer over `Resize` for medical image spacing changes. |
| `Resize(target_shape=...)` | Change tensor shape while preserving FOV. | Warn agents that this changes spacing anisotropically; labels use nearest interpolation. |
| `CropOrPad(target_shape=...)` | Force a fixed spatial shape. | Supports voxel/mm/cm units, padding mode, crop/pad-only, center/random location. |
| `Crop`, `Pad` | Explicit crop or pad margins. | Inverse-capable as paired operations. |
| `Reorient(orientation=...)` | Change orientation code. | Invertible with recorded prior orientation. |
| `EnsureShapeMultiple(k)` | Pad/crop shape to multiples. | Useful before U-Nets. |
| `Transpose` | Swap spatial axes. | Self-inverse. |
| `CopyAffine(target=...)` | Copy affine from a reference image key. | Use when image geometry metadata must match. |
| `ToReferenceSpace(reference=...)` | Move image to another reference space. | Reference is an image object, not a path in runtime docs. |

## Label Transforms

| Transform | Main purpose |
| --- | --- |
| `RemapLabels(mapping)` | Map label values; invertible when mapping is one-to-one. |
| `RemoveLabels(labels)` | Set selected labels to background. |
| `SequentialLabels()` | Renumber labels to compact sequential values; inverse-capable with history. |
| `KeepLargestComponent(labels=...)` | Keep largest connected component for selected labels. |
| `Contour()` | Convert labels to contour/boundary labels. |
| `OneHot()` | Convert label map to one-hot channels; inverse uses argmax. |

## Lambda and Adapters

- `tio.Lambda(function, types_to_apply="scalar")` applies a callable to each matching 4D tensor. Use `types_to_apply="label"` for label maps or `None` for all images.
- `tio.MonaiAdapter(monai_transform, include=..., exclude=...)` wraps MONAI dictionary or array transforms. Dictionary transforms operate on the subject dictionary; array transforms apply to each selected `ScalarImage`. Requires the `monai` extra. It does not record itself in TorchIO history.
- `tio.CornucopiaAdapter(cornucopia_transform, include=..., exclude=...)` wraps Cornucopia transforms and passes selected scalar images first, then label maps, so spatial parameters can be shared. Requires the `cornucopia` package. It is not invertible through TorchIO and does not record itself in history.

## History and Inverse APIs

- Applied transforms are stored as `AppliedTransform(name, params)` records on `subject.applied_transforms`.
- `subject.applied_transforms` is the current replay record; inspect each `AppliedTransform.name` and `.params` when you need to audit what happened.
- `subject.get_inverse_transform()` returns a `Compose` inverse for recorded history when possible. For complex per-element batch history, prefer `apply_inverse_transform()` on the transformed data.
- `subject.apply_inverse_transform(ignore_intensity=False, warn=True)` applies inverse-capable history in reverse order and skips non-invertible transforms with warnings.
- `tio.apply_inverse_transform(data, ...)` is the standalone equivalent.
- Per-element batch history can be cleared with `clear_history()` on batch-like data.

Not every transform is invertible. Invertible examples include `Flip`, `Crop`, `Pad`, `Reorient`, `Normalize`, `Standardize`, `Gamma`, `BiasField`, label remapping/sequential operations when recorded, and many `Spatial`/`Affine` cases with enough output-space metadata. Non-invertible examples include `Blur`, stochastic external adapters, and destructive label cleanup.
