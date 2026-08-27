---
name: models
description: "Wrap NumPy, PyTorch, TensorFlow, and JAX models with Foolbox,
  manage bounds and preprocessing, load samples, measure accuracy, compose model
  wrappers, and plot image batches."
disable-model-invocation: true
metadata:
  disco-role: operating
  root-skill: foolbox
  sub-skill: models
license: MIT
---

# Foolbox models

Use this route when the task involves turning a callable or framework model into a
Foolbox model, choosing input bounds or channel layout, applying preprocessing,
changing bounds, checking clean accuracy, loading Foolbox's bundled image samples,
plotting image batches, thresholding inputs, or averaging randomized model calls.
Trigger phrases include **`NumPyModel`**, **`PyTorchModel`**, **`TensorFlowModel`**,
**`JAXModel`**, **`transform_bounds`**, **`accuracy`**, **`samples`**,
**`plot.images`**, **thresholding**, and **expectation over transformation (EOT)**.

This sub-skill covers model wrappers and their utility helpers. It does **not**
select or execute attacks, download a model zoo, or define adversarial criteria.
Route those tasks to the corresponding root-skill route if available.
## Command and output paths

The helper path in this document is relative to the generated Foolbox skill root,
not a native Foolbox checkout and not the caller's current directory. From any
cwd, set the directory containing the root `SKILL.md` and change into it first:

```bash
# Replace this non-executable placeholder with the absolute directory containing the root SKILL.md.
export SKILL_ROOT=/path/to/installed/skills/disco/foolbox
cd "$SKILL_ROOT"
```

Use the actual skill-root path when it differs from this installation. Keep
plots and other generated artifacts in an explicit absolute output directory or
`"$SKILL_ROOT/outputs/"`; create that directory before writing and never write
to the source/reference assets. The `--plot-output` value is a caller-chosen
filesystem path, so make it absolute (or place it under that output directory)
instead of relying on the process cwd.


## Fast route

1. Identify the framework, the model's native input tensor type, channel order,
   and the model's raw input range (before any normalization).
2. Install Foolbox with `python -m pip install foolbox`; install only the needed
   optional framework separately (`torch`, `tensorflow`, or `jax`). Pillow is
   needed by `samples()` and Matplotlib by `plot.images()`; neither is needed to
   construct a basic model wrapper.
3. Construct the matching wrapper with a two-number `bounds=(lower, upper)`.
   For PyTorch and TensorFlow, pass preprocessing in the model's input convention.
4. Call the wrapper on a native tensor or EagerPy tensor and confirm logits have
   shape `(batch, classes)`. Use [`accuracy()` and `samples()`](references/workflows.md#sample-loading-and-clean-accuracy)
   before any downstream work.
5. If callers need another input range, use `fmodel.transform_bounds(new_bounds)`.
   The default is non-mutating; do not confuse this conversion with clipping.
6. Add `ThresholdingWrapper` only when the model should receive a binary input,
   or `ExpectationOverTransformationWrapper` around a stochastic model when a
   multi-call mean is intended. Plot only four-dimensional image batches.

## Framework choice and caveats

- **NumPy:** `NumPyModel` accepts any callable. It returns NumPy output when given
  NumPy input and has no inferable layout unless `data_format` is supplied.
  Explicitly pass `channels_first` or `channels_last` to `samples()` and plotting.
- **PyTorch:** `PyTorchModel` requires a `torch.nn.Module`, moves it to the
  selected device, defaults to CUDA when available otherwise CPU, and reports
  `channels_first`. Put the module in `.eval()` mode when deterministic behavior
  is wanted; construction warns if it is still training.
- **TensorFlow:** `TensorFlowModel` requires TensorFlow eager execution. Its
  device defaults to GPU when TensorFlow reports one, otherwise CPU, and its
  layout comes from `tf.keras.backend.image_data_format()`.
- **JAX:** `JAXModel` accepts a callable and defaults to `channels_last`. JAX is
  optional; `data_format=None` is allowed at construction but reading the
  property then raises `AttributeError`, so specify a supported layout for data
  helpers.

Framework packages are intentionally optional because their builds differ by
platform and accelerator. Never make an unrelated NumPy-only workflow import an
optional framework. See [API details](references/api-reference.md) and
[troubleshooting](references/troubleshooting.md) for failure-specific handling.

## Operating checklist

- Treat `bounds` as the range of the inputs supplied to Foolbox, **before**
  `mean`, `std`, or `flip_axis` preprocessing.
- Use a negative `axis` for vector mean/std broadcasting: `-3` is the channel
  axis for NCHW and `-1` for NHWC. If `axis` is present, each provided mean/std
  must be one-dimensional.
- Keep model outputs as a batch of class scores with classes on the last axis;
  `accuracy()` computes `argmax(axis=-1)` and returns a Python `float`.
- For samples, use a supported bundled dataset name and remember that only the
  20 bundled examples are available; batches above 20 repeat samples and warn.
- For plots, pass `data_format` whenever shape-based inference could be
  ambiguous and pass the same `bounds` used by the model.

## Contract assumptions

Before writing code, record these values explicitly:

- the framework and the callable/model object that owns inference;
- the tensor layout (`NCHW` or `NHWC`) and the class-score output shape;
- the caller-facing bounds and the model-facing post-preprocessing scale;
- whether mean/std are scalar or channel vectors, and which negative axis broadcasts them;
- whether the model is deterministic, stochastic, or intentionally thresholded;
- whether sample assets and plotting dependencies are available in this runtime.

Prefer a small deterministic toy call before loading a pretrained model. Verify
that the wrapper preserves the input backend, that logits have a final class
axis, and that bounds conversion leaves equivalent logits approximately equal.
Only then add framework device placement or a stochastic wrapper. Treat a clean
accuracy value from the 20 bundled assets as a wiring check, not a model-quality
claim.

Do not silently transpose arrays to repair a layout mismatch. Fix the model,
`data_format`, preprocessing axis, and sample request as one contract. Do not
put attacks, attack criteria, pretrained-weight downloads, or model-zoo loading
instructions in this route.

## Linked runtime material

- [Verified constructors, preprocessing, bounds, and return types](references/api-reference.md)
- [Self-contained wrapping and utility workflows](references/workflows.md)
- [Installation and runtime troubleshooting](references/troubleshooting.md)
- [NumPy model smoke helper](scripts/smoke_models.py)

## Minimal validation

Run the helper from any cwd by first changing to the generated skill root (or
replace the script path with the absolute `$SKILL_ROOT` path shown above):

```bash
cd "$SKILL_ROOT"
python sub-skills/models/scripts/smoke_models.py --help
python sub-skills/models/scripts/smoke_models.py
```

The second command uses only the NumPy path and bundled samples. Add `--plot` only
when Matplotlib is installed. For a saved plot, pass an explicit output such as
`--plot-output "$SKILL_ROOT/outputs/model-smoke.png"`; do not use an unqualified
filename. The helper selects a headless backend unless the caller has already
chosen one. It is a smoke check, not an attack benchmark and does not require an
optional deep-learning framework.
