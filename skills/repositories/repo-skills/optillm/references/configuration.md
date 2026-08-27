# OptiLLM Configuration Reference

Read this when a task spans server CLI flags, environment variables, provider selection, auth, SSL, batching, logging, or request-level approach selection.

## Server entry points

- Package console script: `optillm`
- Backwards-compatible source wrapper: `python optillm.py`
- Main package entry point: `optillm:main`
- HTTP endpoints: `POST /v1/chat/completions`, `GET /v1/models`, `GET /health`

The server defaults to host `127.0.0.1` and port `8000`. Use `--host 0.0.0.0` only for trusted networks or when `--optillm-api-key` is configured.

## Provider selection

OptiLLM selects a client in this order:

1. `OPTILLM_API_KEY` set: use built-in local inference client.
2. `CEREBRAS_API_KEY` set: use Cerebras client.
3. `OPENAI_API_KEY` set: use OpenAI-compatible client, optionally with `--base-url` / `OPTILLM_BASE_URL`.
4. `AZURE_OPENAI_API_KEY` with `AZURE_API_VERSION` and `AZURE_API_BASE`: use Azure OpenAI client; managed identity path uses Azure credentials when no API key is present.
5. No provider env found: use the LiteLLM wrapper fallback.

If the user expected an external provider but local model loading starts, check whether `OPTILLM_API_KEY` is set.

## Important CLI flags and environment variables

| Purpose | CLI flag | Environment variable | Default |
| --- | --- | --- | --- |
| Default approach | `--approach` | `OPTILLM_APPROACH` | `auto` when parsed by CLI |
| Model | `--model` | `OPTILLM_MODEL` | `gpt-4o-mini` |
| Base URL | `--base-url` / `--base_url` | `OPTILLM_BASE_URL` | empty |
| Host/port | `--host`, `--port` | `OPTILLM_HOST`, `OPTILLM_PORT` | `127.0.0.1`, `8000` |
| Server auth | `--optillm-api-key` | `OPTILLM_API_KEY` | empty |
| Best-of-N samples | `--best-of-n` / `--best_of_n` | `OPTILLM_BEST_OF_N` | `3` |
| MCTS | `--mcts-simulations`, `--mcts-exploration`, `--mcts-depth` | `OPTILLM_SIMULATIONS`, `OPTILLM_EXPLORATION`, `OPTILLM_DEPTH` | `2`, `0.2`, `1` |
| RStar | `--rstar-max-depth`, `--rstar-num-rollouts`, `--rstar-c` | `OPTILLM_RSTAR_MAX_DEPTH`, `OPTILLM_RSTAR_NUM_ROLLOUTS`, `OPTILLM_RSTAR_C` | `3`, `5`, `1.4` |
| Number of responses | `--n` | `OPTILLM_N` | `1` |
| CoT reflection detail | `--return-full-response` | `OPTILLM_RETURN_FULL_RESPONSE` | false |
| Plugin directory | `--plugins-dir` | `OPTILLM_PLUGINS_DIR` | package plugins |
| Conversation logging | `--log-conversations`, `--conversation-log-dir` | `OPTILLM_LOG_CONVERSATIONS`, `OPTILLM_CONVERSATION_LOG_DIR` | disabled |
| Batch mode | `--batch-mode`, `--batch-size`, `--batch-wait-ms` | `OPTILLM_BATCH_MODE`, `OPTILLM_BATCH_SIZE`, `OPTILLM_BATCH_WAIT_MS` | disabled, `4`, `50` |
| SSL verification | `--ssl-verify`, `--no-ssl-verify`, `--ssl-cert-path` | `OPTILLM_SSL_VERIFY`, `OPTILLM_SSL_CERT_PATH` | verify enabled |
| Gradio GUI | `--launch-gui` | `OPTILLM_LAUNCH_GUI` | false |

## Approach selection priority

When the server is in auto mode, approach selection can come from:

1. Model prefix: `moa-gpt-4o-mini`
2. Request body field: `optillm_approach` or OpenAI SDK `extra_body={"optillm_approach": "re2"}`
3. Prompt tag: `<optillm_approach>re2</optillm_approach>` inside a system or user message

When `--approach` is not `auto`, the server prepends that approach to the requested model. Do not combine `none` with other approaches; the server rejects `none` inside `&` or `|` compositions.

## Composition semantics

- `approach-model`: one approach, one final response.
- `a&b-model`: pipeline; the output from `a` becomes input to `b`.
- `a|b|c-model`: parallel; returns a list of responses from multiple approaches.
- `n > 1`: repeats the selected operation and returns multiple choices/list items.

Use the bundled `sub-skills/optimization-approaches/scripts/approach_matrix.py` helper to inspect parsing without provider calls.

## SSL and auth

- `--no-ssl-verify` disables upstream certificate verification and is only appropriate for development or controlled debugging.
- `--ssl-cert-path` should point to a CA bundle when using corporate/self-signed upstream endpoints.
- `--optillm-api-key` secures all routes except `/health`; clients must send `Authorization: Bearer <key>`.
- A request bearer token beginning with `sk-` can override the configured provider key for that request.

## Batching and logging

Batch mode rejects streaming requests and incompatible mixed batches. It currently processes through the batching infrastructure and validates compatibility; do not assume true model-level throughput batching unless local inference code for that model path has been verified.

Conversation logging records client request metadata, provider calls, final responses, and errors when enabled. Treat logs as sensitive because they may contain prompts or provider responses.
