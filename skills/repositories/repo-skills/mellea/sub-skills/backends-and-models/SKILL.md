---
name: backends-and-models
description: "Configures and debugs Mellea inference backends, model
  identifiers, generation options, multimodal inputs, Granite adapters, and
  provider capabilities."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Mellea backends and models

Use this route when a task mentions Ollama, an OpenAI-compatible endpoint,
Hugging Face local inference, WatsonX, LiteLLM, Bedrock, Vertex AI, model IDs,
vision, audio, Granite formatters, intrinsics, LoRA/aLoRA, structured output,
provider credentials, or backend capability detection.

## Route first

1. Read [the backend API reference](references/api-reference.md) before
   constructing a backend or interpreting generation metadata.
2. Read [configuration guidance](references/configuration.md) to choose the
   provider, install only the needed extra, identify credentials/services, and
   layer model options.
3. Use [the backend matrix](references/model-and-backend-matrix.md) to check
   model-name fields and multimodal/adapter support before passing a
   `ModelIdentifier`.
4. For images, audio, Granite formatters, structured output, or adapters, read
   [multimodal and adapters](references/multimodal-and-adapters.md).
5. For failures, follow [troubleshooting](references/troubleshooting.md) and
   run the safe [backend checker](scripts/check_backends.py) before changing
   credentials, services, checkpoints, or device settings.

## Common operating decisions

- Prefer `start_session()` for ordinary use. It accepts `backend_name` values
  `ollama`, `openai`, `hf`, `watsonx`, and `litellm`; use `MelleaSession` plus a
  directly constructed backend when provider-specific control is needed.
- Treat an endpoint, its credentials, and a model/checkpoint as separate
  prerequisites. A successful Python import proves none of them is reachable
  or loaded.
- Prefer `ModelIdentifier` constants when the selected backend field is
  populated. Pass a plain string when a server's served model name differs
  from the catalog; do not assume `hf_model_name`, `openai_name`,
  `ollama_name`, `watsonx_name`, `bedrock_name`, and
  `bedrock_litellm_name` are interchangeable.
- Set `ModelOption.MAX_NEW_TOKENS` explicitly for production calls. Backend
  defaults differ, and options supplied to `instruct()`/`chat()` override
  backend/session defaults for that call.
- Use `DummyBackend` or mocked provider clients for deterministic unit and
  parser checks. Do not use it as evidence that a provider, checkpoint, or
  structured-output implementation works.
- Inspect `mot.generation.model`, `provider`, and `usage` when comparing
  providers; `streaming` and `ttfb_ms` describe streaming behavior.
- Do not claim CUDA model execution from an availability check. The versioned
  construction probe imported CUDA and reported it available, but a one-element
  allocation was blocked by current device memory pressure; full model
  execution remains unverified.

## Minimal safe checks

```bash
python skills/disco/mellea/sub-skills/backends-and-models/scripts/check_backends.py
python skills/disco/mellea/sub-skills/backends-and-models/scripts/check_backends.py --torch
```

The checker never starts a service, contacts a provider, downloads a model, or
allocates a model-sized tensor. Use `--probe-allocation` only when explicitly
checking a tiny CUDA allocation.

## Boundaries and handoffs

This route owns backend construction, provider/model selection, options,
multimodal payload compatibility, Granite adapter/intrinsic setup, and related
recovery. Route generative program design to the generative-programming route;
tools to tools-and-agents; evaluation/sampling to sampling-and-evaluation;
serving or `m` commands to serving-and-cli; and telemetry configuration to
observability-and-extensions. Keep credentials and service startup outside
runtime skill files.

## Acceptance checklist

Before handing off a backend-based implementation, confirm the selected extra,
credential names, service/checkpoint prerequisites, model field, supported
options, and capability limits. Exercise provider-independent logic with a
mock or `DummyBackend`; defer live calls unless the user supplies the service
and credentials. For a missing extra, unreachable endpoint, invalid credential,
unsupported option, missing checkpoint, or OOM, report the observable error and
use the recovery sequence in the troubleshooting reference rather than
silently falling back to a different provider.
