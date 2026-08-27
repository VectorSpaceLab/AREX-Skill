# Optimization and compression

## Compression front doors

- `python -m easycv.tools.prune CONFIG CKPT --work_dir WORK_DIR ...`
- `python -m easycv.tools.quantize CONFIG CKPT --work_dir WORK_DIR --device cpu --backend PyTorch`

## Advanced dependency notes

| Workflow | Extra dependency | Notes |
| --- | --- | --- |
| Pruning | `pai_nni` | Required by the pruning path and the model speedup helper. |
| Quantization | `blade_compression` | Required by the quantization path. |
| Blade export | `blade_compression` and Blade runtime support | Required for Blade-optimized export. |
| TorchAccelerator | TorchAcc runtime and documented CUDA image | Follow the tutorial's container guidance. |
| ONNX inference | `onnxruntime` | Needed when the exported model is consumed as ONNX. |

## Read-only analysis helpers

These helpers are safe to use for model inspection and comparison:

- `python -m easycv.tools.analyze_tools.count_parameters`
- `python -m easycv.tools.analyze_tools.count_flops`
- `python -m easycv.tools.analyze_tools.measure_inference_time`

## Workflow notes

- Pruning in this repo is model and backend dependent and usually starts from a YOLOX-style recipe.
- Quantization can target CPU or other supported backends, but the config must match the backend and model type.
- TorchAccelerator uses dedicated configs and usually a dedicated runtime container.

## Common success signals

- The optimized checkpoint is written to the declared work directory.
- The model reloads with the matching predictor or inference path.
- The optional extra used by the path is present before the command starts.

