---
name: backend-protocol
description: "Inspect and use Nesa backend protocol structs, model registry
  handlers, prompt construction, and safe encrypted LLM request previews."
metadata:
  disco-role: operating
disable-model-invocation: true
license: NO_LICENSE
---

# Backend Protocol

Use this sub-skill when the user asks how Nesa builds encrypted LLM requests,
validates sampling parameters, selects model handlers, sanitizes tokens, or
streams responses from the remote service.

Typical triggers:

- "what fields are in `LLMInference`?"
- "why does `LLMParams` reject my sampling args?"
- "how is the Nesa model registry keyed?"
- "preview the encrypted Llama request without calling the endpoint"
- "debug remote stream response parsing"

## Safe workflow

1. Read [references/api-reference.md](references/api-reference.md) for structs,
   defaults, validation, and handlers.
2. Use [scripts/inspect_protocol_defaults.py](scripts/inspect_protocol_defaults.py)
   to confirm local package behavior in the current environment.
3. Build request previews with
   [scripts/build_llm_request_preview.py](scripts/build_llm_request_preview.py)
   before contacting any remote service.
4. Contact the stream endpoint only after the user approves a network/service
   call and provides required model/tokenizer context.
5. If a field or registry key fails, read
   [references/troubleshooting.md](references/troubleshooting.md).

## Core protocol facts

- Messages are role/content pairs.
- Roles include assistant, user, ai, and system.
- `LLMParams` validates sampling ranges and normalizes `stop_token_ids`.
- Low/zero temperature forces greedy sampling behavior and constrains related
  parameters.
- `SessionID` includes an `ee` boolean to mark encrypted sessions.
- `LLMInference` contains stream flag, correlation id, messages, model id,
  optional model params, and optional session.
- Response chunks carry choices and delta content; delta content may be a string
  or an integer token.
- The remote encrypted LLM path tokenizes locally and sends token IDs as message
  content to the configured stream endpoint.

## Model registry facts

The registry checks model-specific keys first, then task-type keys. Source
evidence includes handlers for encrypted DistilBERT local classification and an
encrypted Llama remote streaming path. If a user provides a model name with `/`,
check whether the web UI normalizes it to an underscore form before registry
lookup.

## References and scripts

- [references/api-reference.md](references/api-reference.md): structs, methods,
  signatures, defaults, and validation behavior.
- [references/request-flow.md](references/request-flow.md): local tokenizer,
  prompt-template, request preview, and SSE streaming flow.
- [references/troubleshooting.md](references/troubleshooting.md): parameter,
  registry, dependency, endpoint, and response parsing failures.
- [scripts/inspect_protocol_defaults.py](scripts/inspect_protocol_defaults.py):
  safe import/default/validation check.
- [scripts/build_llm_request_preview.py](scripts/build_llm_request_preview.py):
  self-contained JSON payload preview with no network call.

## Boundaries

- Do not use this sub-skill for one-click installation or UI launch; route to
  `web-ui-runtime`.
- Do not use this sub-skill for local sentiment output interpretation; route to
  `encrypted-distilbert`.
- Do not treat request previews as proof the Nesa remote stream endpoint is
  reachable.
