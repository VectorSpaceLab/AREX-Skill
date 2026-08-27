# Qualcomm SDK deployment troubleshooting

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Converter rejects quantization overrides | The `.encodings` file does not match the exported `.onnx` graph | Re-export model and encodings together and run `inspect_export.py` before conversion. |
| QNN compile fails on an op | Target backend does not support the ONNX op pattern or precision | Inspect the converter/compile log, simplify the ONNX graph, or keep unsupported ops in float fallback if acceptable. |
| `qairt-*` or `qnn-*` command not found | Qualcomm AI Runtime / QNN SDK is not installed or environment variables are not sourced | Locate the SDK install and source its setup script before running generated commands. |
| AI Hub job submission fails | `qai_hub` package missing, user not authenticated, or unsupported device name | Run `python -c 'import qai_hub'`, verify credentials with AI Hub tooling, and list supported devices before submission. |
| Inference accuracy cannot be computed | Output data empty, labels mismatch, or input batch layout differs from compiled model | Use actual input names, batch dimension 1 per sample, and channel-last conversion only when compile options require it. |
