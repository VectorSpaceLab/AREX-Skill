# Compatibility and verification boundaries

## Python and base package

- Distribution name: `outlines`.
- Import root: `outlines`.
- Python metadata in the source revision: `>=3.10,<3.14`.
- Base dependencies include Jinja2, cloudpickle, diskcache, Pydantic v2, jsonschema, Pillow, typing-extensions, `outlines_core==0.2.14`, and GenSON.

## Optional integrations

Install optional dependencies by selected route, not all at once.

| Route | Typical packages/extras | Notes |
|---|---|---|
| Transformers | `transformers`, `torch`, optionally `accelerate`, `datasets`, `sentencepiece` | Model downloads and device placement are underlying-library concerns. |
| llama.cpp | `llama-cpp-python`, optional Hugging Face hub packages | Wheel/build flags and GGUF files determine CPU/GPU behavior. |
| MLX-LM | `mlx`, `mlx-lm` | Apple Silicon/macOS only in practical use. |
| vLLM offline | `vllm`, CUDA-compatible torch stack | GPU-capable environment and model weights normally required. |
| OpenAI/SGLang/vLLM server | `openai` SDK | Loader route determines structured-output request body. |
| TGI | `huggingface_hub` | Needs endpoint URL for live service. |
| Provider-specific SDKs | `anthropic`, `google-genai`, `mistralai`, `ollama`, `lmstudio`, `dottxt` | Do not probe live services without credentials and authorization. |
| Locale helper types | `airportsdata`, `iso3166` | Optional `outlines.types.airports`/`countries` data packages. |

## What the generated skill verified

The creation environment verified:

- Base package import and distribution metadata.
- `outlines`, `outlines.types`, `outlines.backends`, `outlines.models`, and `outlines.inputs` imports.
- Public signatures for `Generator`, `Template`, `Application`, `Chat`, `Image`, output-type wrappers, and provider/local loader functions.
- CPU/base construction of output terms and template rendering.
- The source tree contains tests/docs/examples for optional integrations, but those optional stacks were not installed in the minimum environment.

## What remains optional or unverified

- Live provider calls, credentials, remote endpoints, and service-specific structured-output behavior.
- CUDA/ROCm/MPS device execution.
- vLLM offline engine initialization and guided decoding.
- Transformers or llama.cpp model downloads and generation.
- MLX-LM runtime, because the production host is Linux rather than Apple Silicon.
- Deployment examples for BentoML, Cerebrium, Beam, Modal, or similar services.

## Hardware guidance

- A visible NVIDIA GPU is not enough to claim CUDA support. Verify the selected torch/vLLM/llama.cpp build with a tiny device operation.
- Use Python 3.10 or 3.11 for broad ML wheel compatibility unless the selected package path explicitly supports newer versions.
- Do not install a CPU-only torch wheel and call CUDA verified.
- Do not treat skipped optional/hardware tests as passing.

## Provider guidance

- Provider wrappers differ in JSON/regex/CFG, async, streaming, and batch support.
- OpenAI-compatible clients may be wrapped by `from_openai`, `from_sglang`, or `from_vllm`; choose the route matching the server behavior.
- Missing API keys and endpoints are configuration facts, not package install failures.

## Native verification candidates

A safe CPU/mock subset can validate core logic, template/input behavior, and provider error/type-adapter behavior. Heavy local model, GPU, MPS, and live provider tests require explicitly prepared environments and should remain optional unless the downstream task requires those capabilities.
