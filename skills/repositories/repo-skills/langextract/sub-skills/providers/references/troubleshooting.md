# Provider Troubleshooting

Use this guide when LangExtract fails while selecting, creating, or using a language-model provider. Prompt/example/schema-shape problems belong in `../extraction/SKILL.md`; custom plugin package problems belong in `../provider-plugins/SKILL.md`.

## Quick triage

1. Reproduce provider selection without secrets or network:
   ```bash
   python scripts/check_provider_routes.py --skip-plugins
   python scripts/check_provider_routes.py gemini-3.5-flash gpt-4o gemma2:2b
   ```
2. Decide which stage failed:
   - provider routing (`No provider registered` or wrong provider class);
   - provider construction (`InferenceConfigError`, missing SDK, API key, Vertex config);
   - live inference (`InferenceRuntimeError`, quota, timeout, daemon unavailable);
   - structured output/schema negotiation (`output_schema`, fences, JSON mode);
   - batch job creation/polling/output download.
3. Keep live calls separate from no-network checks. Do not treat an optional credentialed or daemon-backed skip as a package failure.

## Provider routing failures

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `No provider registered for model_id=...` | Model ID does not match built-in patterns and no plugin registered. | Use `factory.ModelConfig(provider=...)`, install/enable a plugin, or choose a model ID that matches Gemini (`gemini...`), GPT/OpenAI (`gpt-4...`, `gpt-5...`), or Ollama/local families. |
| OpenAI-compatible model ID does not auto-route | Built-in OpenAI auto-routing only matches GPT-style IDs. | Use `ModelConfig(provider="openai", provider_kwargs={"base_url": ..., "api_key": ...})`. |
| Wrong provider wins for a local model | A model ID overlaps a built-in or plugin pattern. | Inspect `router.list_entries()` with the route checker. Use explicit `provider=` or a less ambiguous model ID. |
| A custom plugin is not discovered | Plugin not installed in the active Python, entry point missing, discovery disabled, or plugin import failed. | Route to `../provider-plugins/SKILL.md`; inspect entry points and `LANGEXTRACT_DISABLE_PLUGINS`. |

## Credentials and constructor errors

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Gemini error says an API key or Vertex AI config is required | Neither `api_key`/Gemini env vars nor complete Vertex AI config was supplied. | Set `GEMINI_API_KEY` or `LANGEXTRACT_API_KEY`, or pass `language_model_params={"vertexai": True, "project": "...", "location": "..."}`. |
| Vertex AI mode requires both project and location | `vertexai=True` without `project` or `location`. | Pass both fields explicitly. `location` commonly uses `us-central1` or the region required by the project. |
| Both API key and Vertex AI config are present | Gemini API key takes precedence for authentication, which may not be what the user intended. | Remove the unused path and keep either API-key Gemini or Vertex AI configuration. |
| OpenAI provider says the `openai` package is missing | The optional dependency was not installed. | Install with `python -m pip install "langextract[openai]"` or install a package environment that includes the OpenAI extra. |
| OpenAI provider says API key not provided | `OPENAI_API_KEY`/fallback key missing and no explicit `api_key`. | Set `OPENAI_API_KEY` or pass an explicit `api_key` in provider kwargs. Do not print the secret. |
| Unknown provider name with explicit `provider=` | Name does not match registered class/pattern or plugin failed import. | Use a precise class name such as `OpenAILanguageModel` or inspect route checker output. |

## Live inference failures

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Gemini/OpenAI rate-limit, quota, 5xx, overloaded, timeout, or transient network error | Service-side or network transient. | Retry with provider retry controls, lower `max_workers`, reduce batch size, or wait. For Gemini, use `max_retries`, `retry_delay`, and `max_retry_delay` in `language_model_params`. |
| Gemini constructor rejects stacked retries | SDK `http_options.retry_options` and provider `max_retries>0` both configured. | Use only one retry layer: set provider `max_retries=0` or remove SDK retry options. |
| OpenAI runtime error during parallel calls | One worker failed or API rejected request params. | Reproduce with one prompt and `max_workers=1`; then restore parallelism. |
| Ollama request fails to connect | Ollama daemon is not running or `model_url`/`base_url` is wrong. | Run the local service, set the correct URL, and preflight with `python scripts/ollama_demo.py --preflight-only`. |
| Ollama 404 says it cannot find the model | The model has not been pulled into the local Ollama store. | Pull the model outside LangExtract, then rerun preflight. |
| Ollama timeout on large/slow model | Model is slow, context too large, or hardware constrained. | Increase `timeout`, reduce prompt size / `max_char_buffer`, use a smaller model, or reduce `num_ctx`. |
| Ollama returned only a thinking trace | A reasoning model produced reasoning but no final JSON, often because `think=True` was passed. | Let LangExtract default `think=False`; do not consume `thinking` as extraction output. |

## Batch API failures

### Gemini / Vertex batch

- Batch mode only runs when prompt count is at least `threshold`; below threshold, realtime Gemini is used.
- When `batch.enabled=True`, `enable_caching` and `retention_days` must be explicitly supplied. Use `retention_days=None` only when permanent retained objects are intended.
- Vertex batch requires Vertex credentials, project/location, GCS permissions, and network access.
- If output has per-item errors and `ignore_item_errors=False`, treat the batch as failed. If ignoring item errors, preserve the fact that some prompts did not produce outputs.

### OpenAI batch

- OpenAI batch uses the Files and Batch APIs. A 403 while downloading output often means the API key lacks Files read permission.
- `completion_window` must be `"24h"` for the helper.
- Batch is for non-latency-sensitive work. Do not use it to debug a single bad prompt; reproduce bad behavior through realtime calls first.

## Schema and fence mismatches

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Error says `output_schema` cannot be combined with fences | `fence_output=True` was forced. | Remove it or set `fence_output=False`. Schema-constrained Gemini/OpenAI output is raw JSON. |
| Error says `output_schema` requires JSON | YAML `format_type` or incompatible resolver format handler. | Use JSON defaults. Route raw schema envelope details to `../extraction/SKILL.md`. |
| Error mentions `response_format`, `response_schema`, or `response_json_schema` conflict | Caller supplied provider-native schema kwargs while also using `output_schema`. | Let `output_schema` own the structured output, or remove `output_schema` and manage provider kwargs manually. |
| OpenAI strict structured outputs reject a schema | OpenAI strict mode requires supported JSON Schema shapes and object fields listed in `required`. | Prefer the `lx.schema` helpers or revise raw schema to OpenAI-compatible strict JSON. |
| Ollama user `output_schema` unsupported | Ollama exposes JSON format mode, not LangExtract's user-authored schema path. | Use examples and JSON format mode with Ollama, or choose Gemini/OpenAI for explicit `output_schema`. |

## Safe diagnostics

- `scripts/check_provider_routes.py` is safe: it imports LangExtract, loads built-ins/plugins unless skipped, and resolves provider classes without calling APIs.
- `scripts/ollama_demo.py --preflight-only` is safe for local service detection and does not call `lx.extract()`.
- Constructor signature inspection is safe. Live `lx.extract()` calls are credentialed/network/model-cost checks and need user approval when not already part of the task.
