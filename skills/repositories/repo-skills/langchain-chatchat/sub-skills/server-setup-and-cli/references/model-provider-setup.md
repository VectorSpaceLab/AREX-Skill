# Model Provider Setup

## When to read

Read this before configuring model backends for Langchain-Chatchat. Chatchat's service and APIs depend on external LLM/embedding providers for meaningful chat, RAG, tools, and vector rebuilds.

## Provider model

Chatchat model settings are OpenAI-compatible provider configs. Common provider types include:

- `xinference`
- `ollama`
- `oneapi`
- `fastchat`
- `openai`
- `custom openai`

Each model platform has at least a platform name/type, `api_base_url`, `api_key`, concurrency, and model lists or auto-detect settings. The default provider in inspected settings was Xinference at `http://127.0.0.1:9997/v1`, but generated YAML should be treated as a template, not proof that a provider is running.

## Separation rule

Keep Chatchat and heavy model-serving frameworks separate unless the user explicitly wants a combined environment. The upstream docs warn that installing Chatchat with provider frameworks such as Xinference in one environment can trigger dependency conflicts. Prefer:

```text
Chatchat env/container  --->  OpenAI-compatible HTTP endpoint  --->  model provider env/container
```

This makes Chatchat upgrades, provider upgrades, CUDA packages, and model downloads independently diagnosable.

## Provider validation checklist

Before running `chatchat kb -r` or chat APIs:

1. Start the provider service.
2. Load/register at least one LLM model and one embedding model.
3. Confirm model names exactly as the provider exposes them.
4. Put those names in `DEFAULT_LLM_MODEL`, `DEFAULT_EMBEDDING_MODEL`, and any relevant role-specific `LLM_MODEL_CONFIG` entries.
5. Confirm `api_base_url` points to an OpenAI-compatible route root expected by the provider.
6. Set `api_key` and `api_proxy` only when required; do not invent credentials.
7. If auto-detect is enabled, install only the optional client package needed for that provider and only in the Chatchat env if that is acceptable.

## Xinference-specific notes

The repo includes a Streamlit helper conceptually used to inspect Xinference model registrations and cache paths. This skill does **not** bundle that UI as a runnable script because it depends on `streamlit`, `xinference`, a live Xinference service, local model paths, and buttons that mutate model cache/registrations.

Safe distilled usage:

- Start Xinference separately.
- Register or load models in Xinference, either through its UI/API or provider documentation.
- Configure Chatchat `MODEL_PLATFORMS` with the Xinference OpenAI-compatible endpoint.
- Keep model paths and provider cache details out of Chatchat skill/runtime files.
- If `auto_detect_model` logs that `xinference-client` is missing, either install `langchain-chatchat[xinference]` in the Chatchat env or turn off auto-detect and list model names manually.

## Ollama/LocalAI/FastChat/One API notes

- Use the provider's own health/model-list command first.
- Ensure Chatchat's `api_base_url` matches the provider's OpenAI-compatible URL convention.
- Provider-specific model names can differ from local filenames or registry names; use the provider-exposed API name.
- Some providers support function/tool calling better than others. For weak tool-calling models, use manual `tool_choice` and `tool_input` patterns from the API sub-skill.

## Hardware boundaries

- Chatchat package import and API route inspection are CPU checks.
- Loading local LLMs/embeddings may require CUDA, MPS, NPU, large RAM, or model-specific runtimes, but that is a provider verification task.
- Do not call GPU/provider readiness verified unless a concrete provider model-list and a small completion/embedding request pass.
