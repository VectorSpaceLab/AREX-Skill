# Models and Configuration Troubleshooting

## Quick Diagnosis Checklist

1. Confirm import/version: `python -c "import camel; print(camel.__version__ if hasattr(camel, '__version__') else camel)"`.
2. Inspect available platforms/configs without provider calls: `python scripts/inspect_model_registry.py --format text`.
3. Verify the platform/type pair: use a dedicated `ModelPlatformType` for known backends or `OPENAI_COMPATIBLE_MODEL` for generic OpenAI-compatible services.
4. Keep service URL and model name separate: `url` is the base URL, `model_type` is the provider/local model id.
5. Determine whether the failure occurs during import, backend construction, request sending, response parsing, or agent orchestration.

## Missing Provider Extras

Symptoms:

- `ModuleNotFoundError` or `ImportError` for provider SDKs such as `anthropic`, `mistralai`, `litellm`, `boto3`, `cohere`, `fish_audio_sdk`, `xai_sdk`, `transformers`, or media packages.
- A backend import fails before any API request is sent.

Fixes:

- Install the smallest relevant extra, usually `camel-ai[model_platforms]` for provider SDKs or `camel-ai[huggingface]` for Hugging Face/local model utilities.
- Avoid `camel-ai[all]` unless the user explicitly wants a broad optional install.
- On Python 3.13+, check package metadata markers: some optional document/storage/media dependencies are intentionally excluded or changed for that interpreter.

## Missing API Keys or Environment Variables

Symptoms:

- Constructor or request error says an API key is required.
- `OpenAISchemaConverter()` fails before conversion because `OPENAI_API_KEY` is absent.
- OpenAI-compatible backend uses an unexpected endpoint because `OPENAI_COMPATIBILITY_API_BASE_URL` is not set.

Fixes:

- Prefer passing `api_key` and `url` from runtime secrets to `ModelFactory.create()` for one-off scripts.
- For OpenAI-compatible endpoints, set or pass both `OPENAI_COMPATIBILITY_API_KEY` and `OPENAI_COMPATIBILITY_API_BASE_URL`; local servers often accept a dummy key such as `EMPTY`, but cloud gateways do not.
- Do not store credentials in JSON/YAML factory config files that may be committed.

## Incorrect Platform and Model Type Pairs

Symptoms:

- `ValueError: Unknown model platform` from `ModelFactory.create()`.
- Provider rejects a known `ModelType` because it belongs to another provider.
- Local model name is not in `ModelType`.

Fixes:

- Use enum values exactly as exposed by `ModelPlatformType`; inspect with `scripts/inspect_model_registry.py`.
- Use plain strings for provider catalog or local model names not listed in `ModelType`.
- Use `ModelType.STUB` only for offline/test behavior; it forces `StubModel` regardless of platform map.
- When using `ModelPlatformType.DEFAULT` or `ModelType.DEFAULT`, check `DEFAULT_MODEL_PLATFORM_TYPE` and `DEFAULT_MODEL_TYPE` in the runtime environment.

## OpenAI-Compatible URL Confusion

Symptoms:

- 404 or route-not-found errors.
- Request path appears duplicated, such as `/v1/chat/completions/chat/completions`.
- Local service receives no request.

Fixes:

- Pass the base URL in `url`, usually ending in `/v1`; do not include `/chat/completions`.
- For vLLM, try `http://localhost:8000/v1` with `ModelPlatformType.OPENAI_COMPATIBLE_MODEL` or the dedicated `VLLM` backend.
- For Ollama, use dedicated `ModelPlatformType.OLLAMA` or its OpenAI-compatible base `http://localhost:11434/v1` if intentionally using the generic compatible backend.
- For LMStudio, confirm the local server is enabled and copy its base URL, not the UI URL.
- If using `api_mode="responses"`, verify the server actually implements OpenAI Responses API semantics; otherwise use default chat completions.

## Local Ollama, vLLM, SGLang, or LMStudio Not Running

Symptoms:

- `Connection refused`, `ConnectError`, `ReadTimeout`, or requests hang until `timeout`.
- CAMEL construction succeeds but `agent.step()` fails.

Fixes:

- Confirm the local server is running and the selected model is loaded/pulled.
- Test the service with its own health/model-list command before CAMEL.
- Increase `timeout` for first-token latency on large local models.
- Set `max_retries=1` while debugging local services to avoid repeated long waits.
- Verify firewall/container port mapping if CAMEL runs in a different environment from the model server.

## Structured Output Failures

Symptoms:

- `response.msgs[0].parsed` is `None` even though message content looks like JSON.
- Pydantic validation errors after a provider returns nonconforming JSON.
- Provider rejects `response_format`, tools plus schema, or streaming structured output.
- `OpenAISchemaConverter` returns a schema mismatch or requires `OPENAI_API_KEY`.

Fixes:

- Use a Pydantic `BaseModel` subclass for `response_format`; do not pass arbitrary dicts unless the provider specifically expects JSON mode.
- Add explicit prompt instructions to output valid JSON when using `{"type": "json_object"}` style JSON mode.
- Avoid combining structured output with tools on backends that reject it, such as Gemini's tool-plus-response-format path.
- Disable streaming while debugging structured output unless the backend explicitly supports structured streaming.
- If the provider only returns JSON text, parse manually with `MyModel.model_validate_json(response.msgs[0].content)` and tighten the prompt/schema.
- Choose the converter that matches the source: `OpenAISchemaConverter` calls OpenAI; it is wrong for local-only/offline conversion unless the user intentionally wants an OpenAI call.

Synthetic hard case: when a provider returns `{"studentLlst": ...}` for a schema field named `studentList`, distinguish provider noncompliance from a CAMEL converter bug. Check raw content, parsed object, schema spelling, and whether the backend used native parse or JSON-mode prompting.

## Audio and Multimodal Mismatches

Symptoms:

- Audio helper imports fail for media libraries.
- Provider rejects image/audio content.
- Model accepts text but ignores `image_list` or audio bytes.

Fixes:

- Install only relevant extras, such as provider SDKs and media tools, for the target workflow.
- Use `OpenAIAudioModels`/`FishAudioModel` for audio-specific APIs, not a generic chat model unless the provider supports audio chat.
- Confirm selected model type supports the modality; do not assume platform-wide support.
- For Bedrock Converse image data, source code handles data URL images; remote image URLs may need conversion to data URLs first.

## Rate Limits, Timeouts, and Retries

Symptoms:

- HTTP 429, quota exceeded, long request hangs, or repeated failures.
- Local server overload from retries.

Fixes:

- Reduce parallel agent/model calls before increasing retries.
- Set `timeout` based on provider/service latency.
- For local models, reduce `max_retries` during diagnosis.
- For provider 400/422 parameter errors, fix `model_config_dict` instead of retrying.

## Python 3.13 Optional Dependency Caveats

The package allows Python `>=3.10,<3.15`, but optional extras include environment markers. Some dependencies for document, storage, media, or RAG workflows differ or are skipped on Python 3.13+. If a model-adjacent optional import fails only on Python 3.13:

- Check whether the dependency is guarded by `python_version < '3.13'` or has a replacement marker.
- Reproduce in Python 3.10-3.12 before reporting a CAMEL model backend bug.
- Keep model provider troubleshooting separate from unrelated document/storage optional dependency failures.
