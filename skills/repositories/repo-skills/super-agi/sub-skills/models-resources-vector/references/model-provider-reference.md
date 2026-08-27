# Model Provider Reference

## When to Read

Read this when configuring or debugging SuperAGI's model provider layer.

## Provider Enum

`ModelSourceType` recognizes these public values:

- `Google Palm`
- `OpenAi`
- `Replicate`
- `Hugging Face`
- `Local LLM`

`get_model_source_from_model` maps common OpenAI, Google, and Replicate model
names to provider types and defaults unknown names to OpenAI.

## Factory Behavior

`build_model_with_api_key(provider_name, api_key)` builds a provider instance by
case-insensitive provider name:

- `openai` -> `OpenAi`
- `replicate` -> `Replicate`
- `google palm` -> `GooglePalm`
- `hugging face` -> `HuggingFace`
- `local llm` -> `LocalLLM`

`get_model(organisation_id, api_key, model, **kwargs)` reads model/provider rows
from the database, then returns the provider wrapper with configured model name
and provider-specific fields.

## Live Validation Warning

Provider access-key verification calls provider-specific network methods. Do not
use those checks as a harmless smoke test; they require real user credentials and
may fail due to upstream/network policy.

## Local LLM Notes

The config template supports an OpenAI-compatible local base URL. For the Docker
GPU path, the commented internal endpoint points at a text-generation-webui
service. Local LLM success depends on both config values and an actual running
service.

## Image LLMs

The source contains image LLM wrappers such as OpenAI DALL·E and stable
diffusion tool wrappers in the tools tree. Route toolkit execution details to
`toolkits-integrations`; use this file for provider/config decisions.
