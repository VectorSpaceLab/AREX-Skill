---
name: models-and-configuration
description: "Choose, configure, inspect, and troubleshoot CAMEL model backends,
  provider enums, config classes, local/OpenAI-compatible endpoints,
  ModelFactory, ModelManager, and structured output behavior."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Models and Configuration

Use this sub-skill when a task involves CAMEL model selection, provider setup, model backend construction, model config dictionaries, structured outputs, local serving endpoints, or model fallback/scheduling.

## Read This First

- Start with [API reference](references/api-reference.md) for `ModelFactory`, `BaseModelBackend`, `ModelManager`, `ModelPlatformType`, `ModelType`, audio model classes, and schema converters.
- Use [Provider patterns](references/provider-patterns.md) to choose OpenAI, OpenAI-compatible, Ollama, vLLM, LMStudio, cloud providers, custom clients, and credential handling patterns.
- Use [Configuration](references/configuration.md) for `camel.configs` classes, `model_config_dict`, JSON/YAML factory configs, retries, timeouts, streaming, structured output settings, and optional extras.
- Use [Troubleshooting](references/troubleshooting.md) when imports fail, API keys are missing, provider/type pairs do not match, local endpoints refuse connections, structured output parsing fails, or Python 3.13 exposes optional dependency gaps.
- Run [inspect_model_registry.py](scripts/inspect_model_registry.py) to list installed CAMEL model platforms, backend classes, model enum counts, and config classes without making provider calls.

## Common Entry Points

- `from camel.models import ModelFactory` then `ModelFactory.create(...)` for most chat model backends.
- `from camel.types import ModelPlatformType, ModelType` for provider/model enums; use a plain string `model_type` for local/custom model names that are not in `ModelType`.
- `from camel.configs import ChatGPTConfig, OllamaConfig, VLLMConfig, LMStudioConfig, ...` and pass `ConfigClass(...).as_dict()` as `model_config_dict`.
- Pass the model object, or a list of model objects, into `camel.agents.ChatAgent(model=...)`; see sibling [agents-and-societies](../agents-and-societies/SKILL.md) for agent orchestration.
- Keep embeddings and vector retrieval in sibling [memory-rag-and-data](../memory-rag-and-data/SKILL.md), and tool schema/runtime details in sibling [tools-runtimes-and-services](../tools-runtimes-and-services/SKILL.md).

## Fast Routing

- Need a cloud provider backend: read [Provider patterns](references/provider-patterns.md#provider-setup-patterns) and [Configuration](references/configuration.md#provider-config-classes).
- Need a local OpenAI-compatible endpoint: read [Provider patterns](references/provider-patterns.md#openai-compatible-and-local-endpoints).
- Need structured JSON/Pydantic output: read [API reference](references/api-reference.md#structured-output-and-schema-conversion) and [Troubleshooting](references/troubleshooting.md#structured-output-failures).
- Need failover, load balancing, or model scheduling: read [API reference](references/api-reference.md#modelmanager-and-chatagent-scheduling).
- Need to know what the installed package exposes: run `python scripts/inspect_model_registry.py --format text`.
