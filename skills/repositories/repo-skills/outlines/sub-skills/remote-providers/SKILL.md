---
name: remote-providers
description: "Operate Outlines server and black-box provider integrations
  without invoking live models."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# remote-providers

Use this sub-skill when the task involves Outlines model loaders for
server-based or black-box clients: OpenAI/Azure OpenAI, Anthropic, Gemini,
Mistral, Ollama, LM Studio, SGLang, TGI, vLLM server mode, or Dottxt.

This skill is for configuration, routing, capability checks, and error recovery.
Do **not** call provider services, do not validate real credentials, and do not
print secret values.

## Read First

- [Provider matrix](references/provider-matrix.md) for loader signatures,
  supported modes, output types, credentials/endpoints, and exclusions.
- [API reference](references/api-reference.md) for safe loader patterns,
  output-type compatibility, and normalized exceptions.
- [Workflows](references/workflows.md) for provider selection, async/stream
  routing, no-network prerequisite checks, and retry/backoff decisions.
- [Troubleshooting](references/troubleshooting.md) for install/import, auth,
  rate limits, unsupported structured outputs, endpoint mismatches, refusals,
  and mock-vs-live verification.
- [scripts/check_provider_prereqs.py](scripts/check_provider_prereqs.py) for a
  read-only import/env/endpoint probe that never calls a model service.

## Use This When

- Choosing the correct `from_*` loader for a provider client object.
- Deciding whether a task can use sync, async, streaming, or batch calls.
- Checking whether an `output_type` can run on a black-box provider.
- Diagnosing provider SDK import errors, missing API-key variables, endpoint
  configuration, or normalized `outlines.exceptions` errors.
- Handling OpenAI-compatible servers while preserving SGLang/TGI/vLLM-specific
  structured-output behavior.

## Route Elsewhere

- Output-type design, schema shaping, regex/CFG conversion, or local constrained
  decoding strategy -> `../structured-generation/SKILL.md`.
- Prompt, chat, multimodal input construction, reusable generators, or call
  orchestration -> `../prompt-workflows/SKILL.md`.
- Local/offline engines (`Transformers`, `LlamaCpp`, `MLXLM`, `VLLMOffline`) ->
  the local model/runtime route, not this server-provider route.

## Operating Rules

1. **Select the loader from the actual client class.** `from_openai`,
   `from_sglang`, and `from_vllm` all accept OpenAI SDK clients, but they build
   different request bodies for structured output. Do not treat them as
   interchangeable.
2. **Reject unsupported output types before retrying.** For example, an OpenAI
   `Regex` or `CFG` request is a capability mismatch; route to a local/supported
   provider instead of retrying the same OpenAI request.
3. **Batch is unavailable for all providers in this skill.** Server wrappers here
   raise `NotImplementedError` for `batch`; use caller-side bounded concurrency
   only when the provider wrapper has an async model and the provider limits
   permit it.
4. **Retry only normalized transient errors.** `RateLimitError`, `ServerError`,
   `APITimeoutError`, and `APIConnectionError` expose `retryable=True`.
   Authentication, permission, not-found, malformed request/schema, and refusal
   errors require configuration or request changes.
5. **Preserve request IDs and providers.** When catching `APIError`, surface
   `provider`, `status_code`, `request_id`, `retryable`, and `hint` without
   exposing secrets.
6. **No credentials or live probes.** Use placeholders in examples and the
   bundled prerequisite script for import/env checks only.

## Fast Capability Snapshot

| Provider route | Loader | Async | Stream | Batch | Structured-output support |
|---|---|---:|---:|---:|---|
| OpenAI / Azure | `from_openai(client, model_name=None)` | yes | yes | no | JSON schema strict + JSON mode; no Regex/CFG/simple choice |
| Anthropic | `from_anthropic(client, model_name=None)` | no | yes | no | none through Outlines `output_type` |
| Gemini | `from_gemini(client, model_name=None)` | no | yes | no | JSON schema subset, homogeneous lists, enum/choice; no Regex/CFG |
| Mistral | `from_mistral(client, model_name=None, async_client=False)` | opt-in | yes | no | strict JSON schema + JSON mode; no Regex/CFG |
| Ollama | `from_ollama(client, model_name=None)` | yes | yes | no | JSON schema only; no Regex/CFG |
| LM Studio | `from_lmstudio(client, model_name=None)` | yes | yes | no | JSON schema only; local SDK errors are not normalized |
| SGLang | `from_sglang(client, model_name=None)` | yes | yes | no | JSON/schema/regex/simple/choice; CFG only as SGLang-compatible EBNF |
| TGI | `from_tgi(client)` | yes | yes | no | JSON/schema/regex/simple/choice; no CFG |
| vLLM server | `from_vllm(client, model_name=None)` | yes | yes | no | JSON/schema/regex/simple/choice/CFG if server supports structured outputs |
| Dottxt | `from_dottxt(client, model=None)` | yes | no | no | JSON schema only; output type and model id required |

Keep provider-specific caveats in [provider-matrix.md](references/provider-matrix.md)
in front of any implementation or recovery plan.
