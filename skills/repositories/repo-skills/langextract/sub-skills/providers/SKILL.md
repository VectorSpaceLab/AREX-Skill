---
name: providers
description: "Choose, configure, inspect, and troubleshoot LangExtract model
  providers and batch backends."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# LangExtract Providers

Use this sub-skill when a task depends on selecting or configuring the LangExtract language-model backend: Gemini, Vertex AI, OpenAI/GPT, OpenAI-compatible endpoints, Ollama/local models, provider routing, provider kwargs, or batch behavior.

## Fast route

1. Decide whether the user is doing provider setup or prompt/extraction design.
   - Provider/backend choice, API keys, `ModelConfig`, `language_model_params`, batch mode, Ollama daemon/model checks: stay here.
   - Prompt, examples, `output_schema` shape, tokenization, resolver tuning, or extraction result grounding: route to [extraction](../extraction/SKILL.md).
   - Custom provider package scaffolding, entry points, plugin conflicts, or schema implementation for a new provider: route to [provider-plugins](../provider-plugins/SKILL.md).
   - JSONL persistence or HTML output: route to [visualization](../visualization/SKILL.md).
2. Inspect routing without secrets or network by running the bundled route checker:
   ```bash
   python sub-skills/providers/scripts/check_provider_routes.py
   ```
3. Use [references/providers.md](references/providers.md) for exact provider patterns, factory APIs, environment-variable precedence, schema/fence interactions, and batch configuration.
4. Use [references/troubleshooting.md](references/troubleshooting.md) when provider creation or inference fails.
5. For local Ollama, start with a preflight-only check before inference:
   ```bash
   python sub-skills/providers/scripts/ollama_demo.py --model gemma2:2b --preflight-only
   ```

## Provider selection checklist

- Prefer `model_id` auto-routing for known IDs: `gemini...` for Gemini, `gpt-4...` or `gpt-5...` for OpenAI, and common local IDs such as `gemma2:2b`, `llama3.2:1b`, `qwen...`, or `gpt-oss...` for Ollama.
- Use `langextract.factory.ModelConfig(provider=..., provider_kwargs=...)` when a model ID does not match a built-in pattern, when an OpenAI-compatible endpoint uses a non-GPT ID, or when multiple providers could match.
- Do not put secrets in generated code. Read API keys from environment variables or caller-owned secret stores.
- Treat live Gemini/OpenAI/Vertex/Ollama checks as optional. This sub-skill only establishes configuration and local/no-network inspection unless the caller explicitly supplies credentials or a local daemon.
- Batch APIs are opt-in and only trigger when the prompt/chunk count meets the configured threshold.

## Runtime helpers

- `scripts/check_provider_routes.py`: safe, no-network provider registry and sample model-ID resolver.
- `scripts/ollama_demo.py`: local Ollama preflight plus optional tiny extraction demo. It does not require the source repository checkout.

## Evidence basis

This guidance is distilled from `README.md`, `langextract/providers/README.md`, `docs/examples/batch_api_example.md`, `examples/ollama/`, `langextract/factory.py`, `langextract/providers/router.py`, `builtin_registry.py`, `patterns.py`, `gemini.py`, `openai.py`, `ollama.py`, `gemini_batch.py`, `openai_batch.py`, and provider schema modules. Related native verification candidates include `factory_test.py`, `factory_schema_test.py`, `provider_schema_test.py`, `inference_test.py`, `test_kwargs_passthrough.py`, `test_gemini_batch_api.py`, `gemini_retry_test.py`, `openai_batch_test.py`, optional `test_live_api.py`, and optional `test_ollama_integration.py`; do not run those from this sub-skill unless the root verification plan asks for them.
