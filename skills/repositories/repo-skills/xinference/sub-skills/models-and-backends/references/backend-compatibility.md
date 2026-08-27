# Backend Compatibility

## General rules

- LLM launches require an explicit `model_engine`.
- Embedding, rerank, and image can fall back to a default engine when one is not supplied.
- Backend compatibility is gated by model format, quantization, platform, and sometimes the model-family allowlist.
- Virtualenv markers can make an engine appear during discovery, but they do not bypass GPU, OS, or accelerator requirements.
- `cal-model-mem` is a planning aid, not a launch guarantee.

## Optional extras and what they usually enable

| Extra or backend | Typical use | Platform or hardware | Key notes |
| --- | --- | --- | --- |
| `transformers` | Default PyTorch path for LLMs and many multimodal models | General CPU/GPU depending on the model | Supports `pytorch`, `gptq`, `awq`, `bnb`, and `fp4`. FP4 needs a newer `transformers` build with `FPQuantConfig`. |
| `transformers_quantization` | Special install path for AWQ/GPTQ | General, but install-time sensitive | Use with `--no-build-isolation` when the quantization stack needs a special resolver path. |
| `llama_cpp` / `xllamacpp` | GGUF models and selected embedding/rerank families | CPU or CUDA wheel depending on the host | `llama-cpp-python` is deprecated and removed. Per-model virtualenvs can auto-select a matching CUDA wheel on supported Linux hosts. |
| `vllm` | High-throughput LLMs, selected embedding families, selected image families | Linux + CUDA | The model must be in the supported family list. PyTorch requires `quantization=none`; AWQ requires `Int4`; GPTQ requires `Int3`, `Int4`, or `Int8`. Optional FlashInfer may be required for some features. |
| `sglang` | High-throughput LLMs and selected image families | Linux + CUDA | It is kept separate from `all` because of dependency conflicts. Diffusion support uses the diffusion add-on. |
| `mlx` | Apple-silicon LLM, image, and audio families | macOS arm64 | Use only on Apple silicon. |
| `embedding` | Sentence-transformer and FlagEmbedding families | CPU or GPU depending on the family | Also covers selected `vllm` and `llama_cpp` embedding routes. |
| `rerank` | FlagEmbedding rerank families | CPU or GPU depending on the family | Also covers selected `sentence_transformers`, `vllm`, and `llama_cpp` routes. |
| `image` | Diffusers-based image and OCR families | Often GPU for heavier models | Some families also support `vllm`, `sglang`, or `mlx` image engines. |
| `video` | Diffusers-based video families | Often GPU for heavier models | Custom video registration is not supported. |
| `audio` | ASR and TTS families | Mixed CPU/GPU/MPS depending on the family | Many audio families have extra per-model dependencies and engine-specific paths. |
| `otel` | Telemetry | None | Observability only, not a model backend. |
| `intel` | Intel XPU vendor path | Intel XPU | Optional vendor-specific install. |
| `musa` | MThreads/MUSA vendor path | MUSA-compatible hardware | Optional vendor-specific install. |

## Package-group notes

- `all` aggregates most runtime extras, but it deliberately does not include `sglang`.
- `vllm` and `sglang` are Linux-only in the package metadata.
- `mlx` is arm64 macOS-only in the package metadata.
- `embedding`, `rerank`, `image`, `video`, and `audio` are separate optional groups because their dependencies are large and family-specific.

## Memory planning

Use the memory estimator when you need a safe pre-launch estimate.

- Inputs: model size, quantization, context length, and optionally model name.
- Output: model memory, KV-cache memory, overhead, and active memory.
- Without a model name, Xinference falls back to default layer assumptions based on size.
- GGUF estimates and transformer estimates use different formulas.
- Real engine usage can be higher or lower than the estimate, especially for vLLM and GGUF routes.

## Backend choice patterns

- Use `transformers` when you have a PyTorch-family model and no backend-specific reason to switch.
- Use `llama_cpp` for GGUF-family models.
- Use `vllm` or `sglang` only when the platform and the model family both support them.
- Use `mlx` only on Apple silicon.
- If a model only appears through virtualenv markers, confirm that the host also satisfies the hardware gate.
