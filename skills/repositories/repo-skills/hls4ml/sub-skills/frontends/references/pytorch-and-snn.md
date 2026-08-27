# PyTorch and SNN

## PyTorch frontend basics

The PyTorch frontend is FX-trace based. Only models that can be symbolically traced are good candidates.

Supported building blocks include common `torch.nn` modules, many `torch.nn.functional` operations, and selected traced leaf modules from the quantized and SNN ecosystems.

Typical config helper:

```python
config = hls4ml.utils.config_from_pytorch_model(
    model,
    input_shape=(channels, length),
    granularity='name',
    backend='Vitis',
)
```

## Channel layout and I/O

PyTorch uses channels-first tensors, while hls4ml uses channels-last internally.

`config_from_pytorch_model` exposes three layout modes through `channels_last_conversion`:

- `full`: convert both the inputs and the internal layers
- `internal`: convert only the internal layers and expect the caller to transpose inputs manually
- `off`: disable the conversion

`transpose_outputs` adds an output transpose back to channels-first, but only for the parallel I/O path.

### Safe rule for stream I/O

If you choose `io_stream`, do not rely on automatic input transposition. Use `channels_last_conversion='internal'` and transpose the input yourself before calling `predict()`.

## Brevitas and PQuantML

- Brevitas models are not ingested directly by the hls4ml PyTorch parser
- Export Brevitas models to ONNX/QONNX instead
- Non-power-of-two or non-scalar quantization scales may need extra cleanup work
- PQuantML uses the PyTorch parser path, and the current model quantization data should be preserved rather than overridden by hand
- keep `ChannelsLastConversion='full'` active when using the PyTorch path so model-wise precision propagation can work correctly

## SNN support

Install the SNN path with the SNN extra and use the marker module from `hls4ml.contrib.snntorch`.

### Marker module

```python
from hls4ml.contrib.snntorch import SNNReadout
```

The marker acts like an identity in PyTorch and becomes the hls4ml `SNNReadout` layer after conversion.

### Readout signature

`SNNReadout(n_classes=None, window_size=1, stream_length=None, decision_rule=None, class_threshold=1, output_mode='spike', beta=1.0, reset_policy='fixed_window')`

### Important semantics

- backend support is Vitis-only for the current SNN flow
- the frontend is synchronous and clock-driven
- `Leaky` modules become `LIFNeuron` or `IFNeuron` depending on `beta`
- `subtract` and `zero` resets are supported
- `threshold` and `beta` may be scalar or per-neuron vectors
- trainable PyTorch parameters are captured with their values at conversion time
- `window_size` and `stream_length` are aliases for the same sequence boundary concept
- only the fixed-window reset behavior is currently active in generated kernels

### Decision rules

Supported readout decision rules include:

- `argmax_spike_count`
- `first_to_threshold`
- `threshold_then_argmax`
- `binary_logit`
- `argmax_membrane`

`output_mode='membrane'` works with `argmax_membrane` or `binary_logit`.

### Predict usage

The compiled SNN model is stateful across top-level calls. Feed one timestep at a time and treat exactly one window as one sequence.

## Suggested smoke pattern

- build a tiny `Linear` or `Conv` model
- create the config with `granularity='name'`
- convert with a temp output directory
- compile
- run `predict()` on a tiny fixed input
- compare to the native PyTorch output
