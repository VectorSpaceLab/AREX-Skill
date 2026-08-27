# Keras and quantization

## Choose the environment first

Keras v2 and Keras v3 are separate frontend stacks and should not share one environment.

### Common package choices

- Keras v2 / TensorFlow Keras / QKeras / HGQ:
  - install `hls4ml[qkeras]` when you need the QKeras path
  - keep TensorFlow in the v2 range used by hls4ml
- Keras v3 / QKeras-v3 / HGQ2 / PQuantML / sparsepixels:
  - install `hls4ml[keras-v3]`
  - add `qkeras-v3`, `hgq2`, `pquant-ml`, or `sparsepixels` only when the model actually uses them

### Conflict rules

- Keras v2 and Keras v3 do not coexist cleanly in one Python environment.
- QKeras is tied to Keras v2.
- QKeras-v3 is the Keras v3 counterpart.
- HGQ is supported but deprecated in favor of HGQ2.
- HGQ2, PQuantML, and sparsepixels expect a Keras 3-style environment.

## Keras v2 path

The Keras v2 frontend parses serialized model structure and supports the usual dense, convolutional, pooling, recurrent, merge, reshape, activation, and quantized variants.

Use it when:

- the model comes from `tf.keras`
- the model uses QKeras or HGQ-style quantizers
- you want the most mature path for existing Keras 2 models

Typical flow:

```python
config = hls4ml.utils.config_from_keras_model(model, granularity='name', backend='Vitis')
hls_model = hls4ml.converters.convert_from_keras_model(
    model,
    backend='Vitis',
    hls_config=config,
    output_dir='out',
)
```

## Keras v3 path

Keras v3 uses direct model inspection instead of serialized JSON parsing.

Use it when:

- the model is a Keras 3 model object
- the model uses Keras 3-native layers, QKeras-v3, HGQ2, or PQuantML-style components

Keras v3 conversion supports fallback routing for unsupported layers:

- DA fallback can be enabled with `allow_da_fallback=True`
- Keras v2 fallback can be enabled with `allow_v2_fallback=True`
- if both are enabled, DA fallback is tried first

If a layer is unsupported and both fallbacks are disabled, conversion fails with a clear registry error.

## Quantization families

### QKeras

- Works with Keras v2
- Use `granularity='name'` to get a layer-level config that can be tuned per layer
- Put a quantized activation immediately after the input when you need input precision to be derived cleanly
- Do not mix QKeras with the Keras v3 stack

### HGQ

- Keras v2 based
- Still supported, but deprecated in favor of HGQ2
- The recommended flow is to trace the HGQ model to a proxy model and then convert that proxy model
- Existing precision data in the model should drive the result; avoid forcing a custom precision config unless you know why

### HGQ2

- Keras v3 based
- Supports more layers and quantizers than HGQ
- Model-wise precision propagation is intended to make the generated HLS model bit-exact with the trained model
- This bit-exact pass is typically enabled automatically for HGQ/HGQ2-style models unless you explicitly disable it
- Prefer the model's own quantization data over hand-edited precision settings unless you are intentionally overriding the automatic flow

### Distributed arithmetic

- DA is a Keras v3 fallback path for suitable constant-matrix-vector operations
- It is only available for Vivado/Vitis-style backends
- `ReuseFactor` must stay at 1 for the CMVM kernels that DA replaces
- The accumulator precision is not used the same way as in the normal latency path

### PQuantML

- PQuantML appears in the Keras v3 and PyTorch ecosystems
- The important rule is the same: let the model's own quantization information drive the conversion unless you are deliberately overriding it
- The bit-exact pass is also used automatically for PQuantML-style models unless you explicitly disable it

## Unsupported Keras features

- generic Keras operators such as `Add`, `Subtract`, `Multiply`, and `Divide` are not a substitute for supported layers
- arbitrary `Lambda` layers are not supported
- `channels_first` is only partly supported; hls4ml internally expects `channels_last`
- use channels conversion carefully when the input pipeline already fixes a layout

## Practical advice

- Prefer `granularity='name'` for anything quantized or likely to need per-layer tuning
- Prefer an explicit backend argument so backend-specific defaults are visible in the config
- Keep the model built before calling the config helper or the Keras v3 converter
