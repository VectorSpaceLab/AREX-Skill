# NebullVM API Reference

## Public enums and dataclasses

- `DeepLearningFramework`: `PYTORCH`, `TENSORFLOW`, `NUMPY`
- `DeviceType`: `CPU`, `GPU`, `TPU`, `NEURON`
- `ModelCompiler`: compiler/backend names including `tensor_rt`, `onnxruntime`, `openvino`, `deepsparse`, `tvm`, `torchscript`, `torch_dynamo`, `torch_xla`, `torch_neuron`, `faster_transformer`
- `ModelCompressor`: `sparseml`, `intel_pruning`
- `OptimizationTime`: `constrained`, `unconstrained`
- `HardwareSetup`
- `OriginalModel`
- `OptimizedModel`
- `OptimizeInferenceResult`
- `InputInfo`
- `DynamicAxisInfo`
- `ModelParams`
- `Device`
- `DataManager`
- `PytorchDataset`

## Public functions

- `DataManager.from_dataloader(dataloader, max_length=500)`
- `check_device(device=None)`
- `gpu_is_available()`
- `tpu_is_available()`
- `neuron_is_available()`
- `select_frameworks_to_install(include_frameworks, include_backends)`
- `select_compilers_to_install(include_compilers, framework_list)`

## Why it matters

The high-level Speedster API delegates through these objects and selectors. If a compiler or accelerator is missing, the failure usually begins here rather than in the top-level optimization call.
