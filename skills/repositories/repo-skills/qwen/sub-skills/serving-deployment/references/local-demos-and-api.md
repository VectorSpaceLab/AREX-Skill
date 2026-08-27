# Local Demos and OpenAI-compatible API

## CLI chat demo

The CLI demo is the lightest interactive route. Its useful flags are:

```bash
python cli_demo.py --checkpoint-path /path/to/Qwen-7B-Chat --seed 1234
python cli_demo.py -c Qwen/Qwen-7B-Chat --cpu-only
```

Interactive commands include `:help`/`:h`, `:exit`/`:quit`/`:q`, `:clear`, `:clear-his`, `:history`, `:seed`, `:conf key=value`, and `:reset-conf`. The demo streams with `model.chat_stream`; it loads the checkpoint at startup, so do not run it for a mere parser check.

## Gradio web demo

The web demo uses the web dependency group and exposes a browser UI:

```bash
pip install -r requirements_web_demo.txt
python web_demo.py -c /path/to/Qwen-7B-Chat --server-name 127.0.0.1 --server-port 8000
```

Important flags:

- `--cpu-only`: compatibility only; expect slow generation.
- `--share`: creates a public Gradio link. Use only when the user accepts exposure.
- `--inbrowser`: opens a browser tab.
- `--server-name 0.0.0.0`: exposes on all interfaces; use only deliberately.

## Repository OpenAI-compatible API server

The API server exposes `/v1/models` and `/v1/chat/completions` through FastAPI/Uvicorn:

```bash
pip install fastapi uvicorn "openai<1.0" pydantic sse_starlette
python openai_api.py -c /path/to/Qwen-7B-Chat --server-name 127.0.0.1 --server-port 8000
```

Useful flags:

- `--api-auth username:password` adds BasicAuth middleware.
- `--cpu-only` loads with `device_map='cpu'`.
- `--disable-gc` skips per-response garbage collection.
- `--server-name` defaults to loopback; `0.0.0.0` exposes the service.

The server's `ChatCompletionRequest` accepts `model`, `messages`, optional `functions`, `temperature`, `top_p`, `top_k`, `max_length`, `stream`, and `stop`. It maps OpenAI-style function calling to Qwen ReAct text. Function calling is supported only when `stream=False`; the server rejects `stream=True` with functions.

## API client shape

```python
import openai
openai.api_base = "http://localhost:8000/v1"
openai.api_key = "none"

response = openai.ChatCompletion.create(
    model="Qwen",
    messages=[{"role": "user", "content": "你好"}],
    stream=False,
)
print(response.choices[0].message.content)
```

For `functions`, read `../prompting-tool-use-tokenization/references/function-calling-and-react.md` because the server converts tools into ReAct prompts and has strict message ordering.

## Dry-run helper

Use the bundled advisor instead of running the source scripts while planning:

```bash
python scripts/qwen_launch_advisor.py --mode openai-api --checkpoint /models/Qwen-7B-Chat --port 8000 --auth user:pass
python scripts/qwen_launch_advisor.py --mode web --checkpoint Qwen/Qwen-7B-Chat --server-name 127.0.0.1
```
