# Nesa Runtime Overview

Nesa demonstrates **Equivariant Encryption (EE)** for AI inference. The public
repo combines conceptual documentation, a small local sentiment-classification
demo, a modified text-generation web UI, backend request helpers, and contest
material for stress-testing encrypted token mappings.

## What EE means in this repo

The repo presents EE as a transformation of token IDs and model behavior that
preserves model computation while hiding plaintext from the server:

1. The client owns plaintext text and the tokenizer/encryption key.
2. The client encodes text into encrypted token IDs.
3. The server or remote model sees only encrypted tokens.
4. The model returns encrypted outputs or logits.
5. The client decodes/decrypts the result locally.

The repo claims the encrypted inference path should have minimal or no latency
overhead for the demonstrated model families. Do not turn that into a general
performance guarantee unless you run an appropriate benchmark in the user's
actual environment.

## Main workflow surfaces

| Surface | Use it for | Skill route |
|---|---|---|
| Minimal local sentiment demo | Small CPU-friendly walkthrough of encrypted token IDs and DistilBERT sentiment scores | `sub-skills/encrypted-distilbert/` |
| Web UI runtime | Local browser UI, model selection, one-click installer decisions, model download/checksum helpers, CPU/GPU flags | `sub-skills/web-ui-runtime/` |
| Backend protocol | `msgspec` request/response structs, model registry, prompt-template construction, SSE streaming request shape, settings | `sub-skills/backend-protocol/` |
| Hack EE contest/security | Token-mapping JSON submissions, scoring, daily/grand-prize rules, baseline attack heuristics | `sub-skills/security-contest/` |

## Models and modes

The repo evidence covers two practical model paths:

- **Encrypted DistilBERT sentiment classification:** local model/tokenizer files
  are enough for the small demo. The user can also use an equivalent public
  Hugging Face model ID when network access is allowed.
- **Encrypted Llama chat/generation:** the tokenizer is local/client-side, while
  model inference is described as going through Nesa's remote service. Treat this
  as network/service-dependent unless the user provides a local replacement.

## Web UI architecture at a glance

The web UI is based on text-generation-webui with Nesa-specific integration:

- startup scripts create a contained environment and run a one-click installer;
- command flags default to CPU mode in the checked evidence;
- settings define `mode: equivariant-encrypt` and an
  `equivariant-encrypt_command` prompt wrapper;
- the model menu dispatches selected model names through a Nesa model registry;
- local DistilBERT uses a Hugging Face model handler;
- remote encrypted Llama builds a prompt, tokenizes it locally, and streams a
  response from the configured Nesa endpoint.

## Backend protocol architecture

The backend layer uses these concepts:

- `Message`: content plus role.
- `Role`: assistant, user, ai, system.
- `LLMParams`: sampling parameters with validation for temperature, penalties,
  top-p/top-k, max/min token counts, and greedy sampling.
- `SessionID`: includes an `ee` boolean to mark Equivariant Encryption sessions.
- `LLMInference`: stream flag, correlation id, model, messages, model params,
  and session id.
- `InferenceResponse`: streaming response chunks with choices and delta content.
- `ModelRegistry`: chooses a handler by model-specific key before task type.

Read the backend-protocol sub-skill before modifying request payloads or adding
new model handlers.

## Capability boundaries

This skill can help a future agent:

- choose the right Nesa workflow route;
- install a minimal local environment or diagnose missing dependencies;
- run a small local encrypted sentiment example;
- preview request payloads without contacting Nesa's service;
- validate web UI settings and model-download naming; and
- explain the contest mapping/scoring/attack baseline material.

This skill does not provide:

- a proof that EE is secure or insecure;
- Nesa service credentials or guaranteed stream endpoint availability;
- bundled model weights or tokenizers;
- a one-click installer that mutates the user's machine; or
- generic Transformers/web UI expertise outside Nesa-specific behavior.
