# CLI and service troubleshooting

## `agl` executable not found

**Cause**

The package is not installed into the active Python environment or the console-script directory is not on `PATH`.

**Fix**

```bash
python -m pip install --upgrade agentlightning
python -m pip show agentlightning
```

Then rerun `agl --help`. For source-only inspection without installing entry points, import Python APIs directly.

## CLI subcommand crashes on import

**Cause**

Subcommands import optional modules lazily. A base package environment can show a command in top-level help but lack a subcommand dependency.

**Fix**

- Run the subcommand with `--help` first.
- Install only the optional dependency group needed for that subcommand.
- Treat `vllm`, GPU, Mongo, and hosted integrations as optional unless requested.

## FastAPI/LiteLLM import mismatch

**Symptom**

```text
ImportError: cannot import name 'get_flat_dependant' from 'fastapi.dependencies.utils'
```

**Cause**

The installed FastAPI version is incompatible with the LiteLLM proxy module imported by Agent Lightning.

**Fix**

Install a lockfile-compatible FastAPI release and rerun:

```bash
python -m pip check
python - <<'PY'
import agentlightning as agl
print(agl.__version__)
PY
agl --help
```

## `agl prometheus` says `PROMETHEUS_MULTIPROC_DIR is not set`

**Cause**

The exporter serves the Prometheus multiprocess registry and requires a directory.

**Fix**

```bash
export PROMETHEUS_MULTIPROC_DIR="$(mktemp -d)"
agl prometheus --host 127.0.0.1 --port 4748
```

For a short local metrics smoke, run `python scripts/check_prometheus_metrics.py --duration 1 --host 127.0.0.1`.

## `No module named 'prometheus_client'`

**Cause**

The Prometheus client package is not installed.

**Fix**

Install `prometheus-client` or the repository's dev dependency group, then rerun `agl prometheus --help`.

## Port already in use

**Cause**

Another store, proxy, metrics server, or unrelated process is bound to the same port.

**Fix**

- Use `--port` to choose a different port.
- Bind `--host 127.0.0.1` for local-only tests.
- Stop only processes the user authorizes you to stop.

## Mongo backend fails

**Symptoms**

- missing `pymongo`,
- connection refused,
- replica-set errors.

**Fix**

- Use `--backend memory` unless persistence is required.
- Install the `mongo` extra and provision a MongoDB replica set before using `--backend mongo`.
- Do not run Docker setup without explicit user permission.

## LLM endpoint check fails

**Symptoms**

- `/models` returns an error,
- chat completion fails,
- unknown model,
- authentication error,
- timeout.

**Fix**

1. Verify the base URL ends at the OpenAI-compatible root, usually `/v1`.
2. Pass the exact model name exposed by the service.
3. Use an explicit API key or a documented dummy key for local unauthenticated services.
4. Re-run with `--list-models` before `--chat`.
5. Do not print or log secrets.

## Missing token IDs/logprobs

**Cause**

The OpenAI-compatible backend may not support these fields, or the proxy did not request them.

**Fix**

- Verify backend support, especially vLLM version.
- Inspect proxy spans with the tracing sub-skill.
- If training requires token IDs and the backend cannot provide them, stop and explain that the workflow cannot be fully verified.
