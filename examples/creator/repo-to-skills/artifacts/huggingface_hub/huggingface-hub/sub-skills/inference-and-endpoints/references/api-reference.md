# Inference API Reference

This reference records the public surfaces inspected from the checkout at
`huggingface_hub` 1.29.0. Import public names from `huggingface_hub`; the
`_generated` paths are implementation evidence, not stable import targets.

## Client constructors

```python
InferenceClient(
    model: str | None = None, *,
    provider: str | Literal["auto"] | None = None,
    token: str | None = None,
    timeout: float | None = None,
    headers: dict[str, str] | None = None,
    cookies: dict[str, str] | None = None,
    bill_to: str | None = None,
    base_url: str | None = None,
    api_key: str | None = None,
)

AsyncInferenceClient(
    model: str | None = None, *,
    provider: str | Literal["auto"] | None = None,
    token: str | None = None,
    timeout: float | None = None,
    headers: dict[str, str] | None = None,
    cookies: dict[str, str] | None = None,
    bill_to: str | None = None,
    base_url: str | None = None,
    api_key: str | None = None,
)
```

The concrete provider literals are listed in
[providers-and-tasks.md](providers-and-tasks.md). `model` may be a Hub model
ID or a deployed/compatible URL. The constructor rejects both aliases in each
pair (`model` + `base_url`, or `token` + `api_key`). `api_key` is the OpenAI
compatibility spelling for `token`; it does not mean request data. The
implementation stores `model` or `base_url` in the same client field. In chat,
a URL from either spelling is normalized to a chat-completions path. If the
call also passes `model=`, the constructor URL remains the transport target and
the call-time value becomes the payload model; `base_url` is the
OpenAI-compatible name, not a separate transport implementation.

The sync client is a context manager and exposes `close()`. The async client is
an async context manager (`async with`) and exposes `await close()`. A default
`token=None` lets a provider helper resolve the saved token when it requires
one. Third-party helpers require either a compatible direct provider key or an
HF token for routed access; the `hf-inference` URL/helper can prepare an
unauthenticated request, although the target service may reject it. Constructor
`token=False` is always rejected rather than disabling a saved token silently.

## Representative task signatures and outputs

These signatures were obtained with `inspect.signature` against the checkout.
Other task methods follow the same `model` and provider-aware request pattern;
consult [task-types.md](task-types.md) rather than copying generated files.

```python
InferenceClient.text_generation(
    prompt: str, *,
    details: bool | None = None,
    stream: bool | None = None,
    model: str | None = None,
    adapter_id: str | None = None,
    best_of: int | None = None,
    decoder_input_details: bool | None = None,
    do_sample: bool | None = None,
    frequency_penalty: float | None = None,
    grammar: dict | None = None,
    max_new_tokens: int | None = None,
    repetition_penalty: float | None = None,
    return_full_text: bool | None = None,
    seed: int | None = None,
    stop: list[str] | None = None,
    stop_sequences: list[str] | None = None,
    temperature: float | None = None,
    top_k: int | None = None,
    top_n_tokens: int | None = None,
    top_p: float | None = None,
    truncate: int | None = None,
    typical_p: float | None = None,
    watermark: bool | None = None,
) -> str | TextGenerationOutput | Iterable[str] | Iterable[TextGenerationStreamOutput]
```

With defaults, this returns a `str`. `details=True` returns
`TextGenerationOutput`; `stream=True` returns an iterable of strings, or
stream-output dataclasses when `details=True`. Streaming and details are
backend/provider dependent; they are especially meaningful for TGI.

```python
InferenceClient.chat_completion(
    messages: list[dict | ChatCompletionInputMessage], *,
    model: str | None = None,
    stream: bool = False,
    frequency_penalty: float | None = None,
    logit_bias: list[float] | None = None,
    logprobs: bool | None = None,
    max_tokens: int | None = None,
    n: int | None = None,
    presence_penalty: float | None = None,
    response_format: ChatCompletionInputResponseFormatText
        | ChatCompletionInputResponseFormatJSONSchema
        | ChatCompletionInputResponseFormatJSONObject
        | None = None,
    seed: int | None = None,
    stop: list[str] | None = None,
    stream_options: ChatCompletionInputStreamOptions | None = None,
    temperature: float | None = None,
    tool_choice: dict | str | None = None,
    tool_prompt: str | None = None,
    tools: list[ChatCompletionInputTool] | None = None,
    top_logprobs: int | None = None,
    top_p: float | None = None,
    extra_body: dict | None = None,
) -> ChatCompletionOutput | Iterable[ChatCompletionStreamOutput]
```

The actual annotations use generated aliases. A non-stream response is a
`ChatCompletionOutput`; a stream is an iterable of `ChatCompletionStreamOutput`.
Access non-stream text at `output.choices[0].message.content`. A stream delta
can contain `content`, `reasoning`, tool-call fragments, or no content.

```python
InferenceClient.feature_extraction(
    text: str | list[str], *,
    normalize: bool | None = None,
    prompt_name: str | None = None,
    truncate: bool | None = None,
    truncation_direction: Literal["left", "right"] | None = None,
    dimensions: int | None = None,
    encoding_format: Literal["float", "base64"] | None = None,
    model: str | None = None,
) -> numpy.ndarray

InferenceClient.text_to_image(
    prompt: str, *,
    negative_prompt: str | None = None,
    height: int | None = None,
    width: int | None = None,
    num_inference_steps: int | None = None,
    guidance_scale: float | None = None,
    model: str | None = None,
    scheduler: str | None = None,
    seed: int | None = None,
    extra_body: dict[str, Any] | None = None,
) -> PIL.Image.Image
```

`feature_extraction` converts the provider response to a float32 NumPy array
and may accept a batch. `text_to_image` decodes image bytes and therefore
needs Pillow. `audio_*`, vision, classification, QA, translation, and other
methods use generated task-specific outputs; provider availability is not
implied by a method existing on the client.

## Async parity

`AsyncInferenceClient` has the same constructor and public task input
signatures. Its ordinary task methods are coroutines: `await
client.feature_extraction(...)`, `await client.text_to_image(...)`, and
`await client.chat_completion(...)` for non-stream output. When `stream=True`,
await the call first and then `async for` the returned `AsyncIterable`:

```python
async with AsyncInferenceClient(
    model="<MODEL_ID_OR_URL>", api_key="<TOKEN_OR_PROVIDER_KEY>"
) as client:
    stream = await client.chat.completions.create(
        messages=[{"role": "user", "content": "<PROMPT>"}], stream=True
    )
    async for chunk in stream:
        content = chunk.choices[0].delta.content if chunk.choices else None
        if content:
            print(content, end="")
```

`client.chat.completions.create` is an alias for `chat_completion` on both
clients. The generated async client is regenerated from the sync client, so
signature parity is a tested invariant; do not edit it directly.

## Endpoint classes and helpers

Public endpoint data classes exported from `huggingface_hub` are
`InferenceEndpoint`, `InferenceEndpointHardware`, `InferenceEndpointStatus`,
and `InferenceEndpointType`, together with endpoint error classes. The
`scaling_metric` API argument accepts the documented values
`"pendingRequests"` and `"hardwareUsage"`; the implementation enum is not a
public top-level export in 1.29.0. The endpoint object is built from API data
with `InferenceEndpoint.from_raw(raw, namespace, token=None, api=None)` and
exposes `.name`, `.repository`, `.status`, `.url`, `.task`, `.framework`,
`.revision`, `.health_route`, `.raw`, `.client`, and `.async_client`.

```python
get_inference_endpoint(
    name: str, *, namespace: str | None = None,
    token: bool | str | None = None
) -> InferenceEndpoint

list_inference_endpoints(
    namespace: str | None = None, *, token: bool | str | None = None
) -> list[InferenceEndpoint]

list_inference_endpoints_hardware(
    *, namespace: str | None = None, token: bool | str | None = None
) -> list[InferenceEndpointHardware]

create_inference_endpoint(
    name: str, *, repository: str, framework: str, accelerator: str,
    instance_size: str, instance_type: str, region: str, vendor: str,
    account_id: str | None = None, min_replica: int = 1,
    max_replica: int = 1, scaling_metric=None, scaling_threshold=None,
    scale_to_zero_timeout: int | None = None, revision: str | None = None,
    task: str | None = None, custom_image: dict | None = None,
    container_command: list[str] | None = None,
    container_args: list[str] | None = None, env: dict[str, str] | None = None,
    secrets: dict[str, str] | None = None, type="authenticated",
    domain: str | None = None, path: str | None = None,
    cache_http_responses: bool | None = None, tags: list[str] | None = None,
    namespace: str | None = None, token: bool | str | None = None,
) -> InferenceEndpoint

create_inference_endpoint_from_catalog(
    repo_id: str, *, name: str | None = None,
    accelerator: str | None = None, token: bool | str | None = None,
    namespace: str | None = None
) -> InferenceEndpoint

list_inference_catalog(*, token: bool | str | None = None) -> list[str]
```

Catalog operations are experimental. `update_inference_endpoint` accepts
compute/model/route settings including `tensor_parallel_size` and
`data_parallel_size`; `delete_inference_endpoint` returns `None`; pause,
resume, and scale-to-zero return an updated endpoint. The endpoint aliases
have these inspected signatures:

```python
endpoint.fetch() -> InferenceEndpoint
endpoint.wait(timeout: int | None = None, refresh_every: int = 5) -> InferenceEndpoint
endpoint.update(*, accelerator=None, instance_size=None, instance_type=None,
               min_replica=None, max_replica=None, scale_to_zero_timeout=None,
               repository=None, framework=None, revision=None, task=None,
               custom_image=None, container_command=None, container_args=None,
               tensor_parallel_size=None, data_parallel_size=None,
               secrets=None) -> InferenceEndpoint
endpoint.pause() -> InferenceEndpoint
endpoint.resume(running_ok: bool = True) -> InferenceEndpoint
endpoint.scale_to_zero() -> InferenceEndpoint
endpoint.delete() -> None
```

`.client` and `.async_client` raise `InferenceEndpointError` before a URL is
available. `wait` health-checks a running URL, mutates the same object, and
raises `InferenceEndpointTimeoutError` for a bounded timeout or
`InferenceEndpointError` for failed deployment/update.

## Safe signature inspection

The following checks imports and signatures without authentication or HTTP:

```bash
PYTHONPATH=src python - <<'PY'
import inspect
from huggingface_hub import AsyncInferenceClient, InferenceClient
for cls in (InferenceClient, AsyncInferenceClient):
    print(cls.__name__, inspect.signature(cls))
    for name in ("text_generation", "chat_completion", "feature_extraction", "text_to_image"):
        print(name, inspect.signature(getattr(cls, name)))
PY
```

Use `MockTransport` or the bundled synthetic script for request behavior; do
not replace this check with a live prediction.
