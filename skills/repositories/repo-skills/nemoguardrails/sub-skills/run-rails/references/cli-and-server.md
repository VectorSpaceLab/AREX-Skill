# CLI and Server

## CLI quick reference

### `chat`

```bash
nemoguardrails chat --config PATH [--verbose] [--verbose-no-llm] [--verbose-simplify] [--debug-level LEVEL] [--streaming]
```

Use this for an interactive local chat session.

Key flags:

- `--config`: a single config directory or file. The CLI rejects multiple `--config` values.
- `--verbose`: show detailed logging.
- `--verbose-no-llm`: verbose mode without LLM prompts and responses.
- `--verbose-simplify`: reduce the verbosity noise.
- `--debug-level`: enables verbose mode automatically and prints flow execution detail.
- `--streaming`: enable streaming when the configuration supports it.
- `--server-url`: connect to a running server instead of loading config locally.
- `--config-id`: required when connecting to a server.

### `server`

```bash
nemoguardrails server --config PATH [--port 8000] [--default-config-id ID] [--verbose] [--disable-chat-ui] [--auto-reload] [--prefix /api]
```

Use this to expose configurations over HTTP.

Key flags:

- `--config`: path to a configuration root. A root with subfolders becomes multi-config mode; a root with a `config.yml`/`config.yaml` becomes single-config mode.
- `--port`: HTTP port, default `8000`.
- `--default-config-id`: default config when a request omits one.
- `--verbose`: show detailed logs.
- `--disable-chat-ui`: disable the built-in testing UI.
- `--auto-reload`: reload on config file changes; development only.
- `--prefix`: mount all server paths under a prefix. The prefix must start with `/`.

### `actions-server`

```bash
nemoguardrails actions-server [--port 8001]
```

Use this to run custom actions in a separate process. The server discovers actions in the current folder and subfolders and exposes:

- `GET /v1/actions/list`
- `POST /v1/actions/run`

### `convert`

```bash
nemoguardrails convert PATH --from-version 1.0 --validate
```

Use this to migrate Colang and config files.

Key flags:

- `--from-version`: `1.0` or `2.0-alpha`.
- `--verbose`: show migration detail.
- `--validate`: validate the migrated output.
- `--no-use-active-decorator`: disable the active decorator in the migration.
- `--no-include-main-flow`: skip adding a main flow.

## Server behavior

- If you start the server without `--config`, it looks for a local `./config` folder and otherwise falls back to the built-in examples.
- `--disable-chat-ui` is the safest production default.
- `--prefix` changes every mounted path, including `/v1/health`.
- CORS is controlled by `NEMO_GUARDRAILS_SERVER_ENABLE_CORS` and `NEMO_GUARDRAILS_SERVER_ALLOWED_ORIGINS`.

## HTTP endpoints

| Method | Path | Purpose | Notes |
| --- | --- | --- | --- |
| `GET` | `/v1/health` | Liveness check | Also available as `/healthz`; shallow health only. |
| `GET` | `/v1/rails/configs` | List available config IDs | Multi-config mode lists config subfolders with a `config.yml` or `config.yaml`. |
| `GET` | `/v1/models` | Proxy the upstream model list | Uses the request `Authorization` header or provider env vars. |
| `POST` | `/v1/chat/completions` | OpenAI-compatible chat completion | Accepts a `guardrails` extension object. |
| `POST` | `/v1/checks` | Validation-only rails check | Colang 1.0 only. |
| `GET` | `/v1/challenges` | List red-teaming challenges | Loaded from `challenges.json` when present. |

## Chat completion request fields

### Standard OpenAI fields

`model`, `messages`, `stream`, `max_tokens`, `temperature`, `top_p`, `stop`, `presence_penalty`, `frequency_penalty`, `logit_bias`, `logprobs`, `tools`, `tool_choice`, `parallel_tool_calls`.

### `guardrails` extension fields

| Field | Meaning | Limits |
| --- | --- | --- |
| `config_id` | Select one config | Mutually exclusive with `config_ids`. |
| `config_ids` | Combine multiple configs in order | Later configs win on conflicts. |
| `context` | Extra context inserted as a `context` message | Must be a dict. |
| `options` | `GenerationOptions` passed to the runtime | Uses the same structure as the Python API. |
| `state` | Public state for continuation | Only the Colang 1.0 transcript form `{"events": [...]}` is accepted over HTTP. |
| `thread_id` | Server-side conversation thread ID | Colang 1.0 only, length 16-255, non-streaming only, and requires a datastore. |

### Response fields

The chat response is a normal OpenAI `ChatCompletion` plus a `guardrails` object that can include `config_id`, `state`, `llm_output`, `output_data`, and `log`.

## Hard server rules

- `config_id` and `config_ids` are mutually exclusive.
- `thread_id` is not supported for Colang 2.0.
- `state` is not supported for Colang 2.0 over HTTP.
- `tools`, `tool_choice`, and `parallel_tool_calls` are only supported for non-streaming requests when the config has `passthrough: true`.
- `/v1/checks` does not support Colang 2.0 configs.
- Streaming requests return SSE chunks.

## Useful client patterns

- OpenAI-compatible clients can use the server base URL ending in `/v1`.
- For direct HTTP, keep the request body small and choose exactly one config path.
- If you need a quick no-provider preflight, use `scripts/server_schema_smoke.py` instead of opening the server manually.
