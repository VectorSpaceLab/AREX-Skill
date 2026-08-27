# Local Serving Workflows

## When to read

Read this for step-by-step recipes that turn a model tag into a local chat server or terminal chat session.

## Workflow: start a browser chat server

1. Choose a model tag that exists in the selected repository, for example `llama3.2:1b`.
2. If the model is gated, set `HF_TOKEN` before starting the server.
3. Run:

```bash
openllm serve llama3.2:1b
```

4. Open the browser chat UI at `http://localhost:3000/chat` or the port you selected.
5. If you need to pass runtime values into the Bento, use `--env` and `--arg`.

## Workflow: terminal chat loop

```bash
openllm run llama3:8b
```

- OpenLLM starts a temporary server on a high port when `--port` is omitted.
- The terminal loop waits for server readiness and then streams chat completions through an OpenAI-compatible client.
- Press `Ctrl+C` to stop the chat loop.

## Workflow: interactive `hello`

```bash
openllm hello
```

This route is useful when you want OpenLLM to:

- inspect the local machine's accelerators,
- list available Bentos,
- compare runnable versus non-runnable choices,
- and propose `run`, `serve`, or `deploy` actions.

## OpenAI client recipe

When a local server is already running, client code can point at `http://localhost:3000/v1`.

```python
from openai import OpenAI
client = OpenAI(base_url="http://localhost:3000/v1", api_key="na")
```

Use the returned model id from the server when the client needs the exact Bento name.

## Common failure patterns

- No model found: update or inspect the configured repo catalog in `model-repositories`.
- Server never becomes ready: check the server logs, port binding, required envs, and whether the model weights or dependencies are still downloading.
- Resource warning: pick a smaller model or use the cloud deployment route instead.
