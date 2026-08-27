# Inference and Serving Troubleshooting

## Fast Triage

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `vLLM not install` | `infer_backend: vllm` selected without optional vLLM package. | Install compatible `vllm` or retry with `infer_backend=huggingface`. |
| `SGLang not install` | `infer_backend: sglang` selected without optional SGLang package. | Install compatible `sglang[all]` or retry with `infer_backend=huggingface`. |
| HTTP 401 `Invalid API key.` | `API_KEY` is set on the server but client did not send the exact bearer token. | Send `Authorization: Bearer $API_KEY`, or unset `API_KEY` for unauthenticated local testing. |
| HTTP 405 on `/v1/chat/completions` | Loaded model/engine cannot generate. | Use a generating SFT/chat model config, or use `/v1/score/evaluation` for scoring. |
| HTTP 405 on `/v1/score/evaluation` | Loaded model/engine can generate. | Use `/v1/chat/completions`, or load a scorer/reward model through the Hugging Face backend. |
| HTTP 400 `Cannot stream function calls.` | Client requested `stream: true` with `tools`. | Disable streaming for tool calls. |
| HTTP 400 `Cannot stream multiple responses.` | Client requested `stream: true` with `n > 1`. | Use `n: 1` for streaming or disable streaming. |
| Empty or malformed SSE handling | Client is treating SSE chunks as plain JSON lines. | Parse server-sent events; expect an initial empty delta and final `[DONE]`. |
| SGLang startup timeout/failure | Worker process could not launch, bind, download, or fit model. | Check CUDA/GPU memory/backend compatibility; fall back to Hugging Face if validating API shape. |
| vLLM score request failure | vLLM does not implement `get_scores`. | Use Hugging Face backend with a reward/scorer model for score evaluation. |

## API Auth and Root Path

`API_KEY` protects all registered routes. When it is set, every request to `/v1/models`, `/v1/chat/completions`, and `/v1/score/evaluation` must include the bearer token. If a reverse proxy strips authorization headers, the server will return 401 even if the client is configured correctly.

`FASTAPI_ROOT_PATH` only sets FastAPI's root path for proxy/sub-path deployments. It does not change the registered route names; client-facing proxy paths may include a prefix, but the app still registers `/v1/models`, `/v1/chat/completions`, and `/v1/score/evaluation` internally.

## Chat Payload Validation

The API parser removes an optional first `system` message, then expects an odd number of remaining messages in alternating order:

- Even positions: `user` or `tool`.
- Odd positions: `assistant` or `function`.

Common fixes:

- Remove incomplete trailing assistant messages from client history.
- Preserve tool-result messages as `tool` turns after assistant tool calls.
- Use non-streaming requests when `tools` are included.
- Keep `n` equal to 1 for streaming requests.

## Endpoint Choice

Use `/v1/chat/completions` for text, tool, and multimodal generation. Use `/v1/score/evaluation` only for reward/scorer models and pass `messages` as a list of strings, not OpenAI chat message objects.

If users report that the score endpoint returns 405 or a backend says `get_scores` is not implemented, the issue is usually endpoint/backend mismatch rather than model quality.

## Streaming SSE

The streaming endpoint emits JSON chunks as SSE data plus a final `[DONE]`. Clients should:

- Read event data from the SSE protocol instead of calling normal `response.json()`.
- Accept an initial assistant delta with empty content.
- Concatenate only non-empty `choices[0].delta.content` values.
- Stop when `[DONE]` arrives.

The bundled `openai_api_smoke.py --stream` path exercises this behavior through the OpenAI Python client.

## Backend Fallbacks

When a specialized backend fails before generation, first determine whether the failure is backend-specific or model-loading-specific:

- Import errors that name vLLM/SGLang are backend optional dependency issues; install the package or use `infer_backend=huggingface`.
- SGLang local server launch failures are often GPU, port, memory, model support, or optional package compatibility issues.
- vLLM engine construction failures may involve model support, dtype, tensor parallelism, multimodal limits, LoRA rank, or `vllm_config` overrides.
- Tokenizer, adapter, dtype, quantization, and device-map failures belong to `model-loading-and-export` after confirming the selected backend is installed.
- Template mismatch, missing multimodal placeholders, and dataset/template preprocessing errors belong to `data-and-templates`.

A safe diagnostic fallback is:

```bash
llamafactory-cli api CONFIG.yaml infer_backend=huggingface max_new_tokens=16
```

If this fallback also fails during model/tokenizer loading, route away from this sub-skill to model-loading investigation.

## Model Download and Device Failures

The inference surfaces may trigger model config, tokenizer, and weight downloads. Failures related to network access, cache permissions, unsupported model code, GPU OOM, missing CUDA, dtype incompatibility, quantization kernels, or LoRA adapter paths are model/environment issues. Keep this sub-skill focused on serving/API/backend behavior, then hand off with the exact failing launch command and selected `infer_backend`.

## Hard Synthetic Usability Cases

Use these as verification planning ideas outside the runtime tree:

- Authenticated API smoke with `API_KEY`: assert unauthenticated `/v1/models` returns 401, authenticated `/v1/models` returns `API_MODEL_NAME`, non-stream chat succeeds, streaming emits `[DONE]`, and score endpoint is either valid for a scorer or returns the documented 405 for a generator.
- Backend fallback case: start from a config requesting `infer_backend: vllm` in an environment without vLLM, diagnose the optional dependency error, rewrite only the backend override to `huggingface`, and preserve model/template/generation args while explaining that score evaluation still requires a scorer model.
