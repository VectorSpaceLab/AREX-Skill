# Foolbox model and utility API

The signatures and behavior below are derived from the public model, wrapper,
utility, and plotting implementations. Use the public imports rather than
reaching into package internals.

## Public imports

```python
import foolbox as fb
from foolbox import accuracy, samples
from foolbox.models import (
    JAXModel,
    NumPyModel,
    PyTorchModel,
    TensorFlowModel,
    TransformBoundsWrapper,
    ThresholdingWrapper,
    ExpectationOverTransformationWrapper,
)
from foolbox import plot
```

`Model`, the four framework adapters, `accuracy`, and `samples` are also
available from `foolbox`. The three wrappers above are exported from
`foolbox.models`.

## Model constructors and calls

```python
NumPyModel(
    model: Callable,
    bounds: BoundsInput,
    data_format: Optional[str] = None,
)

PyTorchModel(
    model: Any,
    bounds: BoundsInput,
    device: Any = None,
    preprocessing: Preprocessing = None,
)

TensorFlowModel(
    model: Any,
    bounds: BoundsInput,
    device: Any = None,
    preprocessing: Preprocessing = None,
)

JAXModel(
    model: Any,
    bounds: BoundsInput,
    preprocessing: Preprocessing = None,
    data_format: Optional[str] = "channels_last",
)
```

- `bounds` is a two-item tuple or `foolbox.types.Bounds`, such as `(0, 1)` or
  `(0, 255)`. It is the range of inputs supplied to Foolbox, before preprocessing.
  The named tuple does not validate ordering; use `lower < upper`.
- Each adapter accepts a supported native array/tensor or an EagerPy tensor and
  restores the input's native output type. The callable should return batched
  class scores with classes on the last axis, normally `(N, classes)`.
- `NumPyModel` accepts any callable. If a non-`None` `data_format` is supplied,
  it must be `"channels_first"` or `"channels_last"`, otherwise construction
  raises `ValueError`. With `None`, the model has no `data_format` attribute:
  reading it raises `AttributeError`.
- `PyTorchModel` requires a `torch.nn.Module`. It moves it to `device`; a string
  becomes `torch.device`, and `None` chooses `cuda:0` when CUDA is available or
  CPU otherwise. Its layout is `"channels_first"`. Construction warns when the
  module is in training mode, so call `model.eval()` for deterministic inference.
- `TensorFlowModel` requires TensorFlow eager execution and accepts a TensorFlow
  device string/object. Its layout comes from
  `tf.keras.backend.image_data_format()`.
- `JAXModel` accepts a callable and creates a JAX dummy tensor for native output
  restoration. Its default layout is `"channels_last"`. The constructor does
  not validate a custom layout; use one of the two supported strings. With
  `data_format=None`, reading the property raises `AttributeError`.

## Preprocessing semantics

`preprocessing` is `None` or a dictionary containing only these keys:

```python
preprocessing = {
    "mean": ...,      # optional scalar, 1-D sequence, or tensor
    "std": ...,       # optional scalar, 1-D sequence, or tensor
    "axis": -3,       # optional; must be negative
    "flip_axis": -1,  # optional axis passed to EagerPy flip
}
```

For each call the adapter:

1. flips inputs along `flip_axis`, if present;
2. subtracts `mean`, if present; and
3. divides by `std`, if present;
4. invokes the framework model.

`axis` reshapes non-`None` one-dimensional mean/std vectors for broadcasting.
It must be negative (`-1` means the last axis); a positive axis or a scalar/non-
1-D vector with `axis` raises `ValueError`. NCHW channel statistics usually use
`axis=-3`; NHWC channel statistics use `axis=-1`. Unknown keys also raise
`ValueError`. Values are converted to the backend represented by the adapter's
dummy tensor when needed. No preprocessing step clips values.

For example, a PyTorch model receiving RGB images in `[0,1]` but expecting
ImageNet normalization can be wrapped as:

```python
fmodel = fb.PyTorchModel(
    model.eval(),
    bounds=(0, 1),
    preprocessing={
        "mean": [0.485, 0.456, 0.406],
        "std": [0.229, 0.224, 0.225],
        "axis": -3,
    },
)
```

## Bounds and model wrappers

```python
fmodel.transform_bounds(bounds: BoundsInput) -> Model
TransformBoundsWrapper(model: Model, bounds: BoundsInput)
ThresholdingWrapper(model: Model, threshold: float)
ExpectationOverTransformationWrapper(model: Model, n_steps: int = 16)
```

The default `transform_bounds` result is non-mutating. If old bounds are `(a,b)`
and new bounds are `(c,d)`, a new input `x` is mapped to the wrapped model as
`((x-c)/(d-c))*(b-a)+a`. This is an affine range conversion, not clipping. The
base implementation returns `TransformBoundsWrapper`; adapters with
preprocessing use a more efficient copy/update path and adjust mean/std to
preserve the wrapped model's behavior.

The preprocessing adapters support `inplace=False` and `wrapper=False` in their
`transform_bounds` implementation. `inplace=True` mutates that adapter;
`wrapper=True` forces an explicit `TransformBoundsWrapper`; the two flags cannot
both be true and raise `ValueError`. Plain `NumPyModel` inherits the base
one-argument signature. A bounds wrapper delegates `data_format` to its wrapped
model, so a layout remains visible when the original model has one.

`ThresholdingWrapper` preserves bounds and replaces every input value with the
lower bound when it is below `threshold`, otherwise the upper bound, then calls
the wrapped model. It thresholds inputs, not logits.

`ExpectationOverTransformationWrapper` calls its wrapped model `n_steps` times
on the same input, stacks the score outputs on a leading axis, and returns their
mean. The wrapped model must itself randomize or transform on each call if
multiple draws are desired. The implementation does not provide a transform
callback or a friendly zero-step check; use a positive integer.

## Utility signatures and return types

```python
accuracy(fmodel: Model, inputs: Any, labels: Any) -> float

samples(
    fmodel: Model,
    dataset: str = "imagenet",
    index: int = 0,
    batchsize: int = 1,
    shape: Tuple[int, int] = (224, 224),
    data_format: Optional[str] = None,
    bounds: Optional[Bounds] = None,
) -> Any  # runtime value is (images, labels)
```

`accuracy` converts inputs and labels to EagerPy, computes
`fmodel(inputs).argmax(axis=-1)`, compares to labels, averages, and returns a
Python float. It neither applies softmax nor validates one-hot labels.

`samples` returns `(images, labels)`. Supported bundled names are `imagenet`,
`cifar10`, `cifar100`, `mnist`, and `fashionMNIST`. There are 20 files per name;
`index` wraps modulo 20, and `batchsize > 20` repeats files with a warning.
ImageNet files are resized to `shape`; other datasets are not resized by this
helper. Images load as float32, grayscale images gain a singleton channel, and
`channels_first` transposes from `(N,H,W,C)` to `(N,C,H,W)`. When `bounds !=
(0,255)`, pixels are linearly mapped from `[0,255]` to the requested bounds.

When `fmodel` has `data_format`, `samples` infers it unless an explicit value is
provided; a mismatch raises `ValueError`. Models without that attribute require
an explicit layout. Framework adapters have a dummy tensor and return native
images/labels. `NumPyModel` has no dummy and warns, returning NumPy arrays.

## Plot signature and data-format rules

```python
plot.images(
    images: Any,
    *,
    n: Optional[int] = None,
    data_format: Optional[str] = None,
    bounds: Tuple[float, float] = (0, 1),
    ncols: Optional[int] = None,
    nrows: Optional[int] = None,
    figsize: Optional[Tuple[float, float]] = None,
    scale: float = 1,
    **kwargs: Any,
) -> None
```

The input must be rank 4: `(N,C,H,W)` or `(N,H,W,C)`. With no explicit layout,
inference succeeds only if exactly one candidate channel position has size 1 or
3; otherwise it raises an ambiguity `ValueError`. Explicit values must be
`channels_first` or `channels_last`, or a `ValueError` is raised. The helper
normalizes using `bounds`, creates a Matplotlib grid, hides axes, and returns
`None`; it does not call `show()` or save the figure. `n`, `ncols`, `nrows`,
`figsize`, `scale`, and extra keyword arguments control that grid.
