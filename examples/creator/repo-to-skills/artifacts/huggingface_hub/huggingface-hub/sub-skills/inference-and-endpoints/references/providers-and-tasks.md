# Providers, Routing, And Task Families

The provider registry was inspected from the 1.29.0 provider source and live
Python objects. Availability is a server/model mapping fact and can change;
use this table as an implemented-helper route map, not a promise that a
particular model is live. The English guide's rendered provider matrix can lag
new helper additions (for example, newer DeepInfra and Together task helpers),
so reconcile intent from the guide with the checked-out registry and tests.

## Provider task map

The public task method names map to provider helper tasks as follows:

| Provider value | Implemented helper task families in this checkout |
|---|---|
| `baseten` | conversational/chat |
| `cerebras` | conversational/chat |
| `cohere` | conversational/chat |
| `deepinfra` | automatic speech recognition, conversational/chat, feature extraction, text generation, text to speech |
| `fal-ai` | automatic speech recognition, text to image, text to speech, text to video, image to video, image to image, image segmentation |
| `featherless-ai` | conversational/chat, text generation |
| `fireworks-ai` | conversational/chat |
| `groq` | conversational/chat |
| `hf-inference` | text to image, conversational/chat, text generation, classification, QA, audio/ASR, fill-mask, embeddings, vision, audio-to-audio, zero-shot, image-to-image, similarity, tabular, speech, token classification, translation, summarization, VQA |
| `novita` | text generation, conversational/chat, text to video |
| `nscale` | conversational/chat, text to image |
| `openai` | conversational/chat (direct provider key; not HF-routed) |
| `ovhcloud` | conversational/chat |
| `publicai` | conversational/chat |
| `replicate` | ASR, image to image, text to image, text to speech, text to video |
| `scaleway` | conversational/chat, feature extraction |
| `together` | conversational/chat, feature extraction, image to image/video, text generation, text to image/speech/video |
| `wavespeed` | text to image/video, image to image/video |
| `zai-org` | conversational/chat, text to image |

Task support in the registry is only one gate. The model's inference-provider
mapping must include the selected provider with a compatible task. For a
provider-specific call, the helper raises a `ValueError` if no mapping exists
or if the mapping task differs. With a Hub model ID, non-chat `auto` routing
fetches the model's provider mapping and selects the first mapped provider in
the user's ordering; chat uses the HF server-side auto-router. With no model,
`provider=None` **or** `provider="auto"` is normalized to `hf-inference` so the
task may use its current recommended model. Third-party providers still require
an explicit compatible Hub model ID.

A URL model is handled by the `hf-inference` URL path and should not be combined
with a provider selection. For chat, a URL passed by either constructor alias is
normalized to the chat-completions route. For reliable automation, use an
explicit model, provider mode, and token mode.

## Choosing authentication and billing

| Key passed | Transport behavior | Billing owner |
|---|---|---|
| `token="hf_..."` or saved HF token | HF router/provider route | HF account; optional eligible `bill_to` organization |
| provider key such as `"<PROVIDER_KEY>"` | Direct provider URL where supported | Provider account |
| `api_key=...` | Alias for `token`, useful for OpenAI-shaped code | Determined by key type |
| `bill_to="<ORG>"` | Adds HF billing header | Only an organization the user belongs to with required subscription |

Never infer that a provider API key can use HF routing. The provider helper
checks key shape and may reject an unsupported routed/direct combination. Do
not print keys to identify which route was selected; use debug logging with
redaction or inspect only the non-secret prepared URL in a mock.

## Provider caveats

- Chat, tool calling, JSON mode, structured output, multimodal content,
  streaming, and sampling parameters are not portable across all providers.
  Verify the provider's model page/API contract before enabling them.
- `extra_body` is an escape hatch for provider-specific payload fields. Keep it
  small and provider-scoped; do not pass arbitrary user input into it.
- `openai` is a direct OpenAI provider helper and requires an OpenAI-style key;
  do not expect an HF token to route it through HF.
- Async behavior uses the same provider helpers and payload semantics, but
  HTTP session and stream cleanup are different; see [workflows](workflows.md).
- `fal-ai`, `replicate`, `wavespeed`, and similar media providers may use
  queued requests internally. Their helper can poll or fetch result URLs; a
  timeout can occur after a request has already been accepted.
- `hf-inference` supports more task families than third-party entries and can
  use recommended models, but recommended models can change. Explicit model
  IDs are safer for reproducible runs.
- Feature extraction may be served by TEI or an OpenAI-compatible embeddings
  endpoint. `normalize`, `truncate`, `dimensions`, and `encoding_format` are
  not interchangeable options.
- A model may be listed as staging or have an unhealthy mapping. Treat the
  warning as a signal to choose another mapping, not as a reason to retry
  indefinitely.

## Task-family routing

| User intent | Start here | Reference |
|---|---|---|
| Completion from a single prompt | `text_generation` | [task types](task-types.md) |
| Conversational or OpenAI-shaped response | `chat_completion` or `chat.completions.create` | [API reference](api-reference.md) |
| Vector embeddings | `feature_extraction` | [task types](task-types.md) |
| Image generation | `text_to_image` | [task types](task-types.md) |
| Audio/vision/media prediction | The corresponding binary task method | [task types](task-types.md) |
| Classification, QA, summarization, translation, tabular | The task-specific method on `InferenceClient` | [task types](task-types.md) |
| Dedicated production model | Endpoint API, then URL client | [workflows](workflows.md) |

Use `references/task-types.md` for practical input/output shapes and generated
schema classes. Do not import provider internals merely to discover a task;
use public methods and inspect signatures.
