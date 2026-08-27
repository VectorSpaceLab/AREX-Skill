# Foolbox model troubleshooting

## Installation and imports

Install the core package in the interpreter that will run the workflow:

```bash
python -m pip install foolbox
python -c "import foolbox; print(foolbox.__version__)"
```

PyTorch, TensorFlow, and JAX are optional and must be installed separately with
the build appropriate for the machine. A missing optional framework should only
block that framework's constructor; it should not block `NumPyModel`, `accuracy`,
or other core routes. Check an optional dependency without making it a required
import:

```bash
python -c "import importlib.util; print(importlib.util.find_spec('torch'))"
python -c "import importlib.util; print(importlib.util.find_spec('tensorflow'))"
python -c "import importlib.util; print(importlib.util.find_spec('jax'))"
```

If `import foolbox` fails, check that the active Python is the one where Foolbox
was installed (`python -m pip show foolbox`) and that a local file named
`foolbox.py`, `numpy.py`, `torch.py`, `tensorflow.py`, or `jax.py` is not
shadowing the package. Do not make a NumPy-only script import all three optional
frameworks.

## Missing Pillow or Matplotlib

`samples()` imports Pillow when it reads its bundled image files. A model can be
constructed without Pillow, but sample loading fails if Pillow is unavailable:

```bash
python -m pip install pillow
```

`plot.images()` imports Matplotlib lazily. Install it only for plotting:

```bash
python -m pip install matplotlib
```

For a server or CI runner, select a headless backend before the first pyplot
import, for example `MPLBACKEND=Agg python your_plot_script.py`, or call
`matplotlib.use("Agg")` before importing `matplotlib.pyplot`. `plot.images()`
does not save or display a figure; save it through Matplotlib after the call.

## Optional framework construction failures

- **PyTorch:** `PyTorchModel` raises `ValueError` unless the object is a
  `torch.nn.Module`. Put it in `.eval()` mode if the training-mode warning is
  not intended. A CUDA default can fail when a partially configured CUDA build
  is present; pass `device="cpu"` to isolate that issue.
- **TensorFlow:** `TensorFlowModel` raises `ValueError` outside eager execution.
  Enable TensorFlow eager mode or run the wrapper in the normal eager Keras
  process. Pass an explicit device string such as `"/CPU:0"` when device
  selection is the suspected problem.
- **JAX:** the callable is not type-checked by the adapter. Verify it accepts the
  JAX array shape and returns a JAX-compatible score array. With
  `data_format=None`, accessing `fmodel.data_format` raises `AttributeError` by
  design; supply a layout to the constructor or to `samples()`/plotting.

## `data_format` errors

Only `"channels_first"` and `"channels_last"` are valid explicit layouts for
`NumPyModel` and `plot.images`. A NumPy wrapper with `data_format=None` has no
inferred layout. `samples()` then raises:

```text
data_format could not be inferred, please specify it explicitly
```

When an adapter exposes a layout, an explicit `samples(..., data_format=...)`
value must match it. A mismatch raises a `ValueError`; use the model's
`fmodel.data_format` rather than guessing. Keep the tensor layout, preprocessing
axis, and model architecture consistent: NCHW typically uses `axis=-3`, while
NHWC typically uses `axis=-1`.

JAX stores the provided layout without constructor validation. For predictable
helper behavior, use one of the two supported strings even though a typo may not
fail until sampling or plotting.

## Preprocessing axis and shape errors

The preprocessing dictionary accepts only `mean`, `std`, `axis`, and `flip_axis`.
An unknown key raises `ValueError`. If `axis` is supplied it must be negative and
every non-`None` mean/std value must be 1-D; otherwise construction raises
`ValueError`. These are common mistakes:

```python
# Wrong: positive axis.
preprocessing = {"mean": [0.5, 0.5, 0.5], "axis": 1}

# Wrong: scalar combined with an axis; use a scalar without axis or a 1-D vector.
preprocessing = {"mean": 0.5, "std": [0.2, 0.2, 0.2], "axis": -3}

# Right for NCHW; right for NHWC would use axis=-1.
preprocessing = {"mean": [0.5, 0.5, 0.5], "std": [0.2, 0.2, 0.2], "axis": -3}
```

Preprocessing is applied after any bound conversion and in the order flip,
subtract mean, divide std. It does not clip or change the declared bounds. A
model trained for `[0,255]` must not be wrapped with `(0,1)` unless its
preprocessing/model contract actually expects that scale, or the equivalent
`transform_bounds` conversion is used.

## Input bounds and bound transformation

`bounds` are a declaration of the input interval, not an automatic runtime
check. Keep supplied inputs in that interval and ensure `lower < upper`. To
accept a new scale while preserving the old model behavior, call:

```python
converted = fmodel.transform_bounds((0, 1))
```

The default returns a new model and leaves `fmodel` unchanged. The conversion is
affine and does not clip out-of-range values. On framework adapters,
`inplace=True` adjusts the preprocessing and bounds on that adapter. On a plain
`NumPyModel`, use the returned `TransformBoundsWrapper`; its base signature does
not accept adapter-only `inplace` or `wrapper` keywords.

If the converted model produces unexpectedly different logits, check all three
scales: the values passed by the caller, the old/new `bounds`, and the wrapped
model's expected post-preprocessing range. Also ensure mean/std are expressed in
the old model's input convention before transformation.

## Model output shape and labels

`accuracy()` computes `fmodel(inputs).argmax(axis=-1)`. A frequent error is a
model that returns `(batch, classes, height, width)` or a single unbatched vector
when the caller expects `(batch, classes)`. Add the model's pooling/flattening
step or call it with a batch dimension. Confirm:

```python
logits = fmodel(images)
print(logits.shape, labels.shape)
assert logits.ndim == 2 and len(logits) == len(labels)
```

Labels must align one-per-input and use class indices compatible with the output
width. `accuracy()` does not apply softmax and does not translate one-hot labels.

## Samples and plotting shape failures

Supported sample names are `imagenet`, `cifar10`, `cifar100`, `mnist`, and
`fashionMNIST`. An unknown name results in a file lookup failure rather than a
specialized validation message. `batchsize > 20` repeats the bundled set and
emits a warning; it does not load a larger dataset.

`plot.images()` requires four dimensions. It raises `ValueError` for rank-3 input,
invalid explicit layouts, or ambiguous automatic layout detection. Use
`data_format="channels_first"` for `(N,C,H,W)` and `"channels_last"` for
`(N,H,W,C)`. If the plot is blank or colors are wrong, pass the model's bounds
explicitly; the helper maps those bounds to `[0,1]` for Matplotlib.

## Wrapper composition failures

- `ThresholdingWrapper` compares raw input values with its scalar threshold and
  then sends lower/upper-bound values to the model. Choose the threshold in the
  model's declared input scale, not in normalized post-preprocessing units.
- `ExpectationOverTransformationWrapper` averages `n_steps` outputs but does
  not create transformations. Wrap a model that is actually stochastic or
  performs a random transform on every call. A zero step count is unsupported;
  use a positive integer.
- `transform_bounds(..., inplace=True, wrapper=True)` is invalid on adapters and
  raises `ValueError`; choose mutation or an explicit wrapper.
- Both wrappers preserve the wrapped model's bounds. If a composite model needs
  another input range, transform the appropriate layer and verify the order with
  a small deterministic input before using it in a larger workflow.
