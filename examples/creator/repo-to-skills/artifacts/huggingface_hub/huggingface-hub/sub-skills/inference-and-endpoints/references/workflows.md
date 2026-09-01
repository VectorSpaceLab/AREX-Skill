# Safe Inference And Endpoint Workflows

These examples are planning templates. They use placeholders, `--help`, or
mock transports; they do not send live inference, deploy a model, spend
credits, or delete an endpoint. Replace placeholders only after confirming
identity, credentials, billing, and the mutation boundary.

## Inspect without a request

Verify the installed surface and CLI vocabulary first:

```bash
python -c 'import huggingface_hub; print(huggingface_hub.__version__)'
python - <<'PY'
import inspect
from huggingface_hub import AsyncInferenceClient, InferenceClient
for cls in (InferenceClient, AsyncInferenceClient):
    print(cls.__name__, inspect.signature(cls))
    for name in ("text_generation", "chat_completion", "feature_extraction", "text_to_image"):
        print(name, inspect.signature(getattr(cls, name)))
PY
hf endpoints --help
hf endpoints deploy --help
hf endpoints update --help
```

Do not use a real token in a signature check. The bundled
`scripts/mock_chat_recovery.py` is the request-level smoke test.

## A mocked chat request

A client can be exercised with `httpx.MockTransport` by installing a transport
factory before the first HF session is created. The handler below is a sketch;
the full tested composition is in the bundled script.

```python
import httpx
from unittest.mock import patch
from huggingface_hub import InferenceClient
from huggingface_hub.utils import set_client_factory

seen = []
def handler(request: httpx.Request) -> httpx.Response:
    seen.append(request)
    assert request.url.host == "mock.invalid"
    assert "authorization" not in {k.lower() for k in request.headers}
    return httpx.Response(200, json={
        "choices": [{"index": 0, "finish_reason": "stop", "message": {
            "role": "assistant", "content": '{"answer":"mocked"}'
        }}],
        "created": 0, "id": "mock", "model": "mock-model",
        "system_fingerprint": "mock", "usage": {
            "completion_tokens": 1, "prompt_tokens": 1, "total_tokens": 2
        },
    })

set_client_factory(lambda: httpx.Client(transport=httpx.MockTransport(handler)))
client = InferenceClient(base_url="https://mock.invalid/v1", api_key=None)
# Use a placeholder model in the payload; no real network occurs.
with patch("huggingface_hub.inference._providers.hf_inference.get_token", return_value=None):
    result = client.chat.completions.create(
        model="<MODEL_ID>",
        messages=[{"role": "user", "content": "<PROMPT>"}],
    )
assert result.choices[0].message.content
```

A test that wants to prove no credentials were used should pass `api_key=None`
and assert the handler sees no authorization header. A production call should
instead use a secret manager or saved HF login; do not copy this credentialless
fixture as a hosted-service recipe.

## Sync streaming

```python
stream = client.chat.completions.create(
    model="<MODEL_ID>",
    messages=[{"role": "user", "content": "<PROMPT>"}],
    stream=True,
)
for chunk in stream:
    if chunk.choices:
        delta = chunk.choices[0].delta
        if delta.content:
            print(delta.content, end="")
```

A stream is a resource. Consume it, or close the client/stream when stopping
early. Handle empty choices and terminal usage/finish chunks.

## Async streaming and cancellation

```python
import asyncio
from huggingface_hub import AsyncInferenceClient

async def run_once():
    async with AsyncInferenceClient(
        base_url="https://<MOCK_OR_APPROVED_ENDPOINT>/v1",
        api_key="<PLACEHOLDER_NOT_A_REAL_KEY>",
    ) as client:
        stream = await client.chat.completions.create(
            model="<MODEL_ID>",
            messages=[{"role": "user", "content": "<PROMPT>"}],
            stream=True,
        )
        try:
            async for chunk in stream:
                # Stop according to an application budget or abort event.
                if chunk.choices and chunk.choices[0].delta.content:
                    print(chunk.choices[0].delta.content, end="")
                    break
        finally:
            await client.close()

asyncio.run(run_once())
```

The async call is awaited before `async for`. Cancellation can happen while
waiting or while reading; use `try/finally`, cancel the task intentionally,
and close the async client. The generated async client shares input
signatures with the sync client but does not return a synchronous iterable.

## Tool and schema turn

1. Define a narrow JSON Schema for each function, with required fields and
   `additionalProperties: false` where the provider accepts it.
2. Send `tools` and `tool_choice` to `chat_completion`; keep the provider/model
   fixed while testing.
3. Inspect `message.tool_calls`, parse the arguments, validate them, and apply
   authorization/side-effect policy before executing anything.
4. Append the tool result with its `tool_call_id`, then request the next turn
   if the application policy allows it.
5. For JSON output, parse `message.content` and validate it independently;
   do not claim schema adherence merely because the request succeeded.

The synthetic script performs the request-shape portion with tools and a JSON
schema without implementing an untrusted external function.

## MCP client/agent plan

MCP is optional and experimental:

```bash
pip install "huggingface_hub[mcp]"
```

Use placeholders and a narrow allowlist. This configuration is safe to inspect
but must not be run against an untrusted command or URL:

```python
from huggingface_hub import MCPClient

async with MCPClient(
    model="<CHAT_MODEL_ID>",
    provider="<PROVIDER>",
    api_key="<SECRET_MANAGER_PLACEHOLDER>",
) as client:
    await client.add_mcp_server(
        type="http",
        url="https://<APPROVED_MCP_HOST>/mcp",
        headers={"Authorization": "<INJECT_AT_RUNTIME>"},
        allowed_tools=["<APPROVED_TOOL_NAME>"],
    )
    # process_single_turn_with_tools(messages) yields chat chunks and tool results.
```

`add_mcp_server` accepts `stdio` (`command`, optional `args`, `env`, `cwd`),
`sse` (`url`, optional headers/timeouts), and streamable `http` with analogous
fields. `Agent` accepts a list of server configs, has `load_tools()`, and
supports an `asyncio.Event` abort event in `run`. Prefer `cwd` in an isolated
workspace, sanitize environment inheritance, and never pass a token in a
prompt or tool result. MCP server access and model inference are two separate
credential surfaces.

## Endpoint plan (mutations explicit)

**READ-ONLY:** resolve hardware and quota, then inspect existing endpoints.

```python
from huggingface_hub import HfApi
api = HfApi(token="<HF_TOKEN_FROM_SECRET_MANAGER>")
hardware = api.list_inference_endpoints_hardware(namespace="<NAMESPACE>")
existing = api.list_inference_endpoints(namespace="<NAMESPACE>")
```

Select an entry whose status/quota is usable and record its exact vendor,
region, accelerator, instance type, and instance size. Do not paste a token in
logs. No deployment occurs in the inspection step.

**MUTATION:** create only after a reviewed plan:

```python
# PLACEHOLDER: this is a paid deployment; do not run as-is.
endpoint = api.create_inference_endpoint(
    "<ENDPOINT_NAME>", repository="<MODEL_ID>", framework="pytorch",
    task="<TASK>", accelerator="<ACCELERATOR>",
    vendor="<VENDOR>", region="<REGION>",
    instance_type="<INSTANCE_TYPE>", instance_size="<INSTANCE_SIZE>",
    type="authenticated", min_replica=1, max_replica=1,
)
```

For a catalog deployment, the experimental `create_inference_endpoint_from_catalog`
accepts a repository ID, optional name/accelerator, namespace, and token. For a
custom image, preserve the engine variant (`{"vLLM": {...}}`, `{"sGLang":
{...}}`, or another documented variant); a flat dict with `url` is wrapped as
`custom`. Do not echo registry credentials.

**WAIT/VERIFY:** `endpoint.wait(timeout=<SECONDS>, refresh_every=5)` polls,
checks the health route, mutates the same object, and returns only after a
healthy `running` endpoint. Access `.client`/`.async_client` only then. A
running endpoint's URL is passed to `InferenceClient(model=endpoint.url)`;
this is direct endpoint inference, not provider routing.

**MUTATION/DESTRUCTIVE:** `update`, `pause`, `resume`, and `scale_to_zero`
return updated endpoint objects. Pause avoids charges and requires explicit
resume; scale-to-zero avoids charges and can cold-start on request. `delete`
is irreversible: show exact namespace/name and obtain confirmation immediately
before calling it. Re-fetch after a delayed confirmation.

## Why this synthetic case is separate

The bundled case combines tool/schema payload assertions, async stream
cancellation, and fallback after an unsupported provider/task. Repository VCR
and production tests are intentionally narrower: VCR records a chosen service
rather than proving recovery across providers, and production tests are
credential/network dependent and unsuitable for deterministic cancellation or
no-token assertions. The synthetic case therefore complements, rather than
replaces, native tests.
