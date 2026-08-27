# Model and backend matrix

Read this before choosing a model constant or claiming a capability. A checkmark
means the package path has a documented implementation; it does not mean a
service, credential, checkpoint, or live model was available.

## Backend matrix

| Backend | Import/extra | Endpoint or load prerequisite | Images | Audio | `format=` / structured output | Adapter reality |
|---|---|---|---|---|---|---|
| `OllamaModelBackend` | Base install | Ollama service; model tag available or pullable | Yes, model-dependent; URL images are downloaded and encoded | No | Supported through Ollama request format; server/model behavior still matters | No Granite adapter functions |
| `OpenAIBackend` | Base install | OpenAI key or compatible endpoint plus non-empty client key | Yes, model-dependent | Base64 `AudioBlock` through OpenAI `input_audio`; URL audio is rejected | Yes, endpoint/schema-dependent; OpenAI platform is strict about schema shape | Granite Switch embedded adapters when configured |
| `LiteLLMBackend` | `mellea[litellm]` | Provider credentials/service or explicit proxy/local endpoint | Provider-dependent | Provider-dependent; do not generalize from OpenAI | Provider-dependent; LiteLLM may drop unsupported standard parameters and warns | No local PEFT adapter loading in this backend |
| `LocalHFBackend` | `mellea[hf]` | Transformers-compatible checkpoint/tokenizer and device memory | No; raises before generation | No; raises before generation | Yes, via `llguidance`; supports HF constrained decoding | Local LoRA/aLoRA/PEFT adapter path |
| `WatsonxAIBackend` | `mellea[watsonx]` | IBM SDK, URL, API key, and project ID | No; raises before request | No; raises before request | Provider-dependent | No runtime adapter route |
| `DummyBackend` | Base install | None | Not applicable | Not applicable | No; `format` must be `None` | No |

Bedrock has two distinct paths. The Mantle helper returns an `OpenAIBackend`
and requires a bearer token plus region/model availability. The LiteLLM helper
returns a `LiteLLMBackend` and can use standard AWS credential resolution. Both
are remote paths; neither is a local checkpoint. In this `0.8.0.dev0` snapshot,
`mellea.backends.bedrock` imports `LiteLLMBackend` at module import time, so the
Bedrock helper module requires the `litellm` extra even for the Mantle/OpenAI
helper; verify this dependency boundary when upgrading.

## ModelIdentifier field mapping

| Target | Field on `ModelIdentifier` | Example |
|---|---|---|
| Hugging Face | `hf_model_name` | `ibm-granite/granite-4.1-3b` |
| Ollama | `ollama_name` | `granite4.1:3b` |
| Native WatsonX | `watsonx_name` | `ibm/granite-4-h-small` |
| OpenAI-compatible hosted endpoint | `openai_name` | A provider-hosted compatible name, not necessarily OpenAI-hosted |
| Bedrock Mantle/OpenAI helper | `bedrock_name` | A Bedrock model ID |
| Bedrock via LiteLLM | `bedrock_litellm_name` | Usually `bedrock/converse/<model-id>` |
| HF tokenizer override | `hf_tokenizer_name` | Defaults conceptually to HF model when absent |

A field being absent is meaningful. For example, a local-only model may have
no `openai_name`; a model's HF name may be wrong for a vLLM server that exposes
a custom alias. Pass a plain string that exactly matches the selected endpoint
when a catalog field is unavailable.

## Curated examples

| Constant | Useful fields | Typical purpose |
|---|---|---|
| `IBM_GRANITE_4_1_3B` | HF + Ollama | Default text model family |
| `IBM_GRANITE_4_HYBRID_MICRO` | HF + Ollama | Small local HF/Ollama model |
| `IBM_GRANITE_VISION_4_1_4B` | HF + Ollama GGUF tag | Granite vision through Ollama; cap context explicitly |
| `IBM_GRANITE_3_3_VISION_2B` | HF + Ollama | Older Granite vision route |
| `IBM_GRANITE_SWITCH_4_1_3B_PREVIEW` | HF | Granite Switch embedded adapter model |
| `OPENAI_GPT_5_1` | OpenAI-compatible name | Hosted OpenAI-style endpoint |
| `OPENAI_GPT_OSS_120B` | HF + Ollama + Bedrock fields | Select the field matching the target provider |
| `NVIDIA_NEMOTRON_3_SUPER_120B_A12B` | HF + Ollama + OpenAI + Bedrock | Hosted NVIDIA/OpenAI-compatible or Bedrock route with matching endpoint |
| `NVIDIA_NEMOTRON_NANO_12B_V2` | HF only | Local inference; do not pass the identifier to `OpenAIBackend` |

The catalog is larger than this table. Inspect `mellea.backends.model_ids` in
the installed package or use `ModelIdentifier` fields rather than copying a
name from a different provider.

## Capability detection strategy

There is no universal promise that a provider model supports every feature.
Detect capability in layers:

1. Use the matrix and model documentation to choose a plausible route.
2. Inspect the model identifier field and selected backend class.
3. Validate the payload locally (for example, `ImageBlock`, `AudioBlock`, and
   Pydantic schema construction).
4. Run a mocked provider test for serialization and option mapping.
5. Only then exercise the service/checkpoint with credentials and a small
   request.

For `ModelOption.LOGITS` and `RAW_LOGITS`, capability is backend-specific: the
HF backend can populate the per-token tensors, while OpenAI, Ollama, LiteLLM,
and WatsonX warn and leave those fields `None`. Streaming also leaves logits
unavailable.

For adapter capabilities, query `known_intrinsic_names()` or
`fetch_intrinsic_metadata()` rather than inventing a task name. The registry is
advisory and custom capabilities may emit a warning rather than being rejected.
