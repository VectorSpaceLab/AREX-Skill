# Troubleshooting Inference And Endpoints

Diagnose from the selected model, task, provider mode, URL, and non-secret
request shape. Do not paste tokens, cookies, private media, or full request
bodies into issues. Capture HTTP status, request ID, provider/task, and a
redacted response message.

## Credential and routing failures

**Missing token/provider key.** A third-party provider helper may raise
`ValueError` saying an `api_key` is required. Check the saved login or inject
`HF_TOKEN` through a secret manager; for direct provider access inject that
provider's key. A custom/local URL or the `hf-inference` helper can prepare a
request with no token, but the target service may still require one. Do not set
`token=False`: the constructor rejects this legacy spelling so it cannot
silently fall back to a saved token. If using `api_key`, remember that it is an
alias for `token`, not a separate request credential.

**Wrong billing route.** An `hf_...` key normally routes through Hugging Face;
a provider key calls the provider directly where supported. `bill_to` applies
only to an HF-routed request and an organization with the required
subscription. A warning that an external key makes `bill_to` ineffective is
expected; do not rotate credentials or retry to change billing.

**Auto/provider mismatch.** With a Hub model ID, `provider="auto"` relies on
provider mappings or the server-side chat router. With no model, `None` or
`"auto"` selects the recommended `hf-inference` model for the task. A URL
target is direct and should not carry a provider. For a fixed provider, confirm
the model's mapping has that provider and the exact task. If the mapping is
absent, choose another mapped provider or a compatible model; do not blindly
retry the same request.

## Unsupported tasks and models

A `ValueError` such as `Provider ... not supported`, `Task ... not supported`,
`Model ... is not supported by provider ...`, or a task mismatch means the
client has rejected the request before or during request preparation. Compare
[providers-and-tasks.md](providers-and-tasks.md) with the model's current
provider mapping. For non-chat `auto`, use the first compatible mapping. A
narrow fallback may be implemented as:

```python
from huggingface_hub import InferenceClient

messages = [{"role": "user", "content": "<PROMPT>"}]
for provider in ("<PRIMARY_PROVIDER>", "<FALLBACK_PROVIDER>"):
    try:
        client = InferenceClient(
            model="<MODEL_ID>", provider=provider,
            api_key="<SECRET_FROM_MANAGER>", timeout=30,
        )
        output = client.chat_completion(messages, max_tokens=32)
        break
    except ValueError as error:
        if "supported" not in str(error).lower():
            raise
else:
    raise RuntimeError("No selected provider supports this model/task")
```

Use this only for a classification error known to be safe to re-prepare. Do
not retry after a request may have been accepted or billed without an
application-level idempotency policy. The bundled synthetic script uses a
mocked primary mismatch and fallback to avoid a paid retry.

## Malformed chat messages, tools, or schema

- `messages` must be a list of role/content objects. Do not pass one prompt
  string to `chat_completion`; use `text_generation` for that shape.
- Multimodal chunks need `type` (`text` or `image_url`) and the corresponding
  `text` or `image_url.url`. Use an HTTPS URL or a data URL, not a private path
  that the remote provider cannot access.
- Tool definitions need `type="function"`, a stable function `name`, and an
  object JSON Schema under `function.parameters`. Keep function names unique.
  Parse `function.arguments` and validate before executing them.
- `tool_choice` values and named function objects vary by provider. Start with
  `"auto"` or omit it, then use a named choice only after capability checks.
- `response_format` uses `{"type":"json_object"}` or
  `{"type":"json_schema", "json_schema": {"name": ..., "schema": ...}}`.
  Do not put `schema` directly beside `type`. Validate the returned content;
  provider success only means transport/request acceptance.
- A strict schema may use unsupported JSON Schema features. Reduce it to
  finite object/array/string/number/boolean fields and test with a mock before
  selecting a provider. HF Inference maps JSON schema to a grammar form and
  other providers may use their own implementation.

HTTP 422 responses are augmented with response text for a known task. Inspect
that redacted text for the first invalid field; changing the model/provider is
not a substitute for correcting malformed input.

## Streaming and async events

A sync `stream=True` call returns an iterable; an async call returns an
awaitable that resolves to an `AsyncIterable`. Correct async order is:

```python
stream = await async_client.chat_completion(
    [{"role": "user", "content": "<PROMPT>"}], stream=True
)
async for chunk in stream:
    if chunk.choices and chunk.choices[0].delta.content:
        consume(chunk.choices[0].delta.content)
```

An empty `choices` list, a delta without content, tool-call argument fragments,
reasoning-only deltas, and a terminal usage chunk are valid event cases. The
client's parser stops on `data: [DONE]`. On early exit, cancel the containing
consumer task as appropriate and close the async client in `finally`; a
partially consumed stream can keep a response/session open.

`InferenceTimeoutError` can mean the server was unavailable or a long
non-stream generation exceeded the timeout. Streaming may avoid a gateway
wait for long output but does not guarantee a provider will stream. Set an
explicit timeout and make retries bounded. Do not assume partial output is a
complete answer.

## Rate limits and HTTP failures

For `HfHubHTTPError`, preserve the HTTP status and request ID, inspect safe
headers such as `Retry-After`, and use provider-specific quotas. A 401/403 is
identity/access, not a transient failure. A 404 usually means the model,
provider route, endpoint namespace/name, or URL is wrong. A 422 is commonly
payload/task mismatch. 429 is rate/quota and should be retried only with a
bounded backoff honoring `Retry-After`; 5xx/504 may be transient, but repeat
only safe requests. A paid request may have been accepted even if the client
lost its response.

Use `timeout` on the client and the typed `InferenceTimeoutError`; do not catch
all exceptions and silently fall back because that can duplicate paid work.
For debug logs use the library's redaction controls and a mock transport to
inspect URL/payload construction.

## Binary media errors

`ContentT` advertises bytes, byte-like data, binary file objects, `Path`, URL,
and supported PIL images, but each provider helper accepts only a subset. A
string is treated as URL or local path; raw string content must be encoded as
bytes. Common fixes:

1. Check the path exists and is readable, open files as `rb`, and check a
   useful extension/MIME type.
2. Confirm the selected method is one of the provider's binary task helpers.
   For the 1.29.0 `hf-inference` binary helper, normalize file-like, PIL,
   `bytearray`, or `memoryview` input to `bytes` or `Path` before the call.
3. Avoid a second URL fetch by passing already loaded bytes when privacy or
   determinism matters.
4. Install Pillow for image decoding or use `client.post` if raw bytes are
   intentionally required; install NumPy for `feature_extraction`.
5. Do not log base64 media or return it in diagnostics.

When a binary method has parameters, HF's helper can put base64 input and
parameters into JSON; without parameters it may send raw content. Provider
helpers can require a different shape, so inspect a mocked request rather than
assuming all media tasks share a wire format.

## Endpoint state, quota, and health

Before deployment, call `list_inference_endpoints_hardware` and use the exact
vendor/region/accelerator/instance values from an entry with usable status and
sufficient namespace quota. A reserved, unavailable, deprecated, or out of
quota entry is not a valid recovery target.

Expected endpoint states include `pending`, `initializing`, `updating`,
`running`, `paused`, `scaledToZero`, `failed`, and `updateFailed`. `wait()`
health-checks the URL and raises `InferenceEndpointTimeoutError` after its
bounded timeout, or `InferenceEndpointError` for failed deployment/update.
A URL can exist while an endpoint is scaled to zero; the next request may have
a cold-start delay. A paused endpoint needs `resume()` first.

If `.client` or `.async_client` raises `InferenceEndpointError`, the endpoint
has no usable URL yet; fetch/wait rather than constructing a client from a
missing URL. After resume or update, wait again before inference. If health
checks fail while status says running, inspect the endpoint's logs/status in
the service and do not poll aggressively.

## Endpoint mutations and custom images

`create`, `update`, pause, resume, scale-to-zero, and delete are distinct
operations. Record namespace/name, current status, desired changes, and the
non-secret result. `delete` cannot be undone; require explicit confirmation
and re-fetch after any approval delay. Prefer pause or scale-to-zero to reduce
cost without losing configuration.

A custom image must preserve the API's variant shape. A flat dict with
`url` is treated as a custom image; an engine config is keyed, for example,
`{"vLLM": {"url": "<IMAGE>", "port": 8000}}`. Missing `url`, wrong casing,
unsupported fields, or a health route the container does not serve can produce
API validation or failed-health errors. Use `--engine`/`--custom-image` via
`hf endpoints deploy --help` to inspect current CLI options.

For vLLM/SGLang, `tensor_parallel_size` and `data_parallel_size` belong in the
engine image config and must match allocated accelerators. `container_args`
are command-line flags and do not replace those validated image fields. When
updating parallelism without a new image, the API fetches and round-trips the
current image; registry credentials are redacted and may require passing the
full image explicitly.

## MCP failures

Install `pip install "huggingface_hub[mcp]"` in the intended environment
before opening an MCP server connection. Importing `MCPClient` alone may still
succeed without it because the external `mcp` package is imported lazily by
`add_mcp_server`; failure can therefore appear only when connecting. The extra
is not needed for ordinary inference. `add_mcp_server` accepts `stdio`, `sse`,
and streamable `http`; check the transport's URL/command, timeout, headers, and
an explicit `allowed_tools` list. Do not execute an untrusted stdio command or
forward all inherited secrets.

A discovered duplicate tool name is skipped by the client. A missing session,
invalid model JSON arguments, or a tool execution exception becomes a tool
message; treat that as a failed tool result, not a successful answer. Use an
`asyncio.Event` abort event for `Agent.run`, cap turns, close the async context,
and keep MCP credentials separate from inference credentials.
