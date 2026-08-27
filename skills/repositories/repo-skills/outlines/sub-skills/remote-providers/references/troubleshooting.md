# Remote Provider Troubleshooting

Use this when provider setup, request shaping, or normalized errors fail. Keep
secrets out of logs and never use live endpoints unless the downstream runtime
explicitly allows it.

## Install and Import Extras

Symptoms:

- `ModuleNotFoundError: No module named 'openai'`, `anthropic`, `google.genai`,
  `mistralai`, `ollama`, `lmstudio`, `huggingface_hub`, or `dottxt`.
- `ValueError: Invalid client type` from a `from_*` loader.

Recovery:

1. Install the matching optional extra or SDK in the runtime environment:
   - OpenAI/Azure/SGLang/vLLM: `openai` / `outlines[openai]` or provider extra.
   - Anthropic: `anthropic` / `outlines[anthropic]`.
   - Gemini: `google-genai` / `outlines[gemini]`.
   - Mistral: `mistralai` / `outlines[mistral]`.
   - Ollama: `ollama` / `outlines[ollama]`.
   - LM Studio: `lmstudio` / `outlines[lmstudio]`.
   - TGI: `huggingface_hub` / `outlines[tgi]`.
   - Dottxt: `dottxt` / `outlines[dottxt]`.
2. Re-run the prerequisite script to check importability only.
3. Ensure the client instance belongs to the loader:
   - OpenAI SDK client for `from_openai`, `from_sglang`, and `from_vllm`.
   - HF inference client for `from_tgi`.
   - Exact provider SDK client for each other loader.

## Authentication, Permission, and Not Found

Symptoms:

- `AuthenticationError` (`401`), `PermissionDeniedError` (`403`), or
  `NotFoundError` (`404`).
- Provider-native auth errors when using LM Studio or direct SDK calls.

Recovery:

1. Check only whether required variables are present; never print values.
2. Confirm the account/key scope can access the chosen model or deployment.
3. Confirm model identifiers and endpoint/base URL:
   - Azure often needs a deployment name and API version, not just a public
     OpenAI model name.
   - Dottxt requires a model id at loader time or `model=` call time.
   - TGI/vLLM/SGLang model names must match the server's served model.
4. Do not retry auth/permission/not-found errors without changing
   configuration.

## Rate Limits and Bounded Retry

Symptoms:

- `RateLimitError`, usually `status_code=429`; may include `request_id`.

Recovery:

1. Treat as retryable but bounded.
2. Use exponential backoff with jitter and a max attempt count.
3. Reduce async concurrency, stream fan-out, request size, or sampling count
   (`n`/parallel outputs) if applicable.
4. Preserve `provider`, `status_code`, and `request_id` in safe diagnostics.
5. If repeated, ask for provider quota/budget decisions instead of continuing.

## Malformed Schema or Unsupported Output

Symptoms:

- `TypeError` or `NotImplementedError` from an adapter before a service call.
- `BadRequestError` with schema/unsupported parameter messages from a provider.
- TGI CFG raises `NotImplementedError`; OpenAI Regex/CFG raises `TypeError`.

Recovery:

1. Check the output-type row in [provider-matrix.md](provider-matrix.md).
2. If unsupported, route to a supported provider; do not retry identical calls.
3. For OpenAI/Mistral JSON schema, remember Outlines adds
   `additionalProperties: false`; if the provider still rejects it, simplify the
   schema and remove unsupported JSON Schema keywords such as regex `pattern`
   where providers disallow it.
4. For Gemini, use Pydantic/dataclass/TypedDict JSON schemas or homogeneous
   built-in `list[...]`; avoid regex/pattern and CFG.
5. For Dottxt, always provide a JSON-schema `output_type`; it cannot run plain
   text, Regex, or CFG.
6. For SGLang CFG, supply EBNF suitable for SGLang, not a normal Outlines/Lark
   grammar.
7. For vLLM, confirm the live server supports the `structured_outputs` request
   field before trusting constrained results.

## Model or Endpoint Mismatch

Symptoms:

- `NotFoundError`, provider `404`, empty/unconstrained output, or refusal-like
  server responses.
- SGLang/vLLM endpoints return OpenAI-compatible responses but ignore
  constraints.

Recovery:

1. Verify loader-to-endpoint match:
   - Generic OpenAI/OpenRouter/Requesty/OrcaRouter -> `from_openai`.
   - SGLang server -> `from_sglang`.
   - vLLM OpenAI-compatible server -> `from_vllm`.
   - TGI server -> `from_tgi`.
2. Confirm base URL path conventions (`/v1` for OpenAI-compatible servers when
   required by the client).
3. Confirm model/deployment names match the server or cloud account.
4. For vLLM structured outputs, old servers may silently ignore the newer
   `structured_outputs` field; require an approved live constrained-output
   fixture outside this no-network skill.

## Timeout and Connection Failures

Symptoms:

- `APITimeoutError` or `APIConnectionError`.
- Ollama/TGI/SGLang/vLLM local server not running or refused connection.

Recovery:

1. Check endpoint variables and client base URLs without printing secrets.
2. Confirm whether the runtime is allowed to access the network or local server.
3. Retry only after a bounded wait if the error is transient.
4. For local servers, start/pull/load the model outside this skill's no-network
   boundary, then re-run approved live checks if permitted.

## Refusal, Provider Response, and Generation Errors

Symptoms:

- `GenerationError` from OpenAI, SGLang, or vLLM wrapper refusals.
- OpenAI SDK length/content-filter finish reason errors normalized to
  `GenerationError`.
- `ProviderResponseError` for malformed/unparseable provider responses.

Recovery:

1. Do not retry blindly. Inspect whether policy/refusal, max-token, content
   filter, or schema/format mismatch caused the failure.
2. Change prompt, safety-sensitive content, `max_tokens`, or output schema.
3. For `ProviderResponseError`, try a simpler schema or a provider-supported
   output type; if transient, perform only bounded retries.
4. Surface provider/request ID metadata when available.

## Async, Stream, and Batch Limitations

- No batch support in this route; every provider wrapper here raises
  `NotImplementedError` for `batch`.
- Dottxt has no streaming.
- Anthropic and Gemini have no async wrappers in this source revision.
- Mistral async requires `from_mistral(..., async_client=True)`.
- LM Studio async models should be closed with `await model.close()` when done.
- Caller-side concurrency must respect provider rate limits and should catch
  `RateLimitError` with bounded backoff.

## Mock vs Live Verification

- Mock/static tests can prove request argument construction, importability, and
  normalized exception plumbing.
- Mock tests cannot prove credentials, account permissions, live model support,
  or vLLM/SGLang/TGI server backend capabilities.
- The TGI tests use a real server only when `TGI_SERVER_URL` is set; otherwise
  they use mock clients. Treat mock success as API-shape evidence only.
- Live checks require explicit credentials, endpoints, budget, and permission in
  a downstream runtime; this skill and its script do not perform them.
