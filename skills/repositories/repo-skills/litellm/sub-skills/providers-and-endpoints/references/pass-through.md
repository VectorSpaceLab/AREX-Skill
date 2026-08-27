# Pass-Through Endpoints

Pass-through routes forward requests to upstream provider or arbitrary HTTP targets when LiteLLM’s normalized endpoint does not expose the exact provider-native API shape. Use pass-through for native provider APIs, compatibility testing, or provider features that should not be translated into LiteLLM’s OpenAI-normalized schema.

## When To Use Pass-Through

Use pass-through when:

- The upstream endpoint is provider-native and not covered by chat, responses, files, batches, images, audio, rerank, OCR, search, vector stores, or containers.
- The request body and response body must stay provider-native.
- A provider’s beta header, path shape, managed resource ID, or streaming wire format is not represented by LiteLLM’s normalized helpers.
- You need a controlled target to debug headers, subpaths, request method, JSON body, or streaming shape.

Do not use pass-through just to call ordinary chat completions through an OpenAI-compatible provider. Use normalized endpoints unless native shape is required.

## Generic Config Pattern

Proxy config supports pass-through targets under `general_settings.pass_through_endpoints`:

```yaml
general_settings:
  master_key: os.environ/LITELLM_MASTER_KEY
  pass_through_endpoints:
    - path: "/vendor-api"
      target: os.environ/VENDOR_API_BASE
      include_subpath: true
      headers:
        Authorization: os.environ/VENDOR_API_KEY
```

With `include_subpath: true`, a request to `/vendor-api/v1/resource/123` forwards to the configured target plus `/v1/resource/123`. Use this when the upstream target is a base URL. Set it false only when every call should hit exactly the target URL.

## Provider Pass-Through Families

LiteLLM also has provider-aware pass-through routes and handlers for providers such as Anthropic, Assembly, Cohere, Cursor, Gemini, OpenAI, Vertex/Vertex live, Bedrock, Azure, vLLM, and Watsonx where modules are implemented. These can add provider-specific logging, guardrail translation, managed ID rewriting, auth handling, or streaming handling.

Common pass-through route shapes include:

- Bedrock runtime paths such as `/bedrock/model/{model}/converse`, `/bedrock/model/{model}/invoke`, and streaming variants.
- Anthropic or Vertex partner native message paths where beta headers and publisher paths matter.
- OpenAI-compatible raw paths when a provider endpoint is not normalized by LiteLLM yet.
- Generic `pass_through_endpoints` paths configured by the operator.

## Local Shape Debugging

This sub-skill bundles a tiny local HTTP target:

```bash
python sub-skills/providers-and-endpoints/scripts/mock_passthrough_target.py --help
python sub-skills/providers-and-endpoints/scripts/mock_passthrough_target.py --host 127.0.0.1 --port 9999
```

It accepts common Bedrock-like `/model/.../converse`, `/model/.../invoke`, and generic paths, echoes request metadata, and returns safe mock JSON. It does not validate provider credentials or perform destructive actions.

Example generic config for the mock:

```yaml
general_settings:
  master_key: sk-local
  pass_through_endpoints:
    - path: "/debug-upstream"
      target: "http://127.0.0.1:9999"
      include_subpath: true
      headers:
        X-Debug-From-Proxy: "litellm"
```

Example smoke call:

```bash
curl -sS -X POST "http://localhost:4000/debug-upstream/anything" \
  -H "Authorization: Bearer sk-local" \
  -H "Content-Type: application/json" \
  -d '{"hello":"world"}'
```

If the mock sees the request but the real provider fails, the proxy route and header forwarding are probably correct; focus on provider auth, target URL, or provider-native body shape. If the mock does not see the request, focus on LiteLLM route registration, `path`, `include_subpath`, master key/auth, or client URL.

## Header And Auth Rules

- Client-to-proxy auth is separate from proxy-to-upstream auth. The caller’s `Authorization: Bearer <proxy key>` usually should not be forwarded as the upstream provider credential unless that is intentional.
- `headers` in `pass_through_endpoints` can inject static values or environment-backed secrets. Never hard-code secrets in public configs.
- Some provider pass-through handlers sign requests or manage provider auth internally. For example, Bedrock pass-through may still need AWS credentials available to the proxy even when using a local target for shape tests.
- If `curl` works directly against the upstream but fails through the proxy, compare forwarded method, path, query string, content type, authorization header, provider beta/version headers, and body bytes.

## Managed IDs And Subpaths

Pass-through can interact with managed resource IDs for files, vector stores, containers, or provider resources. When diagnosing ID failures:

1. Determine whether the ID is a LiteLLM-managed ID, a provider-native ID, or an alias rewritten by a pass-through handler.
2. Check whether the request path contains the raw provider ID or a LiteLLM managed ID.
3. Confirm `include_subpath` did not duplicate or drop path segments.
4. Retrieve/list the resource through the same endpoint family before updating, deleting, or attaching it to a response.

## Streaming Notes

Streaming pass-through is more fragile than JSON pass-through because upstream providers use different wire formats: SSE, chunked JSON, WebSocket, AWS event stream, or provider-specific event envelopes. If a non-streaming pass-through call works but streaming fails:

- Confirm the upstream content type.
- Confirm proxy streaming handler supports the provider route.
- Check whether the provider stream emits terminal usage/error events.
- Test a minimal stream with the provider-native SDK or direct `curl` before debugging LiteLLM transforms.

## Decision Checklist

- Can the normalized LiteLLM endpoint solve the task? If yes, avoid pass-through.
- Is the target a base URL or complete URL? Set `include_subpath` accordingly.
- Which authorization belongs to the proxy caller and which belongs to the upstream provider?
- Does the provider require version, beta, region, deployment, or workspace headers?
- Does the route require native streaming support?
- Can the bundled mock target reproduce the path/body/header shape safely before using live credentials?
