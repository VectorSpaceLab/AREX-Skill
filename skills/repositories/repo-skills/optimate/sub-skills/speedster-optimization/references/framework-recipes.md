# Framework Recipes

## Purpose

Read this when you need a short framework-specific reminder instead of the full API reference.

| Framework | Practical note |
| --- | --- |
| PyTorch | Most examples in the docs and tests use Torch models and either CPU or CUDA inputs. |
| TensorFlow | Keep inputs and outputs in framework-native tensor formats. |
| ONNX | ONNX paths typically combine NumPy inputs with ONNX Runtime or compiled backends. |
| Hugging Face | Text/model workflows may involve tokenizer-backed sample conversion. |
| Diffusers | Diffusion recipes can require CUDA-specific versions of torch, TensorRT, and related packages. |

## Common backend terms

- `onnxruntime`
- `openvino`
- `tensor_rt`
- `torch_tensor_rt`
- `tvm`
- `deepsparse`
- `intel_neural_compressor`
- `bladedisc`

## Note

These names appear in the docs and source-level enums. If one of them is missing on your machine, that is a backend-support issue rather than a generic Speedster import failure.
