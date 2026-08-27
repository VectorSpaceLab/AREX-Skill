# Tool Calling in vLLM

vLLM supports OpenAI-compatible named function calling, `tool_choice` values `auto`, `required`, and `none`, parser-specific automatic tool extraction, and streaming tool-call deltas. Tool calling is request-driven, but automatic tool choice also needs server flags and a parser/template combination compatible with the selected model.

## Minimal Request Shape

A Chat Completions request defines `tools` and `tool_choice`:

```python
from openai import OpenAI
import json

client = OpenAI(base_url="http://localhost:8000/v1", api_key="dummy")
model = client.models.list().data[0].id

tools = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get the current weather in a city",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {"type": "string"},
                    "unit": {"type": "string", "enum": ["celsius", "fahrenheit"]},
                },
                "required": ["location", "unit"],
                "additionalProperties": False,
            },
        },
    }
]

response = client.chat.completions.create(
    model=model,
    messages=[{"role": "user", "content": "Weather in San Francisco?"}],
    tools=tools,
    tool_choice="auto",
)

if response.choices[0].message.tool_calls:
    call = response.choices[0].message.tool_calls[0].function
    args = json.loads(call.arguments)
    print(call.name, args)
```

vLLM returns tool-call names and JSON argument strings. The caller must validate arguments, dispatch to local application functions, handle errors, and append follow-up `tool` messages if continuing the conversation.

## Server Flags for Automatic Tool Choice

For `tool_choice="auto"`, start serving with:

```bash
vllm serve <model> \
  --enable-auto-tool-choice \
  --tool-call-parser <parser-name> \
  --chat-template <template-or-tool_use-if-needed>
```

Flag meanings:

- `--enable-auto-tool-choice`: required for the model to decide when to call a tool automatically.
- `--tool-call-parser`: selects the model-family parser used to extract tool calls.
- `--tool-parser-plugin`: optional plugin file for custom parsers.
- `--chat-template`: optional but often necessary; use a template compatible with tool-role messages and assistant tool calls. Some models include a tool template in tokenizer config; `--chat-template tool_use` can select that when available.

Named function calling and `tool_choice="required"` use structured outputs to constrain arguments and are supported by default for compatible schemas. Automatic tool calling needs a parser/template/model that emits a parseable tool-call format.

## `tool_choice` Modes

- Named function: `{"type": "function", "function": {"name": "get_weather"}}`; uses structured outputs to force arguments for that tool. First use may incur finite-state-machine/schema compilation latency.
- `"required"`: model must produce one or more tool calls from the provided tool list; uses structured outputs for schema-constrained arguments.
- `"auto"`: model chooses whether to call tools; requires `--enable-auto-tool-choice` and a selected parser.
- `"none"`: no tool calls should be produced. If tools are still included in prompts by default, use server option `--exclude-tools-when-tool-choice-none` when the tool definitions should be omitted.

## Strict Tool Schemas

For `tool_choice="auto"`, schema-level constraints require both default strict enforcement and at least one tool with `strict: true` when the parser supports structural tags. Without strict structural tags, vLLM extracts tool calls from raw text and arguments can be malformed.

Recommended strict schema style:

```json
{
  "type": "function",
  "function": {
    "name": "search",
    "description": "Search documents",
    "strict": true,
    "parameters": {
      "type": "object",
      "properties": {
        "query": {"type": "string"},
        "limit": {"type": ["integer", "null"]}
      },
      "required": ["query", "limit"],
      "additionalProperties": false
    }
  }
}
```

Rules:

- Set `additionalProperties: false` on each object.
- Mark all fields in `properties` as required.
- Represent optional values with nullable types.
- Keep schemas compatible with the structured-output backend.
- `VLLM_ENFORCE_STRICT_TOOL_CALLING=false` disables structural-tag strict tool calling; it does not disable named/required schema-derived structured outputs.

## Parser Names and Model Families

Registered parser IDs include:

| Parser | Typical use |
| --- | --- |
| `hermes` | Hermes and Qwen2.5/QwQ-style Hermes tool format |
| `mistral` | Mistral function-calling models |
| `llama3_json` | Llama 3.1/3.2 JSON tool calling |
| `llama4_pythonic` | Llama 4 pythonic tool calling |
| `pythonic` | Models that emit Python-call/list syntax |
| `xlam` | Salesforce xLAM models and multiple JSON/tag/code-block formats |
| `granite`, `granite4`, `granite-20b-fc` | IBM Granite tool formats |
| `deepseek_v3`, `deepseek_v31`, `deepseek_v32`, `deepseek_v4` | DeepSeek tool formats |
| `openai` | OpenAI GPT-OSS tool format |
| `qwen3_coder`, `qwen3_xml` | Qwen3 Coder tool formats |
| `cohere_command3`, `cohere_command4` | Cohere Command tool formats; may need extra package support |
| `hunyuan_a13b`, `kimi_k2`, `minimax_m2`, `minimax_m3`, `olmo3`, `seed_oss`, `step3`, `step3p5`, `glm45`, `glm47`, `gemma4`, `functiongemma`, `gigachat3`, `apertus`, `longcat`, `jamba`, `internlm`, `lfm2`, `minicpm5`, `phi4_mini_json`, `poolside_v1`, `hy_v3` | Model-family parsers present in vLLM |

Use the parser name exactly as registered. A parser mismatch can yield plain content instead of `tool_calls`, empty calls, malformed arguments, or server startup errors.

## Chat Template Selection

A tool parser only extracts output; the chat template teaches the model how tools are presented and how prior tool calls/messages are serialized.

Common patterns:

```bash
# Llama 3 JSON-style tool calls need a Llama JSON tool template.
vllm serve meta-llama/Llama-3.1-8B-Instruct \
  --enable-auto-tool-choice \
  --tool-call-parser llama3_json \
  --chat-template <llama3-json-tool-template>

# xLAM examples use xLAM parser with the model's compatible template.
vllm serve Salesforce/Llama-xLAM-2-8B-fc-r \
  --enable-auto-tool-choice \
  --tool-call-parser xlam

# Hunyuan reasoning + tools use matching parser pair.
vllm serve tencent/Hunyuan-A13B-Instruct \
  --enable-auto-tool-choice \
  --tool-call-parser hunyuan_a13b \
  --reasoning-parser hunyuan_a13b
```

Because generated skills must be self-contained, do not instruct future agents to rely on original example-template paths. If a deployment needs a custom template, ask the user for the template file or copy/adapt it into that deployment's own configuration.

## Streaming Tool Calls

Streaming responses deliver incremental `delta.tool_calls`; do not treat a single chunk as a complete function call. Accumulate by tool-call ID or index, concatenate `function.arguments`, and parse JSON only after the stream finishes or after the parser indicates the full call is complete.

Safe streaming assembly pattern:

```python
tool_calls = {}
for chunk in stream:
    delta_calls = chunk.choices[0].delta.tool_calls or []
    for piece in delta_calls:
        key = piece.id or str(piece.index)
        state = tool_calls.setdefault(key, {"name": None, "arguments": ""})
        if piece.function and piece.function.name:
            state["name"] = piece.function.name
        if piece.function and piece.function.arguments:
            state["arguments"] += piece.function.arguments

for state in tool_calls.values():
    if state["name"] and state["arguments"]:
        args = json.loads(state["arguments"])
```

Source parser utilities show special handling for required and named tool streaming, including partial JSON parsing and deltas where `function.name` appears once and later chunks contain only argument text. Therefore:

- Do not require every chunk to contain `id`, `name`, and valid JSON.
- Preserve tool-call `index` for parallel calls.
- Keep text `content` and `tool_calls` paths separate.
- For reasoning plus tool calls, collect `delta.reasoning` separately from `delta.tool_calls`.

## Responses API and Anthropic Notes

Tool schema concepts also apply to Responses and Anthropic-style messages where vLLM exposes compatible surfaces. The same strict schema guidance applies, but request field names can differ. When converting a Chat Completions request to Responses, keep the function schema, tool choice, and response text format aligned.

## Quick Triage: No Tool Calls

1. Confirm the server was started with `--enable-auto-tool-choice` for `tool_choice="auto"`.
2. Confirm `--tool-call-parser` exactly matches a registered parser and the model family.
3. Confirm the chat template supports tools and prior `tool` messages.
4. Check whether `tool_choice="none"` or a system prompt discourages tool use.
5. Try named function calling to separate schema/backend problems from model choice behavior.
6. Add `strict: true` and strict schema style if arguments are malformed under auto mode.
7. For streaming, inspect accumulated chunks rather than the first chunk only.

## Native Verification Candidates

Useful native candidate classes from vLLM evidence include tool parser entrypoint tests, parser streaming tests, and OpenAI-compatible tool calling examples. Treat them as final verification candidates only after the whole runtime skill is integrated and the user has a suitable model/server environment.
