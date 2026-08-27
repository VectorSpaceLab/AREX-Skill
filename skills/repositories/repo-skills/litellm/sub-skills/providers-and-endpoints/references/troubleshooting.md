# Troubleshooting Providers And Endpoints

Use this file to diagnose endpoint/model mismatch, provider prefix errors, parameter translation surprises, media upload failures, response/container edge cases, and pass-through header mistakes.

## Unsupported Endpoint Or Model Pair

Symptoms: `model not found`, `provider does not support endpoint`, 404 from upstream, validation error about missing transformer, or a chat call succeeds while embeddings/rerank/images fail.

Checks:

1. Identify the endpoint family first: chat, completion, embeddings, responses, images, audio, files, batches, rerank, OCR, search, vector stores, containers, or pass-through.
2. Confirm the provider has an implementation for that family. A provider chat module does not imply embeddings, files, batches, rerank, OCR, search, vector stores, or containers.
3. Confirm the model prefix selects the provider you intended.
4. For proxy aliases, inspect `model_list` and verify `model_name` is the client-facing alias while `litellm_params.model` is provider-prefixed.
5. Try the smallest request for that endpoint family with one required input and no optional params.

Fixes:

- Add or correct provider prefix.
- Use a provider/model that supports the endpoint family.
- Switch from normalized endpoint to provider pass-through only if the provider feature has no normalized mapping.
- Split mixed workflows into the right endpoint calls instead of sending all options to chat completions.

## Wrong Provider Prefix

Symptoms: the wrong provider API key is requested, a raw model is interpreted as a different provider, Bedrock cannot infer invoke provider, or OpenAI-compatible routes append the wrong path.

Checks:

- Use explicit prefixes for ambiguous models: `openai/`, `azure/`, `anthropic/`, `bedrock/`, `vertex_ai/`, `gemini/`, `openrouter/`, `cohere/`, `jina_ai/`, `voyage/`, and other provider IDs.
- For Bedrock, confirm whether the underlying model path includes an invoke/embedding provider marker when inference fails.
- For OpenAI-compatible providers, verify the prefix matches the configured provider transformer and base URL expectations.

Fixes:

- Use `provider/model` form in SDK calls or `litellm_params.model`.
- For proxy users, keep client-facing aliases stable and correct only the upstream `litellm_params`.
- Avoid raw provider model names in shared configs unless they are unambiguous and tested.

## `api_base` Versus `base_url` Confusion

Symptoms: duplicated `/v1`, missing `/chat/completions`, request goes to LiteLLM proxy instead of upstream, or OpenAI SDK cannot find route.

Checks:

- OpenAI SDK client talking to LiteLLM proxy: set client `base_url` to the proxy, usually ending in `/v1`.
- LiteLLM SDK or proxy upstream config: set `api_base` for the upstream provider.
- Inspect whether the provider transformer expects a base URL or complete endpoint URL.

Fixes:

- Do not put provider `api_base` in the OpenAI client when the client is supposed to call LiteLLM proxy.
- Do not put proxy `base_url` in `litellm_params.api_base` unless the upstream is another proxy.
- Remove duplicate path suffixes when a transformer appends endpoint paths automatically.

## Azure Deployment And API Version

Symptoms: Azure 404, deployment not found, missing API version, or OpenAI model name works outside Azure but fails with `azure/`.

Checks:

1. Model string should reference Azure deployment name or proxy alias, not necessarily the OpenAI base model name.
2. `api_base` should be the Azure resource endpoint.
3. `api_version` should be present and supported by the endpoint family.
4. The deployment should support the requested endpoint: chat, embeddings, responses, images, audio, files, batches, vector stores, or containers.

Fixes:

- Set `model: azure/<deployment-name>` in `litellm_params`.
- Add `api_version` explicitly in config/request/env.
- Use separate deployments or aliases for chat, embeddings, images, and responses.

## Unsupported Params Dropped Or Forwarded

Symptoms: provider rejects a parameter, output ignores an option, or LiteLLM says to set `drop_params=True`.

Checks:

- Determine whether the option is OpenAI-standard, endpoint-specific, or provider-native.
- Check if the provider transformer lists it as supported for that endpoint/model.
- Confirm whether `drop_params` is set globally, per request, or not set.

Fixes:

- Remove unsupported params for strict behavior.
- Set `drop_params=True` only when silently losing the param is acceptable.
- Move provider-native controls into the provider-specific expected field/header if the transformer supports it.
- Use pass-through for native provider features that should not be translated or dropped.

## File And Audio MIME Issues

Symptoms: 400 about invalid file, unsupported media type, empty upload, failed transcription, image edit rejected, or batch file invalid.

Checks:

- Confirm multipart field names and content type boundaries.
- Confirm file extension and MIME type match provider expectations.
- For files/batches, confirm `purpose` and JSONL shape.
- For audio, confirm sample format and provider-supported transcription/speech model.
- For images, confirm edit/variation/generation endpoint family and model support.

Fixes:

- Use actual file handles or correctly encoded multipart bodies rather than JSON strings for upload endpoints.
- Add explicit MIME type when the client cannot infer it.
- Upload batch files through the same provider endpoint that will own the batch.
- Keep file IDs provider-specific; do not reuse IDs across providers unless LiteLLM explicitly manages the mapping.

## Responses Streaming And Container Ownership

Symptoms: stream starts but never terminates, missing final usage, response retrieval fails, tool output continuation fails, or container/resource ID is not found.

Checks:

- Confirm the provider supports Responses API streaming for the selected route.
- Compare non-streaming and streaming behavior with the same model/input.
- Check whether response IDs, tool call IDs, vector store IDs, file IDs, and container IDs belong to the same provider/account/proxy namespace.
- Confirm cancellation/delete/update routes exist for that provider.

Fixes:

- Fall back to non-streaming to isolate transformation versus streaming transport issues.
- Keep response/container/vector/file lifecycle calls on the same endpoint family and provider alias.
- Avoid mixing provider-native IDs with LiteLLM-managed IDs unless the pass-through handler documents rewriting.

## Pass-Through Works In `curl` But Fails Through Proxy

Symptoms: direct upstream `curl` succeeds, proxy returns 401/403/404/415/502, upstream receives wrong path, or headers differ.

Checks:

1. Is the client calling the proxy route, not the upstream URL?
2. Does `general_settings.pass_through_endpoints[].path` match the proxy path exactly?
3. Is `include_subpath` correct for target URL shape?
4. Is caller auth (`Authorization: Bearer <proxy-key>`) separate from upstream auth (`headers` or provider signer)?
5. Are provider headers such as beta/version/region/workspace/deployment preserved?
6. Does the body content type match the upstream expectation?
7. For streaming, does the upstream wire format match a supported streaming handler?

Fixes:

- Reproduce against `scripts/mock_passthrough_target.py` and inspect the echoed path, headers, and JSON/body preview.
- Move upstream auth into pass-through config headers or provider credential environment variables.
- Toggle `include_subpath` if the upstream sees duplicated or missing path segments.
- Add required provider version/beta headers.
- Use non-streaming first, then enable streaming after route and auth are proven.

## Hard Synthetic Cases For Verification

1. Mixed endpoint mapping: given one application that needs chat completion, responses continuation, embeddings for retrieval, and image generation, map each request to the correct LiteLLM SDK helper and proxy route, identify provider prefixes, and flag unsupported endpoint/model pairs before runtime.
2. Pass-through header diagnosis: given a direct upstream `curl` that works and a proxy call that fails, use the mock target to prove whether the proxy forwards the expected subpath, content type, authorization, and custom provider headers.
