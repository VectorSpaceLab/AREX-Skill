# LLM Model and Backend Notes

## Model Families

ExecuTorch examples and docs cover Llama-style flows and several other model families, but support is model- and revision-specific. When a user names a model, verify whether the requested path is native ExecuTorch, Optimum ExecuTorch, or a custom wrapper.

## Quantization

LLM quantization can involve weight-only, low-bit, torchao, backend-specific, or vendor-specific recipes. Do not apply a generic quantization flag without confirming backend support and output accuracy checks.

## Runtime Memory

KV cache, sequence length, batch size, and dynamic-shape bounds dominate memory. Tighten bounds and choose runner/backend based on device memory, not only on export success.

## Deployment

- Android CPU/GPU/NPU flows require Android build outputs and app integration.
- iOS flows require Apple frameworks/Swift package integration and platform-specific backend support.
- QNN LLM paths require QNN SDK, Android NDK, SoC model, and device or supported compile mode.

