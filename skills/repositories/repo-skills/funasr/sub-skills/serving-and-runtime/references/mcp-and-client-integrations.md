# MCP and client integrations

This reference covers the bundled stdio MCP helper and the client surfaces that normally consume the OpenAI-compatible HTTP API.

## Integration matrix

| Surface | Recommended entry | Why it fits |
|---|---|---|
| Python or JavaScript SDKs | `funasr-server` + OpenAI-compatible client | The simplest way to call `/v1/audio/transcriptions`. |
| Browser demos and no-code tools | OpenAI-compatible HTTP API | Gradio, Postman, OpenAPI imports, and workflow builders can all target the same HTTP route. |
| LangChain, Dify, AutoGen, CrewAI, Semantic Kernel | OpenAI-compatible HTTP API | These stacks already know how to speak the OpenAI audio surface. |
| Desktop voice input | Local browser/desktop integration | Useful when the transcript should land in the current app or clipboard. |
| Local agent tools | Bundled MCP helper | Best when an assistant needs a filesystem-backed transcription tool. |

## OpenAI-compatible client pattern

Any client that can set a base URL to `/v1` can call the server.

```python
from openai import OpenAI

client = OpenAI(base_url="http://127.0.0.1:8000/v1", api_key="x")
result = client.audio.transcriptions.create(
    model="sensevoice",
    file=open("sample.wav", "rb"),
    response_format="verbose_json",
)
print(result.text)
```

A browser app, Gradio demo, Postman request, or internal workflow builder should use the same route and model name the server exposes.

## MCP helper

Use [`scripts/funasr_mcp_server.py`](../scripts/funasr_mcp_server.py) when you want an agent-friendly local file transcription tool over stdio.

```bash
python scripts/funasr_mcp_server.py --model iic/SenseVoiceSmall --device cpu
```

The helper exposes one tool:

- `transcribe_audio` → transcribe a mounted local audio file and return transcript text, plus segment details when the backend provides them

### MCP constraints

- The tool only accepts local file paths that the helper process can see.
- URLs, microphone streams, and unmounted files are intentionally unsupported.
- The helper keeps stdout reserved for JSON-RPC traffic; logs belong on stderr.
- The default language can be set on the command line, and each tool call can override it.

## Desktop and voice-input integrations

The voice-input example path is a convenience integration for users who want speech pasted into the active desktop application.

Typical extra dependencies include:

- audio capture
- clipboard access
- hotkey handling
- the OpenAI Python client

Use it only when the user explicitly wants local desktop automation, because it can copy text to the clipboard and trigger paste behavior.

## Browser and workflow integrations

The OpenAI-compatible server is the right surface for:

- browser upload widgets
- OpenAPI import and API gateways
- Postman-style manual checks
- no-code workflow builders
- agent frameworks that expect an OpenAI audio client

When a browser or workflow tool needs a public or internal endpoint, prefer the packaged HTTP API instead of building a custom protocol shim.

## Routing reminders

- If the issue is realtime chunking or session control, use the WebSocket reference instead.
- If the issue is model family choice or vLLM behavior, route to `llm-asr-and-vllm`.
- If the issue is batch transcription or subtitles, route to `python-asr-pipelines`.
