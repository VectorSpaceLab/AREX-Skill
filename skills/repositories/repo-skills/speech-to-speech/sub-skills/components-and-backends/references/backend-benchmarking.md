# Backend benchmarking guidance

STT and TTS benchmarking is useful but not part of the minimum safe skill
verification path. Full measurements can download large models, require CUDA or
MPS, use audio devices or local files, and vary with first-run cache state.

## What to benchmark

For STT:

- model/backend name and exact checkpoint
- input duration and language
- cold-load time versus warm transcription time
- live partial update behavior when using Parakeet TDT
- hardware, dtype, device, and batch/concurrency assumptions

For TTS:

- first-token/first-audio latency
- total synthesis time
- real-time factor (generated audio duration divided by wall time)
- streaming chunk size and non-streaming prefill mode
- Qwen3 backend (`ggml` versus `torch` versus MLX), quantization, and voice mode

## Safe benchmark policy

- Run help/parser checks first; do not start a full benchmark by default.
- Ask before triggering model downloads, long warmups, or external endpoints.
- Separate cold-start and warm-cache results.
- Record CUDA/MPS driver/runtime versions and the exact optional extra set.
- Avoid comparing Apple Silicon MLX and Linux CUDA results as if they were the
  same backend.
- Keep benchmark outputs outside the generated skill directory; they are run
  artifacts, not runtime instructions.

## Qwen3-TTS measurement notes

Qwen3-TTS can change behavior across modes:

- GGML quantization (`BF16`, `Q8_0`, `Q4_K_M`, `F32`) affects memory and speed.
- `--qwen3_tts_non_streaming_mode` pre-fills full target text before decode on
  faster-qwen3-tts; this can improve stability but changes latency shape.
- MLX uses quantized model IDs such as `bf16`, `4bit`, `6bit`, or `8bit` and a
  different streaming chunk default.
- Voice cloning with raw reference audio includes cache-building time on first
  use. Measure cached `.spk`/`.rvq` reuse separately.

## STT measurement notes

- Live transcription is most relevant for Parakeet TDT; measure final transcript
  latency and partial update cadence separately.
- Whisper-family backends may differ in language detection behavior and model
  size. Pin language when comparing pure latency.
- Paraformer defaults are Chinese-oriented; choose test audio that matches the
  selected checkpoint.

## Minimal generated-skill checks

This generated skill bundles `scripts/inspect_backend_registry.py` rather than a
full benchmark runner. Use it to confirm selected backend names, extras, and
default dataclasses before preparing a measurement-specific environment:

```bash
python sub-skills/components-and-backends/scripts/inspect_backend_registry.py
```

Then create a task-specific benchmark script or use the repository's native
benchmark helpers only when operating in a checkout that intentionally includes
those tools and when the user accepts the model/hardware cost.
