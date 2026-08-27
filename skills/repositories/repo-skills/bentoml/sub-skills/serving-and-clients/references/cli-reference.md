# Serving CLI Reference

## HTTP Serve

`bentoml serve` starts an HTTP BentoServer. The first positional argument defaults to `.` and can be:

- A source import target for a service, such as `service.py:Summarization` or `service:svc`.
- A Bento tag in the local Bento store, such as `fraud_detector:latest`.
- A directory containing a valid `bentofile.yaml` with a `service` field.
- A built Bento directory for internal/debug use.

Common flags:

| Flag | Use |
| --- | --- |
| `--development` | Run in development mode; for modern services this passes `development_mode=True`, and for legacy services forces one API worker. |
| `--production` | Deprecated flag; production behavior is the default. |
| `-p`, `--port` | HTTP port. Also reads `BENTOML_PORT`. |
| `--host` | HTTP bind host. Also reads `BENTOML_HOST`. |
| `--api-workers` | Number of API server workers; defaults to available CPU cores in production mode. Also reads `BENTOML_API_WORKERS`. |
| `--timeout` | API server and runner timeout in seconds. Also reads `BENTOML_TIMEOUT`. |
| `--backlog` | Maximum pending connections. Hidden but supported. |
| `--reload` | Restart when code or model-store changes are detected. |
| `--working-dir` | Directory used to find and import the service target. |
| `--ssl-certfile`, `--ssl-keyfile`, `--ssl-keyfile-password`, `--ssl-version`, `--ssl-cert-reqs`, `--ssl-ca-certs`, `--ssl-ciphers` | HTTP TLS settings. Hidden but supported. |
| `--timeout-keep-alive`, `--timeout-graceful-shutdown` | HTTP server connection/shutdown tuning. Hidden but supported. |
| `--arg`, `--arg-file` | Template/build arguments accepted through BentoML’s shared argument option. |
| `--env conda` | Run with the selected BentoML environment manager when available from the shared env option. |

Recommended development pattern:

```bash
bentoml serve service.py:Summarization --working-dir . --development --reload --port 3000
```

Recommended non-current-directory pattern:

```bash
bentoml serve src/my_project/service.py:Classifier --working-dir src/my_project --port 3001
```

## gRPC Serve

`bentoml serve-grpc` starts a gRPC BentoServer. It is hidden in the CLI but implemented for local serving.

Common flags:

| Flag | Use |
| --- | --- |
| `--development` | Run in development mode; use this for local testing and Windows compatibility. |
| `-p`, `--port` | gRPC port. Also reads `BENTOML_PORT`. |
| `--host` | gRPC bind host. Also reads `BENTOML_HOST`. |
| `--api-workers` | Number of API server workers. Also reads `BENTOML_API_WORKERS`. |
| `--reload` | Restart on code or model-store changes. |
| `--backlog` | Maximum pending connections. |
| `--working-dir` | Directory used to find and import the service target. |
| `--enable-reflection` | Enable server reflection. |
| `--enable-channelz` | Enable gRPC Channelz. |
| `--max-concurrent-streams` | Limit concurrent incoming streams on an HTTP/2 connection. |
| `--ssl-certfile`, `--ssl-keyfile`, `--ssl-ca-certs` | gRPC TLS settings. |
| `-pv`, `--protocol-version` | Select generated stub protocol version, `v1` or `v1alpha1`. |

Example:

```bash
bentoml serve-grpc service.py:Summarization --working-dir . --development --port 3000 --enable-reflection
```

## Python `bentoml.serve`

The public serving API accepts a service/Bento target and starts a local server. Verified signature highlights:

```python
bentoml.serve(
    bento,
    server_type="http",
    reload=False,
    production=True,
    env=None,
    host=None,
    port=None,
    working_dir=".",
    api_workers=None,
    backlog=None,
    enable_reflection=None,
    enable_channelz=None,
    max_concurrent_streams=None,
    grpc_protocol_version=None,
    blocking=False,
    args=None,
)
```

Use it as a context manager in local tests or short scripts so the subprocess is cleaned up:

```python
import bentoml

with bentoml.serve("service.py:svc", port=3000, working_dir=".") as server:
    print(server.url)
```

Do not use the helper scripts in this sub-skill to start long-running servers by default; they intentionally dry-run or inspect an already running URL.
