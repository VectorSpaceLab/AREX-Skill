# Serving API reference

DeepPavlov exposes a prepared config either as REST (`riseapi`) or as a length-prefixed socket service (`risesocket`).

## REST start

```bash
python -m deeppavlov riseapi <config_path> [-d] [-p <port>] [--https] [--key <SSL key file path>] [--cert <SSL certificate file path>]
```

`-d` downloads model-specific data before startup. `-p`, `--https`, `--key`, and `--cert` override the service defaults from the active settings directory.

## REST routes

| Route | Method | Purpose | Notes |
| --- | --- | --- | --- |
| `/model` | POST | Run inference | Default model endpoint. The active config may override the endpoint name through `server_config.json`. |
| `/probe` | POST | Health check | Returns the one-item list ["Test passed"] when the model can execute a minimal batch. Requests are not dialog-logged. |
| `/api` | GET | Inspect model I/O names | Returns `{"in": [...], "out": [...]}` in modern mode. With `COMPATIBILITY_MODE`, it returns the legacy argument-name list. |
| `/docs` | GET | Swagger UI | Open the interactive API docs in a browser. |
| `/metrics` | GET | Prometheus metrics | Exposes request counters, latency histogram, and in-progress gauge. |
| `/` | GET | Convenience redirect | Redirects to the docs view for the model endpoint. |

## REST request contract

- Request keys must match `model_args_names` from the active server settings, or `chainer.in` when `model_args_names` is empty.
- Every provided list must have the same batch length.
- Empty requests and empty arrays are rejected with HTTP 400.
- Missing arguments may be filled with `None` only after batch-size validation.
- Response order follows the model's `Chainer` output order in modern mode.

## Socket start

```bash
python -m deeppavlov risesocket <config_path> [-d] [--socket-type TCP|UNIX] [-p <port>] [--socket-file <unix_socket_file>]
```

- `--socket-type TCP` uses an INET socket; `--socket-type UNIX` uses a Unix-domain socket file.
- `-p` applies to TCP sockets.
- `--socket-file` applies to Unix-domain sockets.
- The server prints the resolved host/port or socket-file binding address.

## Socket frame contract

- Payload keys follow the same `model_args_names` / `chainer.in` rule as REST.
- A socket request is `4 header bytes + JSON body bytes`.
- The header is a little-endian unsigned integer (`<I`) containing the JSON body byte length.
- DeepPavlov's public helper signature is `deeppavlov.utils.socket.encode(data: Any) -> bytes`.
- Response frames use the same header/body format. The decoded body is `{"status": "OK", "payload": ...}` on success, or an error string in `status` with `payload: null`.
- Use [the bundled smoke script](../scripts/socket_payload_smoke.py) to inspect the frame format locally without starting a server.

## Payload patterns

- Single-input models: `{"x": ["text"]}`
- Two-input QA or retrieval-style models: `{"context_raw": ["..."], "question_raw": ["..."]}`

## Operational notes

- CORS allows all origins, methods, and headers for REST.
- `COMPATIBILITY_MODE` is a temporary REST legacy bridge only; prefer modern REST clients.
- If a task is about request shaping, start here and then use the socket or service-configuration references as needed.
