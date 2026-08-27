# Transform Workflows

## Migrate Older Random-Style Snippets

When an old snippet uses `RandomFlip`, `RandomAffine`, `RandomNoise`, or `RandomGamma`, translate it to TorchIO 2.0 by removing `Random` and moving randomness into ranges, `Choice`, distributions, and `p`.

```python
import torchio as tio

augmentation = tio.Compose([
    tio.Flip(axes=(0, 1, 2), flip_probability=0.5, p=0.5),
    tio.Affine(degrees=(-15, 15), translation=(-5, 5), p=0.8),
    tio.Noise(std=(0.01, 0.08), p=0.5),
    tio.Gamma(log_gamma=(-0.3, 0.3), p=0.5),
])
```

Migration checklist:

1. Replace old class names with `Flip`, `Affine`, `Noise`, `Blur`, `Gamma`, `Motion`, `BiasField`, `Spike`, `Ghosting`, or another current class.
2. Use scalar values for deterministic effects and tuples for random ranges.
3. Keep transform-wide probability in `p`; for `Flip`, use `flip_probability` for per-axis flip sampling.
4. Update normalization code to keyword-only `Normalize(out_min=..., out_max=..., in_min=..., in_max=...)` or `RescaleIntensity(...)`.
5. Replace `ScalarImage(source=tensor)` with `ScalarImage(tensor)` and `LabelMap(source=tensor)` with `LabelMap(tensor)`.

## Build a Mixed Scalar/Label Pipeline

Use one `Subject` containing scalar modalities and label maps. Spatial transforms keep them aligned; intensity transforms operate only on scalar images.

```python
import torch
import torchio as tio

subject = tio.Subject(
    t1=tio.ScalarImage(torch.rand(1, 64, 64, 48)),
    t2=tio.ScalarImage(torch.rand(1, 64, 64, 48)),
    seg=tio.LabelMap(torch.randint(0, 4, (1, 64, 64, 48))),
)

preprocess = tio.Compose([
    tio.Resample(target=1.0, image_interpolation="linear", label_interpolation="nearest"),
    tio.CropOrPad(target_shape=(64, 64, 64)),
    tio.Normalize(out_min=-1, out_max=1, include=["t1", "t2"]),
])

augment = tio.Compose([
    tio.Flip(axes="LR", flip_probability=0.5, p=0.5),
    tio.Affine(
        degrees=(-10, 10),
        translation=(-4, 4),
        image_interpolation="linear",
        label_interpolation="nearest",
        p=0.8,
    ),
    tio.OneOf({
        tio.Noise(std=(0.01, 0.05)): 0.4,
        tio.Blur(std=(0.5, 1.5)): 0.3,
        tio.BiasField(coefficients=(0.1, 0.5)): 0.3,
    }, p=0.8),
])

pipeline = preprocess + augment
out = pipeline(subject)
assert out.t1.spatial_shape == out.seg.spatial_shape
```

## Restrict Transforms with Include/Exclude

Use exact subject image keys, not image types or filenames.

```python
pipeline = tio.Compose([
    tio.Normalize(out_min=0, out_max=1, include=["t1"]),
    tio.Gamma(log_gamma=0.2, exclude=["t2"]),
    tio.Flip(axes=(0,), include=["t1", "t2", "seg"]),
])
```

Guidance:

- Intensity transforms already select `ScalarImage` instances only, so `include`/`exclude` primarily separates modalities.
- Spatial transforms affect `ScalarImage`, `LabelMap`, `Points`, and `BoundingBoxes` consistently for selected keys.
- `include=[]` or misspelled keys can produce an exact no-op; check `subject.images.keys()` before building the transform.

## Use Per-Instance Batch Augmentation

When a `SubjectsBatch` from a loader is passed to transforms, supported transforms sample independent parameters per element by default.

```python
batch_augment = tio.Compose([
    tio.Flip(axes=(0, 1, 2), flip_probability=0.5),
    tio.Noise(std=(0.01, 0.08)),
    tio.SomeOf(
        [tio.Gamma(log_gamma=(-0.3, 0.3)), tio.Blur(std=(0.5, 1.5))],
        num_transforms=1,
    ),
])
```

Use `per_instance=False` when the entire batch must receive the same sampled operation:

```python
shared = tio.OneOf(
    [tio.Flip(axes=(0,)), tio.Flip(axes=(1,))],
    per_instance=False,
)
```

Be careful with per-instance `OneOf`/`SomeOf`: children must preserve shape and schema so the transformed elements can be stacked again. Avoid mixing `CropOrPad`, `Resize`, or label-creating transforms in per-element compositions unless every branch returns identical keys and shapes.

## Validate History, Replay, and Inverse

Use transform history for debugging, reproducibility, and inversion.

```python
out = pipeline(subject)
for trace in out.applied_transforms:
    print(trace.name, trace.params)

inverse = out.get_inverse_transform()
restored = out.apply_inverse_transform(ignore_intensity=True)
```

Rules:

- `Compose` records child transforms rather than one opaque parent.
- `OneOf` and `SomeOf` record the selected child transforms.
- `apply_inverse_transform()` skips non-invertible transforms and can warn.
- Use `ignore_intensity=True` when only spatial restoration matters after noisy/intensity augmentation.
- Per-element batch history cannot be represented as a single composed inverse; call `apply_inverse_transform()` on the batch or unbatch subjects.

## Export Hydra-Compatible Config

Transforms can emit configuration dictionaries for reproducible experiment setup.

```python
pipeline = tio.Compose([
    tio.Flip(axes=(0, 1), p=0.5),
    tio.Noise(std=(0.01, 0.1)),
])
cfg = pipeline.to_hydra()
```

The result contains `_target_` entries such as `torchio.Compose`, `torchio.Flip`, and `torchio.Noise`. Instantiate it with Hydra in the consuming project when Hydra is available.

## Use MONAI and Cornucopia Adapters

Wrap external transforms only when the optional package is installed.

```python
# MONAI array transform example
from monai.transforms import NormalizeIntensity
import torchio as tio

pipeline = tio.Compose([
    tio.MonaiAdapter(NormalizeIntensity(), include=["t1"]),
    tio.Noise(std=0.05),
])
```

```python
# Cornucopia example; exact transform names depend on Cornucopia version
import cornucopia as cc
import torchio as tio

pipeline = tio.Compose([
    tio.CornucopiaAdapter(cc.GaussianNoiseTransform(sigma=0.05), include=["t1"]),
])
```

Adapter caveats:

- `MonaiAdapter` array transforms apply separately to each selected scalar image; random array transforms may not share spatial parameters across modalities. Prefer MONAI dictionary transforms when alignment matters.
- `CornucopiaAdapter` passes all selected tensors together so Cornucopia spatial transforms can share random parameters.
- Adapters do not record themselves as TorchIO history and are not invertible through TorchIO.

## Quick Synthetic Validation Pattern

Before wiring a training pipeline, validate on synthetic tensors:

```python
import torch
import torchio as tio

subject = tio.Subject(
    image=tio.ScalarImage(torch.linspace(0, 1, 16**3).reshape(1, 16, 16, 16)),
    label=tio.LabelMap(torch.randint(0, 2, (1, 16, 16, 16))),
)

pipeline = tio.Compose([
    tio.Normalize(out_min=-1, out_max=1, include=["image"]),
    tio.Flip(axes=(0,), p=1),
])
out = pipeline(subject)
assert out.image.shape == subject.image.shape
assert out.label.shape == subject.label.shape
assert len(out.applied_transforms) >= 2
```

The bundled scripts provide fuller checks for history/inverse and include/exclude routing.
