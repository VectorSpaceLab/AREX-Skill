# Build, Test, and CI

## Typical commands

```bash
make build
make lint
make format
uv run pytest
uv run pytest tests/sdk/
uv run pytest tests/tools/
uv run pytest tests/workspace/
uv run pytest tests/agent_server/
uv run pytest tests/cross/
uv run pytest tests/examples/test_examples.py --collect-only
uv run pre-commit run --files <changed-file>
```

## What to check first

- Which package or top-level area changed.
- Whether the change is source, tests, examples, scripts, or CI.
- Whether the change crosses package boundaries.
- Whether the change touches public APIs, settings, REST routes, or tool names.

## Example selection guidance

- `tests/sdk/` for core SDK behavior.
- `tests/tools/` for built-in tools and registry behavior.
- `tests/workspace/` for workspace backends.
- `tests/agent_server/` for server routes and deferred init.
- `tests/cross/` for end-to-end behavior and compatibility gates.

## Examples runner

`tests/examples/test_examples.py --run-examples` executes repo examples. Examples that run successfully must print an `EXAMPLE_COST:` line.
