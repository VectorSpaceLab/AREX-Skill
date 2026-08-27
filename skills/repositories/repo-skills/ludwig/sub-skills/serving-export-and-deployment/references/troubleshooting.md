# Serving and Export Troubleshooting

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `fastapi` or `uvicorn` missing | Serve extra not installed | Install the serve dependencies for local serving. |
| Server returns 504 | Prediction exceeded `prediction_timeout` | Increase timeout, reduce payload/batch size, or debug with batch `predict`. |
| Payload validation fails | Feature names/types do not match training config | Build payload from config and include required input fields. |
| Ray Serve import error | Ray Serve dependencies missing | Install distributed/Ray Serve dependencies and verify Ray separately. |
| KServe import error | KServe package/runtime missing | Install KServe package and run in an approved service environment. |
| vLLM fails | Incompatible model/runtime/GPU/quantization | Verify LLM artifact, GPU memory, vLLM install, max length, and tensor parallel settings. |
| ONNX export fails | ONNX deps or model ops unsupported | Use `safetensors` or `torch_export`, or install ONNX dependencies and inspect unsupported ops. |
| Hub upload unauthorized | Missing token/repo permissions | Confirm credentials, repo id, privacy setting, and remote side effects with the user. |
