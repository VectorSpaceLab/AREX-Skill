---
name: inference-and-endpoints
description: "Run hosted model inference and manage Hugging Face Inference Endpoints with sync or async clients, provider-aware payloads, streaming, tools, structured outputs, MCP, and safe lifecycle recovery."
license: Apache-2.0
disable-model-invocation: true
metadata:
  disco-role: operating
---

# Inference And Endpoints

Use this route for hosted inference through `InferenceClient` or
`AsyncInferenceClient`, a provider/token/base URL decision, task payloads or
binary media, OpenAI-compatible chat, streaming, tools or structured JSON,
MCP client/agent workflows, or the deployment and lifecycle of an Inference
Endpoint. This skill targets `huggingface_hub` 1.29.0 evidence.

## Route Before Calling

| Request | Route |
|---|---|
| Serverless Hub/provider prediction | `InferenceClient` or `AsyncInferenceClient`; read [providers and tasks](references/providers-and-tasks.md). |
| Dedicated HF-managed deployment | `HfApi`/root endpoint helpers and `InferenceEndpoint`; read [workflows](references/workflows.md). |
| Chat with an OpenAI-shaped API | `client.chat.completions.create`, an alias of `chat_completion`. |
| Tools, function calls, JSON mode, or schema output | Chat route plus [task types](references/task-types.md) and provider caveats. |
| MCP servers or a tiny tool-using agent | Install the optional `mcp` extra, then read [workflows](references/workflows.md). |
| Local vLLM/TGI/Ollama/LiteLLM server | Use `model`/`base_url` as an OpenAI-compatible URL; this route does not install or run the server. |
| Hub repositories, downloads, jobs, Spaces, or CLI output in general | Use the sibling sub-skill rather than this route. |

Do not confuse `InferenceClient` (an HTTP prediction client for the HF router,
providers, deployed URLs, or compatible servers) with `InferenceEndpoints` API
methods (deployment configuration and lifecycle). An Inference Endpoint can
later be used as the client's URL.

## Safe Setup And Identity

- Base hosted inference needs the package and its HTTP dependencies; it does
  **not** require a local GPU, CUDA, `torch`, or model download. Install only
  what the requested surface needs: `pip install "huggingface_hub"`,
  `pip install Pillow` to decode image outputs, `pip install numpy` for
  embedding arrays, or `pip install "huggingface_hub[mcp]"` before connecting
  to MCP servers. There is no runtime `inference` extra; the repository's
  `testing` extra is for maintainers, not application setup.
- Keep credentials out of prompts, request bodies, logs, notebooks, and
  examples. Prefer a secret manager or `HF_TOKEN`/an existing `hf auth login`;
  pass a placeholder in documentation. A Hugging Face `hf_...` key uses HF
  routing/billing; a provider key uses direct provider access. `bill_to` only
  applies to an eligible HF organization and is ignored for external keys.
- Resolve model identity before the request: a Hub model ID must support the
  selected task, and a third-party provider route also needs a compatible
  provider mapping; a deployed/local URL is a direct target. With a model ID,
  `provider="auto"` selects from mapped providers (chat uses the server-side
  auto-router). With no model, `None` or `"auto"` falls back to the recommended
  `hf-inference` model for that task. A URL is direct and should not be paired
  with a provider. Pin `model` explicitly for repeatability.
- `model` and `base_url` are constructor aliases and mutually exclusive, as are
  `token` and `api_key`. For chat, a URL supplied by either constructor name is
  normalized to a `/v1/chat/completions` route unless it already ends in
  `/chat/completions`; other tasks use the URL unchanged. The implementation
  stores either constructor spelling identically; `base_url` is the
  OpenAI-compatible name. With a constructor URL and a call-time `model=`, the
  URL remains the transport target and the call-time value becomes the JSON
  payload model.
- Set `timeout` when a bounded request is required. `None` means no client-side
  request deadline. Use one client per configured identity and close it,
  especially the async client and any partially consumed stream.

Read [API reference](references/api-reference.md) for inspected signatures,
return types, endpoint classes, and sync/async parity before coding.

## Task And Output Workflow

1. Select a task family and a model/provider combination from [providers and
   tasks](references/providers-and-tasks.md); do not assume every provider
   supports every task.
2. Construct the task-specific input. Text tasks take strings or batches;
   vision/audio tasks accept bytes, binary file objects, `Path`, URL, or PIL
   input where supported. A string is a URL or path, not raw binary content.
3. Call the typed method. Representative contracts are `text_generation`
   (string, detailed output, or iterable), `chat_completion` (output object or
   stream), `feature_extraction` (`numpy.ndarray`), and `text_to_image`
   (`PIL.Image`). [Task types](references/task-types.md) covers generated
   dataclasses and payload shapes without making the router a catalog.
4. For `stream=True`, consume synchronously with `for` or asynchronously with
   `async for` over the awaited async result. Chat deltas may contain content,
   reasoning, tool-call fragments, finish reasons, or a usage-only final chunk;
   do not assume every chunk has content.
5. Record model, provider mode, task, non-secret request ID/status, output
   shape, and typed exception. Never record authorization headers or raw
   private media.

`text_generation` is for a prompt. Use chat for message history so the client
and server apply the model's chat format. `details=True` and detailed stream
objects are backend-dependent, especially for TGI. Provider-specific options
belong in `extra_body` only after checking that provider's contract.

## Chat, Tools, And Structured Output

Use OpenAI-shaped `messages` with valid roles and content. Function tools are
schemas, not executable Python: validate names and JSON arguments yourself,
apply least privilege, and only execute an approved function after checking
its arguments. `tool_choice` may be `"auto"`, `"none"`, `"required"`, or a
provider-supported named function object. Provider/model support is not
uniform; see [providers and tasks](references/providers-and-tasks.md).

Use `response_format={"type": "json_object"}` for valid JSON where supported,
or `{"type": "json_schema", "json_schema": {"name": ..., "schema": ...,
"strict": True}}` for schema-constrained output. Keep the schema finite,
valid JSON Schema, and aligned with the prompt. Parse and validate the returned
message content; a response-format request is not a substitute for validation.
For HF Inference, the implementation translates JSON schema to its supported
grammar form, so check the provider before relying on strict behavior.

OpenAI migration requires replacing the import/client and selecting a valid
HF model/provider or compatible URL; it is not a promise that every OpenAI
parameter or provider feature is portable. `client.chat.completions.create` is
an alias, not a separate transport.

## Async And MCP

`AsyncInferenceClient` has the same representative input signatures and
returns awaitables or `AsyncIterable` streams. Run it inside an asyncio
context, `await` ordinary calls and the stream-producing call, then cancel or
close the consumer on early termination. Do not use synchronous iteration on an
async stream.

MCP is experimental and optional. Importing the public class can succeed
without the optional dependency because the MCP package is loaded when a
server connection is opened; install the `mcp` extra before using that path.
`MCPClient` can attach `stdio`, `sse`, or streamable `http` servers, discover
allowed tools, stream a turn, and execute a tool only through the session that
registered its name. `Agent` wraps a bounded MCP loop. Use placeholder
URLs/commands, an explicit narrow `allowed_tools` list (empty to expose none),
isolated working directories, and explicit headers; never put real credentials
in a sample or allow an untrusted stdio command. Use an async context manager
and call `cleanup` on manual paths.

## Endpoint Lifecycle

Use `list_inference_endpoints_hardware` first to resolve valid vendor, region,
accelerator, instance type/size and quota. Then create with
`create_inference_endpoint` (or the experimental catalog helper), inspect the
returned `InferenceEndpoint`, and wait for a healthy `running` state before
accessing `.client`/`.async_client`. `wait(timeout=..., refresh_every=...)`
mutates the object and raises typed endpoint errors on failure or timeout.

The object aliases `fetch`, `update`, `pause`, `resume`, `scale_to_zero`, and
`delete` to HfApi operations; root helpers are also available. Paused endpoints
need explicit resume; scaled-to-zero endpoints restart on request with cold
start. Delete is irreversible. Treat `secrets` and custom image credentials
as write-only. For engine images, parallelism belongs in the image config;
`container_args` are engine flags and are not equivalent. See [workflows](references/workflows.md).

## Diagnose And Verify

Start with the exact signature and selected task/provider, then inspect the
prepared request only with a mock transport. A missing token/provider mapping,
unsupported task/provider, malformed messages/tools/schema, binary MIME/path,
stream event, timeout/rate-limit, billing, endpoint state, or custom-image
error should be diagnosed using [troubleshooting](references/troubleshooting.md).
Use typed errors and bounded recovery; do not blindly retry non-idempotent
endpoint mutations or repeat paid inference.

No live inference, model download, deployment, or endpoint deletion is part of
this skill verification. Run the safe synthetic transport case instead:

```bash
PYTHONPATH=src python skills/huggingface-hub/sub-skills/inference-and-endpoints/scripts/mock_chat_recovery.py
# In an installed-package project, omit `PYTHONPATH=src`.
```

The script asserts no real network or token use while exercising chat tools and
JSON schema, async stream cancellation, and an explicit provider fallback.
Native VCR/production tests cover individual payloads and recorded services,
not this full cross-provider recovery/cancellation composition; its limitation
is documented in the script and [workflows](references/workflows.md).

## Progressive Disclosure

- [api-reference.md](references/api-reference.md) — verified constructors,
  representative task signatures, output types, endpoint APIs, and aliases.
- [workflows.md](references/workflows.md) — safe mocked client flows, async
  streaming/cancellation, MCP setup, endpoint planning, and `hf endpoints
  --help` discovery.
- [providers-and-tasks.md](references/providers-and-tasks.md) — provider/task
  matrix, routing semantics, billing and capability caveats.
- [task-types.md](references/task-types.md) — generated type system and
  practical text/chat/binary/embedding payload shapes.
- [troubleshooting.md](references/troubleshooting.md) — typed failure diagnosis
  and narrow recovery for all supported surfaces.
- [development.md](references/development.md) — maintainer-only generated-file
  policy; never ask runtime users to invoke source generators.
