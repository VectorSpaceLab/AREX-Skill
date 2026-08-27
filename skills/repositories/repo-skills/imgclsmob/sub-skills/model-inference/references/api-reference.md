# Inference API reference

This reference defines the public provider calls used by the bundled scripts.
The scripts use CPU construction, `pretrained=False`, and do not call a
training/evaluation helper or a model-store downloader.

## Public model providers

### Gluon / gluoncv2

The exact public provider signature is:

```python
gluon.gluoncv2.model_provider.get_model(name, **kwargs)
```

The installed distribution commonly exposes the same function as:

```python
from gluoncv2.model_provider import get_model
```

The provider lowercases `name`, looks it up in its model registry, and raises
`ValueError("Unsupported model: ...")` when there is no match. A CPU
classification construction is:

```python
import mxnet as mx
from gluon.gluoncv2.model_provider import get_model

ctx = mx.cpu()
net = get_model("resnet18", pretrained=False, ctx=ctx, classes=1000)
net.initialize(mx.init.MSRAPrelu(), ctx=ctx)
logits = net(mx.nd.zeros((1, 3, 224, 224), ctx=ctx))
```

`pretrained=False` is important: `pretrained=True` can invoke the provider's
weight retrieval/model-store behavior. `ctx=mx.cpu()` keeps parameters and
inputs on CPU. `classes` and `in_channels` are model-constructor keyword
arguments where supported; they must match the local parameter file. The
bundled Gluon script fixes `classes` from `--classes` and uses three input
channels.

The local repository utility's exact preparation signature is:

```python
gluon.utils.prepare_model(
    model_name,
    use_pretrained,
    pretrained_model_file_path,
    dtype,
    net_extra_kwargs=None,
    load_ignore_extra=False,
    tune_layers=None,
    classes=None,
    in_channels=None,
    do_hybridize=True,
    initializer=mx.init.MSRAPrelu(),
    ctx=mx.cpu(),
)
```

The bundled script intentionally does not import this training-oriented
utility: it constructs the public provider directly, initializes it, and then
loads a local file with `net.load_parameters(filename, ctx=ctx,
ignore_extra=False)`.

### PyTorch / pytorchcv

The exact public provider signature is:

```python
pytorchcv.model_provider.get_model(name, **kwargs)
```

A CPU classification construction is:

```python
import torch
from pytorchcv.model_provider import get_model

net = get_model("resnet18", pretrained=False, num_classes=1000)
net.to(torch.device("cpu"))
net.eval()
with torch.no_grad():
    logits = net(torch.zeros((1, 3, 224, 224), dtype=torch.float32))
```

For this provider, the classifier keyword is `num_classes`; do not substitute
Gluon's `classes` keyword. The provider's `pretrained` option must remain
`False` for an offline run. The bundled script always passes
`pretrained=False`, moves the model to `torch.device("cpu")`, and never calls
`.cuda()`.

The local repository utility's exact preparation signature is:

```python
pytorch.utils.prepare_model(
    model_name,
    use_pretrained,
    pretrained_model_file_path,
    use_cuda,
    use_data_parallel=True,
    net_extra_kwargs=None,
    load_ignore_extra=False,
    num_classes=None,
    in_channels=None,
    remap_to_cpu=False,
    remove_module=False,
)
```

The bundled script does not import this utility. For a local checkpoint it
uses `torch.load(filename, map_location=torch.device("cpu"))`, unwraps a
mapping's `state_dict` key when present, optionally removes a leading
`module.`, and calls `net.load_state_dict(state, strict=True)`.

## Shape and statistics contracts

The expected classification input is one NCHW tensor with shape
`(1, 3, input_size, input_size)`. The scripts require a rank-2 output with
batch dimension one and assert the configured class count. They apply softmax
along the class dimension and print zero-based class indices and probabilities.

The exact repository statistics helper signatures are:

```python
gluon.model_stats.measure_model(model, in_shapes, ctx=mx.cpu())
pytorch.model_stats.measure_model(model, in_shapes)
```

These helpers perform instrumented zero-input passes and are not used by the
smoke scripts. A parameter count is printed instead; it is not a FLOPs,
latency, or accuracy measurement.
