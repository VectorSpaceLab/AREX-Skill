# Local Serving CLI Reference

## When to read

Read this when you need the exact `openllm serve`, `openllm run`, or `openllm hello` flags before constructing a command.

## Verified command surface

### `openllm serve MODEL[:VERSION]`

- `MODEL[:VERSION]` is required.
- `--repo REPO_ALIAS` selects a configured model repository.
- `--port PORT` defaults to `3000`.
- `--verbose` increases output verbosity.
- `--env NAME` or `--env NAME=value` forwards environment variables to the BentoML serve command.
- `--arg key=value` forwards Bento arguments.

### `openllm run [MODEL[:VERSION]]`

- `MODEL[:VERSION]` is optional but commonly provided.
- `--repo REPO_ALIAS` selects a configured model repository.
- `--port PORT` is optional; OpenLLM will choose a random high port when omitted.
- `--timeout SECONDS` defaults to `600`.
- `--verbose`, `--env`, and `--arg` behave like `serve`.

### `openllm hello`

- Interactive starter that detects the local machine, lists available Bentos, and lets a user choose an action.
- Supports `--context`, `--env`, and `--arg` when the final action is deploy.

## Operational details

- `serve` and `run` call `ensure_bento` before starting a server.
- The selected Bento is then served with `bentoml serve <bento-tag>` through OpenLLM's internal helpers.
- `serve` prints the browser chat URL on the selected port.
- `run` starts a chat loop against the local OpenAI-compatible endpoint and exits on `KeyboardInterrupt`.

## Safe command planning

Use the bundled `scripts/build_serve_command.py` helper when you need to validate how a request would be turned into an OpenLLM command without starting the model server.
