# OpenAI-compatible API Reference

## Endpoints

- `GET /v1/models`
- `POST /v1/completions`
- `POST /v1/chat/completions`
- `POST /v1/embeddings`
- model load/unload endpoints when explicit model management is enabled

These endpoints are OpenAI-compatible enough for the OpenAI Python client, but the backend behavior is the selected Triton LLM model/backend.

## Chat request shape

```json
{
  "model": "llama-3.1-8b-instruct",
  "messages": [{"role": "user", "content": "Say this is a test"}],
  "max_tokens": 64,
  "stream": false
}
```

## Completion request shape

```json
{
  "model": "llama-3.1-8b-instruct",
  "prompt": "Machine learning is",
  "max_tokens": 64
}
```

## LoRA and tool calling

- If `--lora-separator` is configured, a LoRA adapter can be selected by appending the separator and LoRA name to the model name.
- Tool calling requires a supported tool-call parser and careful output-size limits.
- Streaming tool-call parsing uses `--max-tool-call-parse-bytes` to avoid unbounded memory growth.

## Request builder

Use `scripts/build_openai_request.py` to print request JSON without contacting a live frontend.
