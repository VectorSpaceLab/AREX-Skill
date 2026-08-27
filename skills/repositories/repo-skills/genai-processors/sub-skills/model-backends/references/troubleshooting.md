# Model backend troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `KeyError: GOOGLE_API_KEY` while importing an example | example helper reads the variable at import time | set a real key before running or a dummy value only for import-level inspection |
| `GenaiModel` produces no memory of prior turns | turn-based model wrapper is stateless | pass full conversation history or use `realtime.LiveProcessor` / Live API |
| Function calls do not execute | model-side automatic function calling consumed them, or `fns` mismatch | set `automatic_function_calling.disable=True` and pass the same callable/session list to `FunctionCalling` |
| Async tools block the conversation | `is_bidi_model` not set or tool implemented sync | use async functions and `FunctionCalling(..., is_bidi_model=True)` for realtime behavior |
| Live API connection fails | non-Live model name, missing key, API version mismatch, or service issue | choose a Live-capable model name and verify API key/http options |
| `OllamaModel` connection error | Ollama service not running or model not pulled | run `ollama serve`, `ollama pull <model>`, and confirm host/port |
| `transformers` says PyTorch was not found | `transformers` package installed without `torch` | install CPU or GPU-compatible PyTorch before actual `TransformersModel` inference |
| LangChain wrapper emits only text | tool/structured output translation is intentionally limited | use `FunctionCalling` with GenAI Processor callables for portable tool execution |
| MCP tool raises `McpToolError` | remote/local MCP tool returned an error payload | inspect the MCP tool result content; validate args and server trust/auth |
| OpenRouter request fails | missing/invalid API key, model name, base URL, or network issue | verify `api_key`, `model_name`, optional `base_url`, and HTTP status details |

## Token and network safety

Importing wrappers and inspecting signatures is safe. Constructing clients may
be safe but can still validate credentials in some third-party libraries.
Calling a processor against real content may spend tokens, hit quotas, download
models, or contact external services. Ask before running any non-smoke model
call in automation.

## Tool schema safety

Provide clear Python type annotations and docstrings for callable tools. The
schema is inferred from the function signature and docstring. Arguments and
return values should be JSON-compatible, unless returning a `ProcessorPart` or
SDK `FunctionResponse` intentionally.

## Realtime triggers

`realtime.AudioTriggerMode.FINAL_TRANSCRIPTION` is usually better for text-only
turn processors because the final transcript is available. `END_OF_SPEECH` is
lower latency for audio-capable turn processors. Choosing the wrong trigger can
make responses late or prompt the model without the expected transcription.
