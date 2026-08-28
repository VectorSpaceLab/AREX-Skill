# Inference troubleshooting

| Symptom | Likely cause | Recovery |
|---|---|---|
| `ValueError` for prompt source | Missing prompt or both prompt and prompt file supplied | Provide exactly one of `request.prompt` or `request.inputs.prompt_path`; ensure the file has non-empty lines. |
| Invalid dimension/empty output | Non-positive or unsupported dimensions/frame count, model geometry constraint, or wrong workload | Start with the model preset defaults and small supported dimensions; verify width/height/frame divisibility and workload. |
| `ImportError` for attention backend | Optional kernel absent or ABI mismatch | Return to SDPA if supported, or install the backend variant matching torch, CUDA, Python, and GPU. Do not silently claim the optimized path. |
| Out-of-memory during generation | Model/resolution/frame count or parallelism exceeds VRAM | Reduce frames/resolution/steps, use supported offload, distilled model, or multiple GPUs; disable memory-expensive return trajectories. |
| Compile is slower | First-run graph build included in timing or shapes changed | Discard warmup, reuse exact shapes, compare same seed/config, and avoid unsupported CUDA-graph modes. |
| Output file missing or wrong extension | `save_video` false, unwritable directory, or workload-specific extension | Inspect result `video_path`, create a writable output directory, and remember image/audio workloads save PNG/WAV. |
| Deprecated warning from `generate_video` | Legacy compatibility API used | Migrate to `GenerationRequest` and `generate()`; preserve only fields supported by the typed schema. |
| Generation quality changes after optimization | Quantization, sparse attention, compile, or different seed | Run an eager/dense baseline with identical prompt/seed/shapes; compare quality on the target model before accepting the optimization. |
