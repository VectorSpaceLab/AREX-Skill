# Speedster API Reference

## Public functions

- `optimize_model(model, input_data, metric_drop_ths=DEFAULT_METRIC_DROP_THS, metric=None, optimization_time="constrained", dynamic_info=None, config_file=None, ignore_compilers=None, ignore_compressors=None, store_latencies=False, device=None, **kwargs)`
- `save_model(model, path)`
- `load_model(path, pipe=None)`

## What `optimize_model` accepts

- `model` may be a torch module, TensorFlow module, or ONNX path.
- `input_data` must be an iterable or sequence of batches.
- Each batch is expected to contain a tuple of model inputs and an optional label tensor.
- `metric_drop_ths` controls acceptable quality loss.
- `metric` may be a callable or a supported metric name such as `numeric_precision` or `accuracy`.
- `optimization_time` is either `constrained` or `unconstrained`.
- `dynamic_info` describes dynamic axes for input and output tensors.
- `ignore_compilers` and `ignore_compressors` filter the optimization search space.
- `store_latencies=True` writes a JSON summary of compiler timings in the working directory.
- `device` accepts `cpu`, `cuda`, `gpu`, `tpu`, `neuron`, and indexed variants such as `cuda:1`.

## Output shape

The optimized model is returned as a framework-compatible inference learner that should preserve the original call style. Use `save_model` and `load_model` to persist and restore the optimized learner.

## Supported compiler and compressor names

- Compilers / backends: `tensor_rt`, `onnx_tensor_rt`, `torch_tensor_rt`, `openvino`, `tvm`, `torch_tvm`, `onnx_tvm`, `onnxruntime`, `deepsparse`, `torchscript`, `xla`, `tflite`, `bladedisc`, `intel_neural_compressor`, `torch_neuron`, `torch_xla`, `torch_dynamo`, `faster_transformer`
- Compressors: `sparseml`, `intel_pruning`

## Cross-reference

If your question is about `DataManager`, `check_device`, or compiler-selection logic, read `../nebullvm-backends/references/api-reference.md` next.
