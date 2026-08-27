# Root deployment summary

For detailed deployment operations, read `../sub-skills/deployment/`.

Use deployment when the user asks for high-performance inference, serving, high-stability serving, Paddle2ONNX, GenAI client/server, plugin installation, GPU/TensorRT/OpenVINO/HPI backend selection, or hardware-specific packaging.

Common commands:

```bash
paddlex --install serving
paddlex --install paddle2onnx
paddlex --install hpi-cpu
paddlex --install hpi-gpu
paddlex --install genai-client
paddlex --serve --pipeline image_classification --host 0.0.0.0 --port 8080
paddlex --paddle2onnx --paddle_model_dir ./inference_model --onnx_model_dir ./onnx --opset_version 7
paddlex_genai_server --help
```

HPI/GPU/server paths are not proven by CPU import alone. Verify the matching PaddlePaddle wheel, PaddleX plugin, backend library, and hardware before claiming readiness.
