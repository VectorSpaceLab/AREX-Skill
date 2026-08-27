# LLM Workflows

## Native vs Optimum Export

| Path | Best when | Inputs |
| --- | --- | --- |
| Native ExecuTorch LLM export | The model family is covered by ExecuTorch examples or you need fine control over ExecuTorch-specific optimizations | Local checkpoint/weights, tokenizer, model params, backend/quantization options |
| Optimum ExecuTorch | The model is a Hugging Face architecture supported by the integration and the user wants a higher-level CLI/API | HF model id or local model, task, backend/quantization flags |
| Custom LLM export | Architecture-specific wrappers/KV cache/method decomposition are needed | Custom module wrappers, example inputs, tokenizer/sampler integration |

## Runner Targets

- CPU host/mobile: best first functional path.
- CUDA/Metal/Vulkan: performance-oriented GPU paths; require matching build preset and runtime libraries.
- QNN: route to `qualcomm` for SDK/device compile/run details.
- iOS/Android: requires platform packaging, mobile app integration, and runner/library build artifacts.

## Asset Checklist

- Weight checkpoint identity and format.
- Tokenizer files and vocabulary compatibility.
- Prompt/template convention and BOS/EOS handling.
- KV cache shape/layout assumptions.
- Quantization recipe and calibration/evaluation data if quantized.
- Output artifact names (`.pte`, optional `.ptd`, tokenizer, runner binary/library).

## Validation

Start with tiny prompts and deterministic sampling. Compare tokenization and first-token logits before long-generation benchmarking. For quantized or backend-specific exports, compare against an unquantized CPU baseline with tolerances appropriate to the backend.

