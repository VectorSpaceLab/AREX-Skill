# Export and optimization troubleshooting

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Export stops before writing the model | The config / checkpoint pair is incompatible | Re-check the model family and the export type. |
| Missing JIT / Blade sidecar files | The export path was interrupted or the files were moved | Keep the exported model and sidecars in the same directory. |
| Blade import fails | Blade runtime or `blade_compression` is missing | Install the documented Blade stack or stay on raw / JIT export. |
| `pai_nni` import fails during prune | The pruning dependency is missing | Install `pai_nni` before invoking the pruning command. |
| ONNX load fails later | `onnxruntime` was not installed or the ONNX file is stale | Install the runtime and regenerate the export artifact if needed. |
| TorchAccelerator tutorial fails | The host runtime does not match the documented container | Use the documented CUDA 11.3 container or another supported TorchAcc runtime. |
| `use_trt_efficientnms` errors out | The Blade / TensorRT helper is unavailable | Disable the feature or install the full optimization stack. |

## Recovery checklist

1. Confirm the base model trains and evaluates before optimizing it.
2. Confirm the artifact format you want before exporting.
3. Confirm the backend extras are installed for prune / quantize / Blade / TorchAcc.
4. Re-run the smallest safe export or analysis helper first.

