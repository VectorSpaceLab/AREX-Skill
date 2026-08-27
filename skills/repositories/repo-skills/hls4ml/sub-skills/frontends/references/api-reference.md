# API reference

## Live snapshot

- hls4ml version: `0.1.0.dev1+gb90fb0673`
- Supported layer registry counts in the inspected environment:
  - Keras: 70
  - PyTorch: 56
  - ONNX: 35
- Available backend names in the inspected environment included: `vivado`, `vivadoaccelerator`, `vitis`, `quartus`, `catapult`, `symbolicexpression`, `oneapi`, and `libero`.

Use `scripts/inspect_supported_layers.py` to print the current registry and optional dependency status in the active environment.

## Frontend helpers

### Config builders

- `hls4ml.utils.config_from_keras_model(model, granularity='model', backend=None, default_precision='fixed<16,6>', default_reuse_factor=1, max_precision=None)`
- `hls4ml.utils.config_from_pytorch_model(model, input_shape, granularity='model', backend=None, default_precision='ap_fixed<16,6>', default_reuse_factor=1, channels_last_conversion='full', transpose_outputs=False, max_precision=None)`
- `hls4ml.utils.config_from_onnx_model(model, granularity='name', backend=None, default_precision='fixed<16,6>', default_reuse_factor=1, max_precision=None)`

Rules of thumb:

- Pass `backend=` when you can. It lets the config builder see backend-specific configurable attributes.
- `config_from_onnx_model` defaults to `granularity='name'` and that is the recommended mode for QONNX.
- Only layer-level precision entries can be `auto`; model-level precision must be explicit.
- `max_precision` is a ceiling for automatic inference and only applies to integer/fixed precision types.

### Converters

- `hls4ml.converters.convert_from_keras_model(model, output_dir='my-hls-test', project_name='myproject', input_data_tb=None, output_data_tb=None, backend='Vivado', hls_config=None, bit_exact=None, allow_da_fallback=True, allow_v2_fallback=True, **kwargs)`
- `hls4ml.converters.convert_from_pytorch_model(model, output_dir='my-hls-test', project_name='myproject', input_data_tb=None, output_data_tb=None, backend='Vivado', hls_config=None, **kwargs)`
- `hls4ml.converters.convert_from_onnx_model(model, output_dir='my-hls-test', project_name='myproject', input_data_tb=None, output_data_tb=None, backend='Vivado', hls_config=None, bit_exact=None, **kwargs)`
- `hls4ml.converters.convert_from_config(config)`

`convert_from_config` accepts a dict or YAML path and dispatches on the model key present in the config. In this snapshot, the modern dispatch keys are `KerasModel`, `PytorchModel`, and `OnnxModel`.

### Saved-model and project helpers

- `hls4ml.converters.load_saved_model(file_path, output_dir=None)`
- `hls4ml.converters.link_existing_project(project_dir)`

### Example and visualization helpers

- `hls4ml.utils.fetch_example_list()`
- `hls4ml.utils.fetch_example_model(model_name, backend='Vivado')`
- `hls4ml.utils.plot_model(model, to_file='model.png', show_shapes=False, show_layer_names=True, show_precision=False, rankdir='TB', dpi=96)`

### SNN marker

- `hls4ml.contrib.snntorch.SNNReadout(n_classes=None, window_size=1, stream_length=None, decision_rule=None, class_threshold=1, output_mode='spike', beta=1.0, reset_policy='fixed_window')`

## Minimal conversion pattern

```python
import numpy as np
import hls4ml

config = hls4ml.utils.config_from_keras_model(model, granularity='name', backend='Vitis')
hls_model = hls4ml.converters.convert_from_keras_model(
    model,
    output_dir='my-hls-test',
    project_name='demo',
    backend='Vitis',
    hls_config=config,
)
hls_model.compile()
y = hls_model.predict(np.asarray(x, dtype='float32'))
```

## Registry inspection

The active registries are backend-dependent and depend on optional packages. Typical categories are:

- Keras frontend layers, including core, convolutional, pooling, recurrent, merge, quantized, HGQ, and utility layers
- PyTorch frontend layers, including linear, convolutional, pooling, functional, quantized, and SNN markers
- ONNX frontend layers, including arithmetic, convolutional, pooling, reshape, transpose, and quantization operators

The exact registry list can change with installed extras. Use `scripts/inspect_supported_layers.py` for the authoritative local list.
