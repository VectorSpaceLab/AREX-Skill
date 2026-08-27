# Deployment Reference

PaddleOCR has multiple deployment paths. Choose the path that matches the user's runtime, hardware, and packaging constraints.

## Common choices

| Path | Best for | Notes |
| --- | --- | --- |
| PaddlePaddle / PaddleX serving | Service-style inference with Paddle-native backends | Good when the user wants a server or API around a PaddleOCR model. |
| Official API | No local model hosting | Use the hosted API client sub-skill instead of this path when the user has a token and does not want local inference. |
| ONNX Runtime | Portable inference | Useful when the selected model and export path support ONNX. |
| C++ / Lite / mobile | Edge and embedded deployment | Treat the `deploy/` tree as evidence for platform-specific build steps. |
| High-performance inference | GPU or accelerator acceleration | Backend-specific and model-specific; verify hardware before claiming success. |

## What to verify before choosing a path

- The model family supports the target export/deployment format.
- The selected checkpoint exists and matches the config.
- The backend and hardware are available.
- The deployment path does not need a different dependency stack than the training environment.

## Evidence sources

- `deploy/`
- `test_tipc/`
- `docs/version3.x/inference_deployment/`
- `docs/version3.x/pipeline_usage/`

## Recommended approach

1. Inspect the training/export reference to confirm the model family.
2. Use the safe config helper to confirm the selected checkpoint and architecture.
3. Choose a deployment path only after the export and backend requirements are clear.
4. Treat platform-specific shell scripts as reference evidence unless the user explicitly asks for a deployment run.
