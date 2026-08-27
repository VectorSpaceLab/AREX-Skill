# ONNX and QONNX

## What hls4ml expects

The ONNX frontend expects a cleaned graph with known shapes and supported operator types.

The QONNX path is the safest way to prepare more complex ONNX graphs because it can clean the graph, normalize layouts, and rewrite unsupported constructs before hls4ml sees them.

## Recommended preprocessing

A practical cleanup flow is:

1. load the model through QONNX's `ModelWrapper`
2. run graph cleanup / constant folding
3. convert to channels-last when convolutions are involved
4. rewrite `Gemm` to `MatMul` plus `Add` when needed
5. clean again

Example shape of the flow:

```python
from qonnx.core.modelwrapper import ModelWrapper
from qonnx.util.cleanup import cleanup_model
from qonnx.transformation.channels_last import ConvertToChannelsLastAndClean
from qonnx.transformation.gemm_to_matmul import GemmToMatMul

model = ModelWrapper('model.onnx')
model = cleanup_model(model)
model = model.transform(ConvertToChannelsLastAndClean())
model = model.transform(GemmToMatMul())
model = cleanup_model(model)
```

## Config and conversion

`config_from_onnx_model` defaults to `granularity='name'`. That is also the recommended granularity for QONNX models.

```python
cfg = hls4ml.utils.config_from_onnx_model(model, granularity='name', backend='Vitis')
hls_model = hls4ml.converters.convert_from_onnx_model(
    model,
    backend='Vitis',
    hls_config=cfg,
    io_type='io_stream',
    output_dir='out',
)
```

## Supported operator notes

The active ONNX registry covers common arithmetic, convolution, pooling, reshape, transpose, and quantization operators. It does not mean every legal ONNX graph will pass directly.

Important caveats:

- `Gemm` should usually be rewritten before conversion
- `Quant` support is limited to the operator forms hls4ml understands
- quantization parameters such as `scale`, `zeropt`, and `bitwidth` should be constant
- scalar power-of-two scales with zero zero-point are the easiest case
- models with convolution usually need the channels-last cleanup path

## Safe usage rule

Do not try to convert a raw ONNX graph until the shape, layout, and operator set are stable. If the model came from another toolchain, clean it first and then convert.
