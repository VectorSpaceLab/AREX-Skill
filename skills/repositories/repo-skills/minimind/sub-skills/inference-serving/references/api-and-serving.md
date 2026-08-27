# OpenAI-compatible API and serving reference

MiniMind serving evidence exposed a lightweight OpenAI-compatible `/v1/chat/completions` endpoint with extra thinking and tool-call behavior. This reference describes the contract so future agents can build clients or probes without reading source files.

## Runtime dependencies

Server-side dependencies:

```bash
python -m pip install fastapi uvicorn pydantic torch transformers
```

Client-side dependency for the bundled helper:

```bash
python -m pip install openai
```

FastAPI and Uvicorn are required by the lightweight server path and were absent from the requirements evidence. Streamlit is required only for WebUI-style usage.

## Endpoint

```text
POST /v1/chat/completions
Content-Type: application/json
```

The server evidence listened on port `8998`. Bind to `127.0.0.1` for local-only use unless the deployment has explicit authentication and network controls.

## Request schema

| Field | Type | Required | Default evidence | Meaning |
| --- | --- | --- | --- | --- |
| `model` | string | yes | any model identifier accepted | Required by OpenAI-compatible clients; lightweight MiniMind server may not use it for model selection. |
| `messages` | list | yes | none | OpenAI-style chat messages. Roles: `system`, `user`, `assistant`, `tool`. |
| `temperature` | number | no | `0.7` | Sampling temperature. |
| `top_p` | number | no | `0.92` | Nucleus sampling threshold. |
| `max_tokens` | integer | no | `8192` | Maximum generated tokens, not guaranteed context capability. |
| `stream` | boolean | no | `true` | Enables server-sent streaming chunks. |
| `tools` | list | no | `[]` | OpenAI-compatible function schemas passed into the tokenizer chat template. |
| `open_thinking` | boolean | no | `false` | Top-level MiniMind thinking switch. |
| `chat_template_kwargs` | object or null | no | `null` | Extra template kwargs; `open_thinking` or `enable_thinking` set here also enables thinking. |

Thinking can be enabled in either of these forms:

```json
{"open_thinking": true}
```

```json
{"chat_template_kwargs": {"open_thinking": true}}
```

The OpenAI Python SDK sends MiniMind-specific fields through `extra_body`:

```python
response = client.chat.completions.create(
    model="minimind",
    messages=[{"role": "user", "content": "Who are you?"}],
    max_tokens=256,
    extra_body={"chat_template_kwargs": {"open_thinking": True}},
)
```

## Message and tool schemas

Tool schema follows OpenAI function-calling shape:

```json
[
  {
    "type": "function",
    "function": {
      "name": "calculate_math",
      "description": "Calculate a simple arithmetic expression.",
      "parameters": {
        "type": "object",
        "properties": {
          "expression": {"type": "string", "description": "Expression such as 256 * 37"}
        },
        "required": ["expression"]
      }
    }
  }
]
```

MiniMind's tokenizer template expands tools and tool observations into text tags:

```text
<tool_call>{"name": "calculate_math", "arguments": {"expression": "256 * 37"}}</tool_call>
<tool_response>{"result": "9472"}</tool_response>
```

When calling the API after a tool execution, append messages in OpenAI-compatible form:

```json
[
  {"role": "user", "content": "Calculate 256 * 37."},
  {
    "role": "assistant",
    "content": "",
    "tool_calls": [
      {
        "id": "call_0",
        "type": "function",
        "function": {"name": "calculate_math", "arguments": "{\"expression\": \"256 * 37\"}"}
      }
    ]
  },
  {"role": "tool", "tool_call_id": "call_0", "content": "{\"result\": \"9472\"}"}
]
```

For local text-template loops, a tool observation may also be represented as a `tool` role message whose content is the JSON observation; the tokenizer template wraps it in `<tool_response>...</tool_response>`.

## Non-streaming response schema

Successful non-streaming responses use this shape:

```json
{
  "id": "chatcmpl-<timestamp>",
  "object": "chat.completion",
  "created": 1760000000,
  "model": "minimind",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "Visible final answer",
        "reasoning_content": "Optional extracted thinking text",
        "tool_calls": [
          {
            "id": "call_<timestamp>_0",
            "type": "function",
            "function": {
              "name": "calculate_math",
              "arguments": "{\"expression\": \"256 * 37\"}"
            }
          }
        ]
      },
      "finish_reason": "tool_calls"
    }
  ]
}
```

`reasoning_content` appears only when `<think>` text is extracted. `tool_calls` appears only when valid `<tool_call>...</tool_call>` JSON is parsed. `finish_reason` is `tool_calls` when tool calls exist, otherwise `stop`.

## Streaming response behavior

Streaming responses are server-sent events:

```text
data: {"choices": [{"delta": {"content": "..."}}]}

```

Chunk types:

| Delta field | When emitted | Notes |
| --- | --- | --- |
| `reasoning_content` | While `open_thinking=true` and before the first `</think>` | The stream splits thinking from visible answer. |
| `content` | After thinking ends, or immediately when thinking is disabled | Client should append in order. |
| `tool_calls` | After generation completes and valid tool tags are parsed | Tool calls are not streamed token-by-token in the lightweight server evidence. |
| empty delta + `finish_reason` | Final chunk | `finish_reason` is `tool_calls` or `stop`. |

The lightweight streaming evidence did not require a literal `data: [DONE]` terminator. Clients that depend on `[DONE]` may need adapter handling.

## Parser behavior for thinking and tools

The server parser behavior was:

1. If text contains `<think>...</think>`, extract the inside text as `reasoning_content`, strip it, and remove the entire think block from `content`.
2. Else, if text contains `</think>` without a recognized opening tag, treat text before the first `</think>` as `reasoning_content` and the text after it as `content`.
3. Parse each `<tool_call>...</tool_call>` block in the remaining text as JSON.
4. Convert each valid call to OpenAI style:

```json
{
  "id": "call_<timestamp>_<index>",
  "type": "function",
  "function": {
    "name": "<name>",
    "arguments": "<JSON string of arguments>"
  }
}
```

5. Invalid tool-call JSON is ignored by the lightweight parser. Use `scripts/toolcall_smoke.py` when you need explicit invalid-call diagnostics.
6. If one or more valid tool calls were found, remove `<tool_call>...</tool_call>` blocks from visible `content`.

Smoke this behavior locally:

```bash
python scripts/toolcall_smoke.py \
  --text '<think>need a calculator</think><tool_call>{"name":"calculate_math","arguments":{"expression":"256*37"}}</tool_call>' \
  --execute \
  --json
```

## One-shot client usage

Non-streaming probe:

```bash
python scripts/openai_chat_once.py \
  --base-url http://127.0.0.1:8998/v1 \
  --model minimind \
  --prompt "Say hello in English." \
  --max-tokens 64 \
  --no-stream
```

Streaming + thinking probe:

```bash
python scripts/openai_chat_once.py \
  --base-url http://127.0.0.1:8998/v1 \
  --model minimind \
  --prompt "Explain photosynthesis briefly." \
  --open-thinking \
  --stream
```

Tool-schema probe:

```bash
cat > tools.json <<'JSON'
[
  {
    "type": "function",
    "function": {
      "name": "calculate_math",
      "description": "Calculate arithmetic.",
      "parameters": {
        "type": "object",
        "properties": {"expression": {"type": "string"}},
        "required": ["expression"]
      }
    }
  }
]
JSON

python scripts/openai_chat_once.py \
  --base-url http://127.0.0.1:8998/v1 \
  --model minimind \
  --prompt "Use a tool to calculate 256 * 37." \
  --tools-json tools.json \
  --no-stream
```

The helper prints a JSON summary containing `content`, `reasoning_content`, `tool_calls`, and `finish_reason`.

## Server startup recipes

### Transformers-format model

Use a small explicit server wrapper that loads `AutoTokenizer` and `AutoModelForCausalLM` from `MODEL_DIR`, applies `tokenizer.apply_chat_template(...)`, and exposes `/v1/chat/completions` with the schema above.

Important runtime choices:

- Use `trust_remote_code=True` for MiniMind custom-format Transformers exports.
- Prefer Qwen3-compatible export if the server must run without MiniMind custom code.
- Bind `127.0.0.1` for local development.
- Cap `max_tokens` and request body size for shared systems.

### Raw checkpoint model

Raw server startup must additionally provide:

| Field | Example |
| --- | --- |
| tokenizer directory | `TOKENIZER_DIR` |
| weights directory | `WEIGHTS_DIR` |
| weight prefix | `full_sft` |
| hidden size | `768` |
| layer count | `8` |
| MoE flag | `false` or `true` |
| optional LoRA prefix | `lora_identity` |

Raw serving is easier to misconfigure than Transformers serving. Validate with `scripts/check_model_artifacts.py` and consider export first.

## WebUI serving notes

A Streamlit UI around MiniMind should be treated as an interactive client, not as the primary server:

- It should load only explicit user-selected Transformers-format model directories.
- It needs `streamlit`, `torch`, and `transformers`.
- It should expose controls for history turns, max generation length, temperature, thinking, language, and up to four tools.
- It should show `reasoning_content` or `<think>` text separately from visible answer text.
- It should render tool calls and tool observations distinctly.
- It should enforce a loop cap for repeated tool calls.

## Serving validation checklist

Before declaring a MiniMind server usable:

1. `scripts/check_model_artifacts.py` succeeds for the selected artifact.
2. A no-thinking non-streaming one-shot chat returns `choices[0].message.content`.
3. A thinking request returns either `reasoning_content` or a clean direct answer without parser errors.
4. A tool-schema request returns either `tool_calls` or plain content; if tool JSON is malformed, `scripts/toolcall_smoke.py` explains the malformed block.
5. Streaming clients receive content chunks and terminate cleanly without waiting forever for `[DONE]`.
6. Device and dtype are explicit; CPU fallback does not force unsupported half-precision ops.
