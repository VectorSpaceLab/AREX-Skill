# Remote Provider Workflows

These workflows avoid credentials and live endpoints. They are intended for
planning, code review, and downstream implementation guidance.

## 1. Select the Correct Loader

1. Identify the intended runtime:
   - Hosted API: OpenAI/Azure, Anthropic, Gemini, Mistral, Dottxt.
   - Local or remote server with an SDK client: Ollama, LM Studio, TGI.
   - OpenAI-compatible structured-generation server: SGLang or vLLM.
   - Generic OpenAI-compatible router with no source module: use `from_openai`.
2. Match the actual client class:
   - OpenAI SDK sync/async -> `from_openai`, `from_sglang`, or `from_vllm`
     depending on endpoint semantics.
   - Hugging Face `InferenceClient`/`AsyncInferenceClient` -> `from_tgi`.
   - Provider SDK clients -> matching `from_*` loader.
3. If the endpoint is SGLang or vLLM, do **not** use generic `from_openai` when
   the task needs regex/CFG/simple constrained outputs. Their loaders inject
   server-specific fields that the OpenAI wrapper does not.
4. If the docs page is OpenRouter, OrcaRouter, Requesty, or another generic
   OpenAI-compatible provider, do not invent a provider. Use `from_openai` and
   be prepared for upstream model support differences.

## 2. Gate Structured Output Before the Call

Use this before writing retry logic:

1. Classify the requested output type: plain text, JSON schema, JSON mode,
   enum/choice, regex, CFG/grammar, or simple scalar.
2. Check [provider-matrix.md](provider-matrix.md). If unsupported, fail fast or
   route to a supported provider.
3. Preserve provider-specific strictness:
   - OpenAI and Mistral need object schemas with `additionalProperties: false`;
     Outlines applies this automatically through `models/utils.py`.
   - Gemini only accepts a subset of JSON schema definitions and has its own
     enum/list path.
   - Dottxt must have a JSON-schema `output_type` and a model id.
   - vLLM structured output requires a new-enough server; old servers may
     silently ignore constraints.
4. Do not retry capability mismatches.

### Required difficult routing case: OpenAI Regex

If a caller asks for `outlines.regex(...)` or `outlines.types.Regex(...)` with
`from_openai`, the OpenAI adapter raises `TypeError` before any provider call:

- Do not change API keys or retry the same OpenAI request.
- Route to a supported provider: SGLang, TGI, vLLM server, or a local model via
  the structured-generation route.
- If the task must stay on a hosted OpenAI-compatible router, confirm that the
  upstream supports JSON schema and replace regex with an equivalent JSON schema
  only when semantically valid; otherwise surface the unsupported constraint.

## 3. Choose Sync, Async, Stream, or Caller-Side Concurrency

1. If the user needs streaming, exclude Dottxt; all other providers in this
   route have stream wrappers.
2. If the user needs async:
   - Use async client class: OpenAI/Azure, Dottxt, LM Studio, Ollama, SGLang,
     TGI, vLLM.
   - Use `from_mistral(..., async_client=True)` for Mistral.
   - Exclude Anthropic and Gemini in this source revision.
3. If the user asks for batch, explain that server wrappers here raise
   `NotImplementedError` for `batch`. Use bounded caller-side concurrency only
   with async-capable wrappers and provider-approved request rates.
4. For LM Studio async, call `await model.close()` when finished because the
   wrapper lazily enters the underlying async client context.

## 4. Run a No-Network Prerequisite Probe

The bundled script checks only importability and environment-variable presence.
It never instantiates a provider client and never calls a service.

```bash
python scripts/check_provider_prereqs.py --help
python scripts/check_provider_prereqs.py --providers openai tgi vllm --summary
```

Expected output labels variables as set/unset without printing values. Treat
unset credentials as configuration work, not as proof that a provider is
unusable in another runtime.

## 5. Handle Normalized Provider Errors

1. Catch `APIError` subclasses from Outlines wrappers, not provider-native SDK
   classes, unless using LM Studio or a local model that does not normalize.
2. Branch on `exc.retryable` for bounded retries.
3. Log or return safe metadata only: `provider`, `status_code`, `request_id`,
   `retryable`, and `hint`. Never log the original request body if it may
   contain prompts, credentials, or private data.
4. For `RateLimitError`, reduce concurrency/request rate and apply exponential
   backoff with jitter. Preserve `request_id` for provider support.
5. For `ServerError`, `APITimeoutError`, or `APIConnectionError`, retry only a
   bounded number of times; then surface endpoint/model/provider status.
6. For `AuthenticationError`, `PermissionDeniedError`, `NotFoundError`,
   `BadRequestError`, `ProviderResponseError`, or `GenerationError`, do not
   retry blindly. Change credentials, permissions, model/endpoint, schema,
   inference args, or prompt/refusal handling.

### Required difficult recovery case: 429 with request id

When a provider raises a status-bearing error with `status_code=429` and a
request ID/header, `normalize_provider_exception` produces `RateLimitError` with
`retryable=True`, `provider=<route>`, and `request_id=<id>`.

Recovery plan:

1. Stop immediate repeat calls.
2. Back off with jitter and a small max-attempt cap.
3. Lower concurrent async tasks or request rate.
4. Include the request ID in user-visible troubleshooting notes or provider
   support tickets.
5. Do not treat permanent auth/permission/not-found errors as retryable.

## 6. Mock-vs-Live Verification Boundary

- Unit tests can validate request shaping and exception normalization with mock
  clients; this skill can describe or run only no-network/static probes.
- Live provider verification requires explicit downstream permission,
  credentials, model names, budgets, and endpoint access. This skill must not
  perform it.
- For TGI, tests use `TGI_SERVER_URL` if present and otherwise mock clients.
  Mock coverage proves JSON/Regex request shaping and CFG rejection, not server
  availability.
- For vLLM, mock/static checks cannot prove that the live server version honors
  `structured_outputs`; verify with an approved constrained-output fixture in a
  separate runtime.
