# Cross-Cutting pomegranate Feature Guide

This page covers package-wide behavior that affects multiple pomegranate model families. Use the model-specific sub-skills for concrete constructors and workflows.

## PyTorch backend and devices

Pomegranate v1.x models are PyTorch modules or use PyTorch tensors internally. Practical consequences:

- Use `torch.Tensor`, NumPy arrays, or Python lists as inputs; pomegranate casts many inputs to tensors during validation.
- Move the model and data to the same device before CUDA execution, for example `model = model.cuda()` and `X = X.cuda()`.
- If using CPU only, no special pomegranate backend flag is needed.
- GPU support is optional for the core workflows. A CPU run validates the model logic, while CUDA validation also requires a CUDA-capable PyTorch install and visible NVIDIA device.

## Missing values

Use `torch.masked.MaskedTensor` for missing values. The mask convention is important:

- `mask=True` means the value is observed.
- `mask=False` means the value is missing and should be ignored or inferred.
- Do not encode missingness only as `NaN`; convert to a mask first.

Common pattern:

```python
import torch
from pomegranate.distributions import Normal

X = torch.tensor([[1.0, float('nan')], [2.0, 4.0], [3.0, 5.0]])
mask = ~torch.isnan(X)
X_masked = torch.masked.MaskedTensor(torch.nan_to_num(X), mask=mask)
model = Normal(covariance_type="diag").fit(X_masked)
```

Documented limitations: missing-value support is not universal. Avoid claiming missing-value support for Bernoulli, categorical distributions, full-covariance `Normal`, or `Uniform` unless a local check proves the exact path works.

## Priors and semi-supervised behavior

`GeneralMixtureModel`, `BayesClassifier`, and HMMs expose prior-probability paths that bias or hard-label component/state assignments.

- Priors are probabilities, not arbitrary weights; rows should be nonnegative and sum to 1.
- A row with a `1.0` in one component is treated as a hard label for that example or timestep.
- Soft priors affect initial component/state estimates but are not equivalent to supervised targets.
- For HMMs, sequence priors follow the same shape as sequence data with the last dimension equal to the number of states.

Read [../sub-skills/mixtures-and-classifiers/SKILL.md](../sub-skills/mixtures-and-classifiers/SKILL.md) and [../sub-skills/sequence-models/SKILL.md](../sub-skills/sequence-models/SKILL.md) for model-specific prior handling.

## Out-of-core and mini-batch updates

Most trainable models support a two-step update pattern:

```python
for X_chunk in chunks:
    model.summarize(X_chunk)
model.from_summaries()
```

Use this when a dataset is too large to hold in memory. The accumulated sufficient statistics are additive, so the final update is intended to match fitting all chunks together for supported models. Reset behavior is model-owned; do not manually modify private cache tensors.

## Sample weights, inertia, and frozen parameters

- `sample_weight` usually accepts one weight per example or per feature/time element, depending on the model.
- `inertia` in `[0, 1]` interpolates between old and new parameters during `from_summaries()`.
- `frozen=True` prevents parameter updates for a model or component.
- To freeze individual tensors or values, operate on the component's PyTorch parameter state only after confirming the exact object layout.

## Mixed precision and dtypes

Pomegranate can run inside PyTorch autocast or on lower-precision tensors, but operations such as covariance linear algebra, categorical indexing, and graph/HMM inference may be less robust than ordinary neural-network layers. Prefer full precision while debugging, then introduce mixed precision behind assertions.

```python
with torch.autocast("cuda", dtype=torch.bfloat16):
    model.fit(X)
```

## Serialization

Because models are PyTorch modules, use PyTorch serialization for complete objects when the runtime environment and pomegranate version are controlled:

```python
import torch

torch.save(model, "model.torch")
# Only for trusted files: recent PyTorch versions may default to weights_only=True.
model = torch.load("model.torch", weights_only=False)
```

If a newer PyTorch raises a `Weights only load failed` / unsupported-global error for a saved pomegranate object, either reload the trusted file with `weights_only=False` or use `torch.serialization.safe_globals(...)` / `add_safe_globals(...)` for the specific pomegranate classes you trust. Do not set `weights_only=False` for untrusted files because full-object unpickling can execute arbitrary code.

For long-term or cross-version interchange, keep constructor parameters, training code, and package version alongside the serialized file because v1.x APIs are not compatible with pre-v1 Cython-era pomegranate objects.

## `torch.compile`

When compiling individual methods, set `check_data=False` on the model only after validating shapes, dtypes, and ranges manually. Compiling nested composite methods can fail with opaque PyTorch errors; start with leaf methods such as a distribution's `log_probability` before compiling mixture or HMM `predict` paths.

```python
model = Normal([0.0], [1.0], covariance_type="diag", check_data=False)
model.log_probability = torch.compile(model.log_probability, mode="reduce-overhead", fullgraph=True)
```
