# Local model troubleshooting

## Optional package missing

Symptoms:

- `ModuleNotFoundError: transformers`, `llama_cpp`, `mlx_lm`, or `vllm`.
- `outlines` imports, but the selected local wrapper fails during setup.

Actions:

1. Install only the selected optional runtime.
2. Verify with `scripts/check_local_model_prereqs.py`.
3. Avoid broad installs such as every Outlines extra unless a dedicated environment can absorb the risk.

## Model/tokenizer mismatch

Symptoms:

- Tokenizer cannot encode/decode expected prompts.
- Chat prompts are malformed.
- Generation fails because eos/pad tokens or vocabulary shape disagree.

Actions:

- Load the tokenizer/processor intended for the exact model revision.
- For chat models, inspect whether the tokenizer has a chat template.
- If no chat template exists, pass a fully formatted prompt string or use a model-specific template from the underlying library.
- For multimodal processors, align prompt image markers with the number of `Image` objects.

## Device, dtype, and VRAM failures

Symptoms:

- CUDA out of memory.
- CPU-only torch installed on a GPU host.
- dtype conversion failure after `device_dtype`.
- vLLM cannot initialize the engine.

Actions:

1. Check actual framework backend, not just `nvidia-smi`.
2. Use a smaller model, lower precision, lower max sequence length, or CPU fallback when supported.
3. Install torch/vLLM wheels compatible with the driver and Python version.
4. Treat `vLLMOffline` as requiring a GPU-capable vLLM setup unless documented otherwise.

## llama.cpp build or GGUF issues

Symptoms:

- `llama-cpp-python` install compiles for a long time or fails.
- GGUF file cannot be found or has incompatible metadata.
- Chat responses include control tokens or empty chunks.

Actions:

- Use a wheel/build matching CPU/GPU offload needs.
- Confirm the `repo_id`, `filename`, and `chat_format` before constructing the wrapper.
- For streaming JSON, ignore empty role/control chunks until the first non-empty token when appropriate.
- Do not run source repo examples as hidden downloads; create explicit model acquisition steps.

## MLX-LM on the wrong host

Symptoms:

- `mlx` import fails.
- Metal is unavailable.
- Tests are skipped with Apple Silicon requirement.

Actions:

- On Linux or non-Apple-Silicon hosts, route to Transformers CPU/GPU or a hosted provider.
- Do not install arbitrary MLX packages expecting them to provide MPS on Linux.

## vLLM server vs offline confusion

Symptoms:

- User has an OpenAI-compatible vLLM server URL but code uses `from_vllm_offline`.
- User has a local `vllm.LLM` object but code uses `from_vllm`.

Actions:

- Use `from_vllm_offline(LLM(...))` for in-process vLLM.
- Use `from_vllm(openai_client, model_name=None)` for a running vLLM OpenAI-compatible server.
- Provider/server mode belongs in `../../remote-providers/SKILL.md`.

## Backend mismatch

Symptoms:

- CFG with `outlines_core` fails.
- `xgrammar` fails with LlamaCpp.
- `JsonSchema(..., whitespace_pattern=...)` fails with `llguidance`/`xgrammar`.

Actions:

- See `../../structured-generation/references/backends.md`.
- Pick the backend after choosing the local wrapper, not before.

## Unsupported batch or stream

Symptoms:

- Transformers streaming raises `NotImplementedError`.
- llama.cpp batch raises or tokenizer rejects list input.
- vLLM offline stream raises `NotImplementedError`.
- MLX-LM constrained batch raises `NotImplementedError`.

Actions:

- Use wrapper-specific capabilities rather than assuming common support.
- For unsupported batch, loop with bounded concurrency only if the underlying engine can safely handle it.
- For unsupported streaming, generate bounded non-streaming outputs and parse after completion.
