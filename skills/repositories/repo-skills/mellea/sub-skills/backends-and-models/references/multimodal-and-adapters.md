# Multimodal inputs, Granite formatters, and adapters

Read this for vision, audio, structured output, Granite intrinsic functions,
LoRA/aLoRA, or Granite Switch. Capability support is model- and backend-
dependent; never infer it from the presence of an `images` or `audio` argument.

## Image and audio blocks

`MelleaSession.instruct()` and `.chat()` accept `images=` and `audio=`. Images
can be PIL images, `ImageBlock` (base64 PNG), or `ImageUrlBlock` (HTTP(S) URL).
Audio uses `AudioBlock` (base64 plus an explicit or data-URI-derived format) or
`AudioUrlBlock`.

```python
from PIL import Image
from mellea import MelleaSession
from mellea.backends.openai import OpenAIBackend
from mellea.core import ImageBlock

session = MelleaSession(
    OpenAIBackend(
        model_id="vision-model-as-served",
        base_url="http://127.0.0.1:8000/v1",
        api_key="local",
    )
)
image = ImageBlock.from_pil_image(Image.open("photo.png"))
result = session.instruct("Describe this image.", images=[image])
```

OpenAI-compatible serialization makes image content parts. `AudioBlock` becomes
an `input_audio` part with raw base64 data and `format`; `AudioUrlBlock` is
rejected because OpenAI Chat Completions does not accept audio URLs. Ollama
accepts images but converts URL blocks to base64 and rejects audio. WatsonX and
LocalHFBackend reject both images and audio before the request. LiteLLM passes
through to the underlying provider, so confirm that provider's multimodal
schema. A text-only model may still reject an otherwise valid image payload.

When using a `ChatContext`, multimodal blocks remain in conversation history.
Pass `images=[]` explicitly to remove images on the next turn. Do not send a
remote URL to a backend that cannot fetch it; convert it to an `ImageBlock` only
when the source is trusted and the download is allowed.

The `ImageBlock` constructor validates a PNG signature. `AudioBlock` validates
base64 and requires a non-empty format when a data URI does not provide one.
These validations are local and safe to test without a provider.

## Granite formatters

The `mellea.formatters.granite` package exports typed Granite chat-completion
models and the intrinsic rewriter/result processor. The lower-level interfaces
are `InputProcessor`, `OutputProcessor`, `ChatCompletionRewriter`, and
`ChatCompletionResultProcessor` under `mellea.formatters.granite.base.io`.

For ordinary backend calls, let the backend's default `TemplateFormatter` or a
provider-appropriate formatter handle message rendering. Supply a
`TemplateFormatter(model_id=...)` explicitly when a Granite Switch/OpenAI
endpoint needs the model's chat template. Do not manually paste control tokens
unless the serving model's documented template requires it.

`IntrinsicsRewriter` reads an adapter `io.yaml` configuration and may add
parameters, `extra_body.structured_outputs`, logprobs, instructions, document
placement, and sentence boundaries. `IntrinsicsResultProcessor` converts the
provider result back through the adapter's output transformations. Configuration
errors are validation failures, not reasons to silently use an unrelated
adapter.

## Built-in intrinsic functions

High-level wrappers live in `mellea.stdlib.components.intrinsic.core` and
`rag`. Examples include `check_answerability`, `find_citations`,
`flag_hallucinated_content`, `rewrite_question`, `clarify_query`,
`check_certainty`, `requirement_check`, and context attributions. The catalog
also contains Guardian capabilities such as policy guardrails and factuality.
Use a `LocalHFBackend` or a Granite Switch model served through
`OpenAIBackend` as described below; Ollama and generic remote backends do not
provide the adapter-function route.

`check_context_relevance` is deprecated and is Granite 4.0-only; it has no
Granite 4.1 replacement. For current per-document relevance, use a prompted
requirement/generative check instead of substituting answerability, which asks
a different question over a document set.

## Local LoRA/aLoRA on HF

For catalog adapter functions:

```python
from mellea.backends.huggingface import LocalHFBackend
from mellea.stdlib.components.intrinsic import rag

backend = LocalHFBackend(model_id="ibm-granite/granite-4.1-3b")
# rag.check_answerability(question, documents, context, backend)
```

The first use may obtain adapter I/O configuration and weights from the Hub,
so `mellea[hf]`, network/access, a compatible checkpoint, and device memory are
separate prerequisites. Local custom adapter checkpoints use the adapter API
and currently commonly use the compatibility `CustomIntrinsicAdapter` path; it
is deprecated but remains the documented route for locally trained custom
weights. Ensure the adapter's base model and `io.yaml` output contract match.

Adapter routing is specific: loaded aLoRA/LoRA adapters can service requirement
checks; `default_to_constraint_checking_alora=False` suppresses automatic
routing for that backend, while an explicit `LLMaJRequirement` asks for an
LLM-as-judge path. If an adapter cannot be loaded, Mellea can fall back to
LLM-as-judge; if it loads but returns a schema-invalid result, the schema error
propagates and must be fixed.

## Granite Switch embedded adapters on OpenAI-compatible servers

Granite Switch embeds adapter weights in the model. Configure the OpenAI backend
with `load_embedded_adapters=True`, a matching `TemplateFormatter`, and the
vLLM/server endpoint. Only capabilities listed by the served model's
`adapter_index.json` are available. The I/O configurations may be retrieved
from the model repository on first use; this is a network operation.

For explicit selection, `EmbeddedIntrinsicAdapter.from_hub(...)` loads only the
adapter index and I/O configs, not separate adapter weights, and then the
adapter can be added to the OpenAI backend. Use `from_model_directory(...)` for
a local Granite Switch directory containing `adapter_index.json` and referenced
`io_configs/` files. Validate local paths and revisions before invoking.

## Structured output and difficult options

A Pydantic `format=` schema may be serialized differently by OpenAI, vLLM,
LiteLLM, WatsonX, or HF/llguidance. If a compatible endpoint rejects a schema or
an option, first reproduce the request with a mocked client and remove the
unsupported option; do not add a provider flag from memory. For a Granite
intrinsic, let the rewriter's declared `io.yaml` contract own its structured
output fields, and preserve unrelated `default_extra_body` keys through the
OpenAI backend's deep merge.

## Verification boundary

Native candidates include mocked OpenAI audio serialization, mocked WatsonX/HF
multimodal rejection, adapter catalog tests, formatter tests, and HF option
mapping tests. Live vision/audio, Hub adapter downloads, Granite Switch servers,
and full local checkpoints are deferred unless the user supplies the required
service, credentials, network, and hardware.
