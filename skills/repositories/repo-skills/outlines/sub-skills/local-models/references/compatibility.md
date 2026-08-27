# Local model compatibility

## Minimum verified scope

The generated repo skill was prepared with a base CPU inspection environment. It verified Outlines importability and loader signatures, but it did **not** install or verify torch/Transformers, llama-cpp-python, MLX-LM, vLLM, CUDA runtime generation, MPS runtime generation, or any model weights.

Use this compatibility reference to avoid overstating runtime readiness.

## Wrapper matrix

| Wrapper | Optional dependency direction | Hardware/service | Structured-output route | Batch | Stream | Key caveats |
|---|---|---|---|---:|---:|---|
| `from_transformers` | `transformers`, `torch`, tokenizer/model packages | CPU or CUDA depending on model size | Outlines backends turn output types into logits processors | yes | no in this revision | model download, tokenizer chat template, pad/eos setup, dtype/device |
| Transformers multimodal | `transformers`, `torch`, processor/model packages | Usually CUDA for useful models; tiny CPU tests possible | same local backend path | yes for compatible inputs | no | image count/format must match processor |
| `from_llamacpp` | `llama-cpp-python`, GGUF model | CPU or GPU-offload depending on build | outlines_core/llguidance; xgrammar unsupported for LlamaCpp | no | yes | compiled wheel/toolchain, GGUF download, chat format |
| `from_mlxlm` | `mlx`, `mlx-lm`, compatible tokenizer | Apple Silicon/macOS MPS/Metal | outlines_core/llguidance/xgrammar | plain batch only | yes | unavailable on Linux CPU; constrained batch unsupported |
| `from_vllm_offline` | `vllm`, compatible torch/CUDA stack | NVIDIA GPU normally required | vLLM guided decoding params | text batch yes | no | not server `from_vllm`; GPU/model download/version constraints |

## Backend/output compatibility

For local steerable models, output types compile into logits processors or guided-decoding parameters.

| Output type | Transformers | llama.cpp | MLX-LM | vLLM offline |
|---|---:|---:|---:|---:|
| Plain text | yes | yes | yes | yes |
| Basic/simple types | yes | yes | yes | yes |
| JSON schema / Pydantic | yes | yes | yes | yes |
| Literal / Enum / Choice | yes | yes | yes | yes |
| Regex | yes | yes | yes | yes |
| CFG | yes with compatible backend | yes with `llguidance`; not `outlines_core` | yes with compatible backend | yes if vLLM version supports structured outputs |
| Custom `OutlinesLogitsProcessor` | yes | yes | yes | not via the same processor path |

Always check backend support in `../../structured-generation/references/backends.md` before choosing `backend=`.

## Hardware decision rules

- A visible GPU does not mean the selected environment is CUDA-ready. Verify the actual torch/vLLM/llama.cpp build and a tiny device operation before claiming CUDA support.
- vLLM offline should be treated as GPU-required unless a specific vLLM version/model path documents otherwise.
- MLX-LM is for Apple Silicon; on Linux, route users to Transformers CPU/GPU or a hosted provider instead.
- llama.cpp can run CPU-only, but wheel/build options and GGUF model acquisition are still runtime prerequisites.
- Large model examples in the source repo are evidence, not safe default commands.

## Optional dependency installation examples

Install only the selected stack:

```bash
pip install outlines
pip install transformers torch
pip install llama-cpp-python
pip install mlx mlx-lm          # Apple Silicon only
pip install vllm                # GPU-capable vLLM environment
```

Prefer the official install instructions for torch/vLLM/CUDA/ROCm wheels and for `llama-cpp-python` builds. Do not mix incompatible torch CUDA tags, Python versions, or source-built extension packages without checking ABI compatibility.

## Verification levels

- **Import check**: optional package imports; proves only that Python can see the package.
- **Object construction**: create tokenizer/model wrapper with a tiny object; may still avoid model generation.
- **Tiny generation**: generate a short response with a small model; may require downloads.
- **Backend smoke**: allocate a tiny CUDA/MPS tensor or run vLLM guided decoding; required before claiming hardware backend coverage.
- **Native example/test**: execute a selected safe repo-native test after the whole skill is integrated; not a substitute for hardware smoke when hardware is required.
