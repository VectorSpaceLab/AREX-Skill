# LitServe cross-cutting troubleshooting

Use this page for issues that affect multiple LitServe workflows. For OpenAI
chat/embedding issues, use `sub-skills/openai-specs`. For MCP tool exposure,
use `sub-skills/mcp`. For general server workflows, use `sub-skills/server-basics`.

## Import or install failure

Symptoms:
- `ModuleNotFoundError: No module named 'litserve'`
- `ImportError` while importing `litserve` from a new environment
- `python -m pip check` reports conflicts

Fixes:
- Install the base package with `pip install litserve`.
- Re-run `python -m pip check`.
- Confirm the interpreter is the one you expect with `python -I -c "import sys; print(sys.executable)"`.

## Optional dependency missing

Symptoms:
- `fastmcp` import or MCP constructor failure
- `Pillow` import failure in image helpers
- Multipart or form parsing failure
- `openai` client examples or ASGI client demos fail to import

Fixes:
- Install only the missing workflow package, not the whole dev stack.
- Keep the server environment aligned with the chosen sub-skill.

## CLI and Docker issues

Symptoms:
- `litserve --help` or `litserve dockerize --help` fails
- `Dockerfile` generation raises `FileNotFoundError`
- `client.py` already exists and is not regenerated

Fixes:
- Ensure the server file you pass to `litserve dockerize` exists in the current
  working directory.
- Run the command from a directory containing the server entry file.
- Delete or rename an existing `client.py` if you want a new client file.

## Route and path validation

Symptoms:
- `api_path must start with '/'`
- `healthcheck_path` or `info_path` must start with `/`
- Route collisions between multiple APIs
- `ValueError: middlewares must be a list of tuples`

Fixes:
- Use explicit leading slashes in every route-like path.
- Do not reuse reserved internal paths such as `/health` or `/info` for model routes.
- Pass middlewares as a list, even when there is only one item.

## Payload, auth, and worker readiness

Symptoms:
- HTTP 413 payload errors
- 401 or 403 authentication failures
- 503 `not ready` from health checks
- request timeout or workers failing during startup

Fixes:
- Install `python-multipart` for multipart files.
- Verify the auth header expected by the route.
- Move heavy initialization into `setup(device)`.
- Reduce to `accelerator="cpu"`, `devices=1`, and `workers_per_device=1` when debugging startup.
- Check `timeout` and `batch_timeout` settings together.

## Excluded workflows

The following are intentionally out of scope for this generated skill tree and
should not be bundled into runtime guidance here:
- Torch/CUDA benchmark harnesses
- Throughput parity tests against FastAPI
- Transformer/vision benchmark reproduction
