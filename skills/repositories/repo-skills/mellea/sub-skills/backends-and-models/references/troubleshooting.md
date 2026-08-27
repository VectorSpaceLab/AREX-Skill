# Backend troubleshooting and recovery

Classify the failure before changing code: import/extra, credential, service,
model/checkpoint, payload/option, or device memory. Preserve the original error
and do not silently switch providers.

## Import and optional dependency failures

**Symptom:** `ImportError` says the backend requires extra dependencies, or a
module such as `litellm`, `ibm_watsonx_ai`, `transformers`, `torch`, or
`llguidance` is absent.

**Recovery:** install only the matching extra (`mellea[hf]`,
`mellea[litellm]`, or `mellea[watsonx]`), then rerun the safe checker. Add
`mellea[cli]`, `[tools]`, `[telemetry]`, or `[server]` only for those features.
If the dependency cannot be installed, route to a base-install backend or a
mock; do not claim the unavailable route is verified.

**Symptom:** a package import succeeds but generation fails at model load.

**Recovery:** distinguish importability from checkpoint access and device
capacity. For HF, verify the model ID, tokenizer compatibility, local cache or
Hub access, and `mellea[hf]`; a package probe is not a checkpoint probe.

## Ollama service and model failures

**Symptom:** `ConnectionError` says the Ollama server is not running, commonly
around port `11434`.

**Recovery:** start the separately installed service, confirm its host/port, or
set `OLLAMA_HOST`/`base_url`. Use a mocked Ollama client for unit tests. Avoid
constructing `OllamaModelBackend` in a no-network parser check because its
constructor checks the service and may pull a model.

**Symptom:** model pull failure or model-not-found response.

**Recovery:** compare the exact tag with `ollama list`; pull it explicitly or
choose a `ModelIdentifier` that has an `ollama_name`. A model constant without
that field must be passed as a plain Ollama tag. Check RAM/VRAM and context
window before moving to a larger model.

**Symptom:** slow or stuck local generation.

**Recovery:** retain the backend's 300-second HTTP timeout unless the deployment
needs another value; separately tune `ModelOption.STREAM_TIMEOUT` for streaming
first-token/chunk waits. Set `MAX_NEW_TOKENS` and, for Granite vision 4.1,
cap `CONTEXT_WINDOW` rather than allocating the full context window.

## OpenAI-compatible endpoint failures

**Symptom:** `OPENAI_API_KEY or api_key is required`.

**Recovery:** export `OPENAI_API_KEY` or pass a non-empty `api_key`. A local
server may ignore the key, but the OpenAI SDK still expects a value.

**Symptom:** connection refused or 404 at a custom `base_url`.

**Recovery:** verify the service is running, the URL includes the provider's
expected `/v1` path where applicable, and `model_id` exactly matches the served
name. `base_url`/`api_key` constructor arguments take precedence over
`OPENAI_BASE_URL`/`OPENAI_API_KEY`. Do not treat an endpoint that accepts
`/v1` as proof it supports every OpenAI feature.

**Symptom:** a `ModelIdentifier` raises because `openai_name` is absent, or a
hosted model returns 404.

**Recovery:** use an identifier with the correct provider field, or pass the
server's exact plain-string name. Hosted catalog names such as NVIDIA NIM names
require their matching base URL; self-hosted vLLM normally uses its served/HF
name.

**Symptom:** structured output or a request option is rejected by a compatible
server.

**Recovery:** reproduce serialization with a mocked client, inspect the outgoing
`response_format`/`extra_body`, and remove or translate the unsupported option.
Use `format=MyPydanticModel` only when the endpoint supports the emitted schema.
Do not invent flags or assume OpenAI and vLLM have identical schema rules.

**Symptom:** final `.value` is empty but usage is non-zero.

**Recovery:** inspect `.thinking`, raw provider metadata, and the server's
reasoning configuration. A thinking model can emit reasoning with no final
content. Use `default_extra_body` for a persistent documented thinking switch;
remember per-call `extra_body` is an override and nested chat-template values
are merged.

## LiteLLM, Bedrock, Vertex, and WatsonX failures

**Symptom:** LiteLLM import failure or provider authentication error.

**Recovery:** install `[litellm]`, use the provider prefix required by the model
string, and set that provider's credentials. Leave `base_url` unset for direct
cloud mode; set it only for a local/proxy endpoint. LiteLLM may warn that a
standard option is unsupported and drop it; remove it or use a provider-native
field after checking the provider contract.

**Symptom:** importing `mellea.backends.bedrock` fails with the LiteLLM
optional-dependency message, even though the intended route is Mantle/OpenAI.

**Recovery:** install `mellea[litellm]` for this package snapshot. The module
imports `LiteLLMBackend` at import time; this is distinct from the later choice
of Mantle/OpenAI versus LiteLLM execution. Recheck the boundary after package
upgrades rather than inventing a separate Bedrock extra.

**Symptom:** Bedrock helper reports missing bearer token, missing AWS
credentials, missing region, or a model not supported in the region.

**Recovery:** for Mantle/OpenAI, set `AWS_BEARER_TOKEN_BEDROCK` and use a region
where the model is enabled. For LiteLLM Bedrock, use the standard AWS
credential chain or bearer token and ensure a region is resolvable from
`AWS_REGION_NAME`, `AWS_DEFAULT_REGION`, or `AWS_REGION`. Use a raw Bedrock
model string only when its format matches the helper. Listing regional models
is a network operation; mock `list_mantle_models` in tests.

**Symptom:** Vertex authentication, project, location, or SDK import error.

**Recovery:** install the LiteLLM extra plus the required Google provider
package, set `VERTEXAI_PROJECT` and `VERTEXAI_LOCATION`, and authenticate with
application-default credentials or an approved service-account mechanism. Do
not place service-account JSON in source control.

**Symptom:** native WatsonX reports missing URL/key/project or behaves
inconsistently across event loops.

**Recovery:** install `[watsonx]`, set `WATSONX_URL`, `WATSONX_API_KEY`, and
`WATSONX_PROJECT_ID`, and keep async calls on one event loop. Prefer LiteLLM's
`watsonx/` path for new code, noting that LiteLLM uses `WATSONX_APIKEY`.

## Multimodal and adapter failures

**Symptom:** `WatsonxAIBackend`, `LocalHFBackend`, or Ollama rejects image/audio
blocks; OpenAI rejects `AudioUrlBlock`.

**Recovery:** use a model/backend with the needed modality. Convert a trusted
PIL image to `ImageBlock`; convert audio URLs to validated base64 `AudioBlock`
with `wav` or `mp3` as required by OpenAI. Do not silently drop content. For
HF, remove multimodal blocks or route the call to a compatible remote/local
vision backend.

**Symptom:** adapter function import, Hub access, missing checkpoint, or I/O
schema failure.

**Recovery:** install `[hf]`, verify the base model/checkpoint and network/HF
permissions, and use a catalog name from `known_intrinsic_names()`. For local
LoRA/aLoRA, confirm base-model compatibility and adapter I/O configuration. For
Granite Switch, verify the served model has the requested capability in
`adapter_index.json`, set `load_embedded_adapters=True`, and use the matching
formatter. If the adapter cannot load, a safe LLM-as-judge fallback may occur;
if it loads but its output violates the schema, fix the contract rather than
expecting fallback.

**Symptom:** adapter request loses either `enable_thinking` or `adapter_name`.

**Recovery:** place persistent thinking controls in `OpenAIBackend`'s
`default_extra_body`; let per-call/intrinsic `extra_body` add fields. Avoid the
older construction-time per-call pattern that can be overwritten.

## CUDA, CPU, MPS, and OOM

**Symptom:** CUDA is reported available but model construction or even a tiny
allocation fails with out-of-memory.

**Recovery:** treat this as a device-pressure failure, not proof of successful
GPU execution. Free other allocations/processes, lower model size/precision or
context, disable/limit caches, or choose CPU/MPS only after checking the
model's actual requirements. A CPU import or `torch.cuda.is_available()` check
cannot validate full HF generation. The current package inspection recorded
CUDA import and availability success but a one-element allocation blocked by
memory pressure; full model execution was intentionally not claimed.

**Symptom:** CPU fallback is unexpectedly slow or a model cannot fit.

**Recovery:** choose a smaller checkpoint, set explicit output/context limits,
use a provider-backed model when appropriate, or stop and request hardware.
Do not call a partial CPU substitution a validation of CUDA-only adapter or
full-checkpoint workflows.

## Deterministic testing

Use `DummyBackend(responses=[...])` for ordered, deterministic response tests;
exhausting the list is an intentional error. It does not support `format=`.
Mock provider clients at the SDK boundary and assert serialized payloads,
option mappings, metadata, and early capability errors. Native candidates in
this scope include unit/mocked OpenAI, Ollama, HF, WatsonX, Bedrock, adapter,
formatter, and helper tests; live provider and checkpoint cases remain deferred.
