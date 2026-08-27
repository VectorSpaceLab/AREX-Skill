# Export Troubleshooting

| Symptom | Likely cause | Action |
| --- | --- | --- |
| `--include saved_model` is rejected or not exported | TensorFlow export is not implemented here | Use supported include values: `torchscript`, `onnx`, `openvino`, `engine`, `coreml`, `paddle`. |
| TensorRT export fails on CPU | `.engine` requires CUDA | Verify CUDA and run on GPU, or choose TorchScript/ONNX/OpenVINO. |
| ONNX export fails | Missing `onnx` or incompatible opset/dependency | Install export extras, adjust `--opset`, retry without `--simplify`. |
| OpenVINO export fails | OpenVINO package missing or incompatible | Install compatible OpenVINO packages and use CPU-oriented workflow. |
| CoreML export/import warning | `coremltools` or platform support mismatch | Verify target platform; prefer macOS for CoreML runtime validation. |
| Half precision export fails | `--half` needs compatible GPU path | Keep CPU exports in FP32. |
| Exported file not accepted by detection | Runtime dependency/suffix mismatch | Match file suffix to `DetectMultiBackend` support and install the runtime backend. |
