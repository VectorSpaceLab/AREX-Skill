---
name: model-client-and-generator-workflows
description: "Use AdalFlow ModelClient, Generator, and Embedder workflows for
  provider integration, prompt/model kwargs, output processors, caching,
  streaming basics, and no-credential fake-client tests."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Model Client and Generator Workflows

Use this sub-skill when a task involves AdalFlow model-provider plumbing rather than retrieval, agents, optimization, or tracing.

## Load when

- Building or debugging `Generator`, `ModelClient`, `Embedder`, or `BatchEmbedder` flows.
- Selecting provider clients or optional extras for OpenAI/OpenAI-compatible, Anthropic, Groq, Google, Ollama, Together, Cohere, Azure, Bedrock, Fireworks, Mistral, DeepSeek, XAI, SambaNova, or local Transformer integrations.
- Configuring prompt templates, `prompt_kwargs`, `model_kwargs`, `ModelType`, output processors, cache behavior, or streaming response handling.
- Writing no-network tests with a fake `ModelClient`.

## Route elsewhere

- RAG, indexes, retrievers, `LocalDB`, vector stores, and document pipelines: use `retrieval-rag-and-data-pipelines`.
- Agent, Runner, ReAct, FunctionTool, tool streaming, permissions, and MCP: use `agents-tools-and-streaming`.
- Evaluation, datasets, `Trainer`, optimizers, text gradients, and few-shot training: use `evaluation-and-optimization`.
- Logging, generator-state/call loggers, callback tracing, MLflow, and config utilities: use `tracing-observability-and-configuration`.
- Core `Component`, `Prompt`, `DataClass`, and parser schema construction without model calls: use `core-components-and-structured-io`.

## Internal references

- [Generator workflows](references/generator-workflows.md): prompt rendering, call/acall/forward, output processors, caching, streaming, fake-client tests, embedder orchestration.
- [Model clients](references/model-clients.md): protocol requirements, provider extras/lazy imports, provider notes, OpenAI-compatible patterns, direct client usage.
- [API reference](references/api-reference.md): verified signatures, return fields, `ModelType`, `GeneratorOutput`, `EmbedderOutput`, and concise call contracts.
- [Troubleshooting](references/troubleshooting.md): optional SDK/API-key errors, bad `model_kwargs`, parser failures, `GeneratorOutput.error`, cache surprises, streaming, and image/content formatting.
- [Fake-client smoke script](scripts/generator_fake_client_smoke.py): deterministic no-credential sanity check for `Generator`, `JsonParser`, `Embedder`, and `BatchEmbedder`.

## Operating checklist

1. Decide whether the workflow is service-free or requires a live provider. Prefer the bundled fake-client script for unit tests and examples.
2. Pick the correct `ModelType`: `LLM` for text generation, `LLM_REASONING` for reasoning-compatible LLM endpoints, `EMBEDDER` for embeddings, and provider-specific types only after checking support.
3. Keep `model_kwargs` provider-shaped and JSON-serializable when caching is enabled. Pass per-call overrides through `Generator.call(..., model_kwargs={...})` or `Embedder.call(..., model_kwargs={...})`.
4. Render and inspect the prompt with `generator.get_prompt(...)` before blaming the provider. Missing or mismatched Jinja variables usually become poor prompts, not provider errors.
5. Treat `GeneratorOutput.error` as the authoritative failure signal. Check `raw_response`, `api_response`, and parser configuration before retrying live API calls.
6. For streaming, consume `raw_response`/`stream_events()` and do not expect structured output processors to run until a complete text response is available.
7. Do not embed API keys in generated code or logs. Use provider environment variables or explicit runtime configuration supplied by the caller.
