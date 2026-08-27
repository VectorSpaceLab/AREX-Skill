# Foolbox model workflows

These recipes are self-contained and keep the input contract visible. Replace the
toy callables or layers with the real model while preserving bounds, channel
order, and output shape. Framework examples require that framework to be installed
separately; the NumPy recipe is the base smoke path.
Any filesystem path in these recipes is resolved by the Python process. Do not
assume it starts in the native Foolbox checkout. If a recipe uses a skill-relative
helper or output, run it from the generated skill root (or use an absolute path):

```bash
# Replace this non-executable placeholder with the absolute directory containing the root SKILL.md.
export SKILL_ROOT=/path/to/installed/skills/disco/foolbox
cd "$SKILL_ROOT"
mkdir -p "$SKILL_ROOT/outputs"
```

Keep generated plots under that explicit output directory (or another absolute
directory you choose), never in `references/`, `scripts/`, or native source
assets.

## Wrap a NumPy callable

A NumPy callable receives a NumPy array from `NumPyModel`. The example emits three
class scores for an image batch in NHWC layout:

```python
import numpy as np
import foolbox as fb

class Toy:
    def __call__(self, x):
        channel_means = x.mean(axis=(1, 2))
        return np.stack(
            [channel_means[:, 0], channel_means[:, 1], channel_means[:, 2]], axis=-1
        )

fmodel = fb.NumPyModel(Toy(), bounds=(0, 1), data_format="channels_last")
logits = fmodel(np.zeros((2, 32, 32, 3), dtype=np.float32))
assert logits.shape == (2, 3)
```

A NumPy model with `data_format=None` can still be called, but `samples(fmodel)`
cannot infer a layout. Supply `data_format` at construction or pass it explicitly
to every data helper and plotting call.

## Framework-specific wrappers

### PyTorch (NCHW)

```python
import torch
import foolbox as fb

class Net(torch.nn.Module):
    def forward(self, x):
        x = x.mean(dim=(2, 3))
        return torch.cat((x[:, :1], x[:, 1:2], x[:, 2:3]), dim=1)

model = Net().eval()
fmodel = fb.PyTorchModel(
    model,
    bounds=(0, 1),
    device="cpu",
    preprocessing={
        "mean": [0.485, 0.456, 0.406],
        "std": [0.229, 0.224, 0.225],
        "axis": -3,
    },
)
images, labels = fb.samples(fmodel, dataset="cifar10", batchsize=4)
# images and labels are native torch tensors for this adapter.
clean_accuracy = fb.accuracy(fmodel, images, labels)
```

The model must be a `torch.nn.Module`. Move/choose the device through the
constructor rather than manually passing a tensor on a different device. Call
`.eval()` before wrapping if dropout or batch-normalization should be frozen.

### TensorFlow (usually NHWC)

```python
import tensorflow as tf
import foolbox as fb

model = tf.keras.Sequential([
    tf.keras.layers.GlobalAveragePooling2D(),
    tf.keras.layers.Dense(3),
])
# Build the model if the application requires an explicit input shape.
fmodel = fb.TensorFlowModel(model, bounds=(0, 255), device="/CPU:0")
images, labels = fb.samples(fmodel, dataset="cifar10", batchsize=4)
clean_accuracy = fb.accuracy(fmodel, images, labels)
```

TensorFlow must be running in eager mode. TensorFlow's Keras image-data-format
setting determines `fmodel.data_format`; if the application uses a different
layout, make that setting and the sample layout agree before calling the model.
For preprocessing a channel vector in NHWC, use `axis=-1`; for a BGR flip use
`flip_axis=-1`.

### JAX (usually NHWC)

```python
import jax.numpy as jnp
import foolbox as fb

def model(x):
    channel_means = x.mean(axis=(1, 2))
    return channel_means

fmodel = fb.JAXModel(model, bounds=(0, 1), data_format="channels_last")
images, labels = fb.samples(
    fmodel, dataset="cifar10", batchsize=4, data_format="channels_last"
)
clean_accuracy = fb.accuracy(fmodel, images, labels)
```

JAX is optional. The callable must accept a JAX array and return a JAX array (or
an output EagerPy can wrap). Keep `data_format="channels_last"` or explicitly
choose `"channels_first"`; `data_format=None` is not usable with inferred data
helpers.

## Sample loading and clean accuracy

The bundled helper is useful for a small sanity check, not for a representative
dataset evaluation. It has 20 images per supported dataset name and cycles when
`index + batchsize` exceeds that set:

```python
import eagerpy as ep
import foolbox as fb

images, labels = fb.samples(
    fmodel,
    dataset="imagenet",
    index=0,
    batchsize=8,
    shape=(224, 224),
    # omit this when fmodel.data_format is available and correct
    data_format=fmodel.data_format,
    # omit this to use fmodel.bounds
    bounds=fmodel.bounds,
)
# Either native tensors or NumPy arrays depending on the adapter.
images_ep, labels_ep = ep.astensors(images, labels)
print(fb.accuracy(fmodel, images_ep, labels_ep))
```

For a NumPy wrapper without a layout, pass `data_format` explicitly. Do not pass
the opposite layout: `samples()` checks it against adapters that expose a layout
and raises `ValueError` on mismatch. Images are generated in the requested
model bounds, so do not rescale them a second time before the model call.

## Change bounds without changing the wrapped model

```python
# Original model receives [0, 255] and possibly normalizes afterward.
fmodel_255 = fb.PyTorchModel(model, bounds=(0, 255), preprocessing=None, device="cpu")
# New callers can supply [0, 1]; the wrapper maps it back to [0, 255].
fmodel_01 = fmodel_255.transform_bounds((0, 1))
assert fmodel_01.bounds == (0, 1)

# The original object remains at (0, 255) by default.
# For an adapter with preprocessing, mutate deliberately on a separate object:
fmodel_255_inplace = fb.PyTorchModel(
    model, bounds=(0, 255), preprocessing=None, device="cpu"
)
fmodel_255_inplace.transform_bounds((0, 1), inplace=True)
```

The `inplace` form in the last line is available on adapters derived from
`ModelWithPreprocessing` (PyTorch, TensorFlow, and JAX), not the plain
`NumPyModel` signature. To force a wrapper instead of the efficient adjusted
preprocessing path, use the unmodified model adapter:

```python
wrapped = fmodel_255.transform_bounds((0, 1), wrapper=True)
# wrapped.bounds == (0, 1); wrapped.transform_bounds(..., inplace=True) is allowed.
```

Use `wrapper=True` and `inplace=True` together only to discover the explicit
`ValueError`; they are mutually exclusive. Bounds conversion is affine and does
not clamp inputs outside the new interval.

## Compose thresholding and EOT wrappers

### Binary input thresholding

```python
from foolbox.models import ThresholdingWrapper

binary_model = ThresholdingWrapper(fmodel, threshold=0.5)
# Every value < 0.5 becomes lower bound; every other value becomes upper bound.
logits = binary_model(images)
```

The threshold is applied to the input tensor and the result is then passed to the
wrapped model. It does not threshold logits and it does not alter `bounds`.

### Expectation over transformation

The wrapper assumes that `fmodel` is stochastic on each call (the wrapped model
must draw/apply its own random transform):

```python
from foolbox.models import ExpectationOverTransformationWrapper

randomized = fb.PyTorchModel(randomized_torch_module.eval(), bounds=(0, 1))
eot_model = ExpectationOverTransformationWrapper(randomized, n_steps=16)
mean_logits = eot_model(images)
```

`mean_logits` is the arithmetic mean over 16 model outputs. The wrapper does not
accept a transform function, reseed a framework, or modify the input between
calls. Use a positive step count and control random seeds at the framework level
when reproducibility matters. EOT can be composed with bound or threshold
wrappers; make the order explicit because each wrapper transforms the input at
its own call boundary.

## Plot a batch safely

```python
import os
import matplotlib
matplotlib.use("Agg")  # do this before importing pyplot in headless jobs
import matplotlib.pyplot as plt
import foolbox as fb

fb.plot.images(
    images,
    n=4,
    data_format=fmodel.data_format,
    bounds=fmodel.bounds,
    ncols=2,
    scale=3,
)
plt.savefig(os.path.join(os.environ["SKILL_ROOT"], "outputs", "model-samples.png"))
plt.close()
```

`plot.images` requires rank-4 image input and normalizes pixels from the provided
bounds to `[0, 1]`. It returns `None` and does not show or save the figure itself;
use Matplotlib after the call. Explicitly pass `data_format` for a `(N,3,3,3)`
or other shape where both channel positions look plausible. Matplotlib is lazily
imported, so NumPy model wrapping and `accuracy()` do not require plotting.
