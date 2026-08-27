# Reasoning Parsers in vLLM

Reasoning parsers extract model reasoning traces into a separate `reasoning` field while leaving the final answer in `content`. Use them for reasoning models that emit hidden/thinking tags or model-specific reasoning formats.

## Server Setup

Start serving with a parser that matches the model family:

```bash
vllm serve <reasoning-model> --reasoning-parser <parser-name>
```

Example:

```bash
vllm serve deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B \
  --reasoning-parser deepseek_r1
```

Then request through Chat Completions:

```python
response = client.chat.completions.create(
    model=model,
    messages=[{"role": "user", "content": "9.11 and 9.8, which is greater?"}],
)
print("reasoning:", response.choices[0].message.reasoning)
print("content:", response.choices[0].message.content)
```

The `reasoning` field replaced older `reasoning_content` naming. Prefer `message.reasoning` and `delta.reasoning`.

## Registered Reasoning Parser IDs

Registered parser IDs include:

| Parser | Typical model family |
| --- | --- |
| `deepseek_r1` | DeepSeek R1 and QwQ-style reasoning |
| `deepseek_v3`, `deepseek_v4` | DeepSeek V3/V4 reasoning variants |
| `qwen3` | Qwen3 reasoning |
| `mimo` | Qwen3-engine Mimo parser |
| `gemma4` | Gemma 4 reasoning |
| `granite` | IBM Granite reasoning |
| `holo2` | Holo2 reasoning |
| `hunyuan_a13b` | Hunyuan A13B reasoning |
| `cohere_command3`, `cohere_command4` | Cohere Command reasoning |
| `glm45`, `glm47` | GLM 4.5/4.7 reasoning |
| `openai_gptoss` | GPT-OSS reasoning format |
| `kimi_k2`, `minimax_m2`, `minimax_m2_append_think`, `minimax_m3`, `mistral`, `nemotron_v3`, `olmo3`, `seed_oss`, `step3`, `step3p5`, `poolside_v1`, `ernie45`, `hy_v3` | Model-family parsers present in vLLM |

Use exact parser IDs. A wrong parser often produces absent `reasoning`, content containing raw thinking tags, or malformed streaming transitions.

## Streaming Reasoning

Streaming chat completions expose reasoning in the chunk delta:

```python
stream = client.chat.completions.create(
    model=model,
    messages=[{"role": "user", "content": "9.11 and 9.8, which is greater?"}],
    stream=True,
)

reasoning_parts = []
content_parts = []
for chunk in stream:
    delta = chunk.choices[0].delta
    reasoning = getattr(delta, "reasoning", None) or None
    content = getattr(delta, "content", None) or None
    if reasoning is not None:
        reasoning_parts.append(reasoning)
    if content is not None:
        content_parts.append(content)

print("reasoning:", "".join(reasoning_parts))
print("content:", "".join(content_parts))
```

OpenAI Python client versions may not type `reasoning` as a first-class streaming attribute, so use `getattr` rather than direct attribute access.

## Reasoning with Tool Calling

Tool calling can be enabled together with reasoning when the model/parser combination supports it:

```bash
vllm serve Qwen/QwQ-32B \
  --reasoning-parser deepseek_r1 \
  --enable-auto-tool-choice \
  --tool-call-parser hermes
```

Important behavior:

- Tool parsing extracts tool calls from the final `content`, not from `reasoning`.
- In streaming, collect `delta.reasoning` separately from `delta.tool_calls`.
- Reasoning plus tool calls needs both parser families to match the model's output format.
- Some model families support reasoning but not tool calling; check the model-family parser notes before promising both.

Streaming extractor pattern:

```python
reasoning = []
tool_calls = {}
for chunk in chunks:
    delta = chunk.choices[0].delta
    if getattr(delta, "reasoning", None):
        reasoning.append(delta.reasoning)
    for call in delta.tool_calls or []:
        key = call.id or str(call.index)
        state = tool_calls.setdefault(key, {"name": "", "arguments": ""})
        if call.function and call.function.name:
            state["name"] = call.function.name
        if call.function and call.function.arguments:
            state["arguments"] += call.function.arguments
```

## Reasoning with Structured Outputs

Structured outputs can be used with reasoning models. The server must parse reasoning separately so the structured-output backend constrains the final answer rather than thinking text. For Qwen3 Coder reasoning mode, enable structured outputs in reasoning mode when needed:

```bash
vllm serve <model> \
  --reasoning-parser qwen3 \
  --structured-outputs-config.enable_in_reasoning=True
```

If JSON/regex constraints appear to be ignored when reasoning is enabled, check whether reasoning text is still mixed into `content` and whether the selected parser provides structured-output support for that model.

## Thinking Controls

Some model families require chat template kwargs to enable or disable thinking:

- Qwen3 reasoning is enabled by default; disable with `extra_body={"chat_template_kwargs": {"enable_thinking": False}}` or server default kwargs.
- Granite 3.2 and DeepSeek-V3.1 reasoning can require `thinking=True` in `chat_template_kwargs`.
- Gemma 4 reasoning can require `enable_thinking=True` or a non-`none` `reasoning_effort`.
- Holo2 reasoning is enabled by default and can be disabled with `thinking=False`.

Server-level defaults:

```bash
vllm serve Qwen/Qwen3-8B \
  --reasoning-parser qwen3 \
  --default-chat-template-kwargs '{"enable_thinking": false}'
```

Request-level kwargs override server defaults:

```python
response = client.chat.completions.create(
    model=model,
    messages=messages,
    extra_body={"chat_template_kwargs": {"enable_thinking": True}},
)
```

`reasoning_effort` can automatically enable thinking for model templates that use `enable_thinking`:

```python
response = client.chat.completions.create(
    model=model,
    messages=[{"role": "user", "content": "What is 15 * 37?"}],
    reasoning_effort="high",
)
```

## Thinking Token Budget

`thinking_token_budget` is a sampling/request parameter that limits reasoning tokens for supported models. Token counting starts at the configured reasoning start marker; when the budget is reached, vLLM forces the configured reasoning end string.

Serving example:

```bash
vllm serve Qwen/Qwen3-0.6B \
  --reasoning-parser qwen3 \
  --reasoning-config '{"reasoning_start_str": "<think>", "reasoning_end_str": "I have to give the solution based on the reasoning directly now.</think>"}'
```

Request example:

```json
{
  "model": "Qwen/Qwen3-0.6B",
  "messages": [{"role": "user", "content": "9.11 and 9.8, which is greater?"}],
  "thinking_token_budget": 10
}
```

Offline example:

```python
from vllm import LLM, SamplingParams
from vllm.config import ReasoningConfig

llm = LLM(
    model="Qwen/Qwen3-0.6B",
    reasoning_config=ReasoningConfig(
        reasoning_start_str="<think>",
        reasoning_end_str="</think>",
    ),
)
outputs = llm.chat(
    [{"role": "user", "content": "9.11 and 9.8, which is greater?"}],
    sampling_params=SamplingParams(thinking_token_budget=10),
)
```

## Limitations

- Reasoning content is available for online serving Chat Completions, Anthropic Messages, and Responses API surfaces.
- Reasoning extraction depends on model-specific markers and parser support; arbitrary instruct models will not expose `reasoning` just because `--reasoning-parser` is set.
- CPU/precompiled inspection can confirm signatures and CLI help, but model-backed reasoning behavior requires a suitable model and runtime hardware.

## Quick Checks

- Parser ID matches the model family exactly.
- The model actually emits reasoning tokens or has thinking enabled by template kwargs.
- Client code uses `message.reasoning` or `getattr(delta, "reasoning", None)`.
- Tool-call code parses functions from `content`/`tool_calls`, not from reasoning.
- Structured-output code uses a reasoning-compatible parser/backend path when constraining final content.
