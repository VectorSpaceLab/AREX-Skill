---
name: transforms
description: "Build TorchIO 2.0 preprocessing and augmentation pipelines with
  deterministic/random transforms, composition, include/exclude routing,
  per-instance batches, history, inverse replay, and MONAI/Cornucopia adapters."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# TorchIO Transforms

Use this sub-skill when an agent needs to design, migrate, debug, or validate TorchIO transform pipelines. It focuses on TorchIO 2.0 APIs: transform class names are `Flip`, `Affine`, `Noise`, `Gamma`, etc. rather than older `RandomFlip`/`RandomAffine` names, and random behavior is controlled by parameter ranges, `Choice`, distributions, and `p`.

## Route by Task

- **Build or migrate a pipeline**: start with [`references/workflows.md`](references/workflows.md) for preprocessing/augmentation patterns and TorchIO 2.0 migration notes.
- **Check constructor names and semantics**: use [`references/api-reference.md`](references/api-reference.md) for base arguments, transform families, composition, parameter ranges, adapters, and inverse/history APIs.
- **Debug transform behavior**: use [`references/troubleshooting.md`](references/troubleshooting.md) for include/exclude mistakes, no-op warnings, label interpolation, inverse limits, and optional dependency failures.
- **Validate history/inverse mechanics**: run [`scripts/transform_history_smoke.py`](scripts/transform_history_smoke.py) on synthetic tensors.
- **Validate scalar/label routing**: run [`scripts/include_exclude_smoke.py`](scripts/include_exclude_smoke.py) on synthetic tensors.

## Core TorchIO 2.0 Rules

- Construct in-memory images as `tio.ScalarImage(tensor)` and `tio.LabelMap(tensor)`, where tensors are 4D `(C, I, J, K)`.
- Use `tio.Normalize(...)` / `tio.RescaleIntensity(...)` with keyword-only range arguments such as `out_min`, `out_max`, `in_min`, and `in_max`.
- Use one transform class for fixed and random behavior: scalar parameters are deterministic, tuples are sampled ranges, `tio.Choice([...])` samples discrete values, and `torch.distributions.Distribution` objects can supply custom sampling.
- Apply `p` to gate a transform; in real `SubjectsBatch` inputs, transforms that support it use `per_instance=True` by default to sample/gate each element independently.
- Use `include=[...]` and `exclude=[...]` with exact image keys from a `Subject`; intensity transforms already skip `LabelMap` images unless they are label-aware transforms.
- Keep labels safe during spatial operations by relying on default `label_interpolation="nearest"` or setting it explicitly when using `Spatial`, `Affine`, `ElasticDeformation`, `Resample`, or `Resize`.

## Minimal Pipeline Pattern

```python
import torch
import torchio as tio

subject = tio.Subject(
    t1=tio.ScalarImage(torch.rand(1, 32, 32, 32)),
    seg=tio.LabelMap(torch.randint(0, 3, (1, 32, 32, 32))),
)

pipeline = tio.Compose([
    tio.Resample(target=1.0),
    tio.CropOrPad(target_shape=(32, 32, 32)),
    tio.Normalize(out_min=-1, out_max=1, include=["t1"]),
    tio.Flip(axes=(0, 1, 2), flip_probability=0.5, p=0.5),
    tio.OneOf({
        tio.Noise(std=(0.01, 0.05)): 0.7,
        tio.Blur(std=(0.5, 1.5)): 0.3,
    }),
])

transformed = pipeline(subject)
assert transformed.t1.shape == transformed.seg.shape
assert transformed.seg.data.dtype == subject.seg.data.dtype
assert transformed.applied_transforms
```

## Related Sub-skills

- Use the root TorchIO skill and `data-model` for `Subject`, `Image`, `ScalarImage`, `LabelMap`, `Study`, `Points`, and `BoundingBoxes` construction basics.
- Use `patch-workflows` for `GridSampler`, `UniformSampler`, `WeightedSampler`, `LabelSampler`, `Queue`, `SubjectsLoader`, and `PatchAggregator`.
- Use `cli-and-io` for the `torchio transform` command and file conversion workflows.
