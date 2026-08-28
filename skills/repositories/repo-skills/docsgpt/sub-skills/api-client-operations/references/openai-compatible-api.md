# OpenAI-Compatible API

## Setup

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:7091/v1",
    api_key="agent-api-key",
)
response = client.chat.completions.create(
    model="docsgpt-agent",
    messages=[{"role": "user", "content": "Summarize the policy"}],
)
print(response.choices[0].message.content)
```

The request `model` field is accepted but ignored; the API key selects the DocsGPT agent and its configured model.

## Supported behavior

- streaming and non-streaming Chat Completions;
- common sampling fields (`temperature`, token limits, `top_p`, penalties, `stop`, `seed`);
- JSON object or JSON Schema structured output through `response_format`, plus `response_schema` convenience;
- typed text/image user content;
- client-side tool calling;
- provider reasoning in non-standard `reasoning_content`;
- DocsGPT extension object for attachments/persistence and response metadata.

## Streaming

Standard content uses `choices[0].delta.content`. DocsGPT-specific sources/tool metadata appears on otherwise-empty chunks with a top-level `docsgpt` object so strict clients can ignore it.

## Client-side tool continuation

The flow is stateless unless a DocsGPT conversation id is explicitly managed:

1. send messages plus client tool definitions;
2. receive assistant `tool_calls` with `finish_reason="tool_calls"`;
3. execute tools client-side;
4. resend full history, including assistant tool-call message and `role="tool"` results;
5. receive final answer.

Do not omit the assistant tool-call message or tool-call ids.

## Idempotency

For non-streaming `/v1/chat/completions`, send a unique `Idempotency-Key`:

- completed key replays stored body/status for the retention window;
- an in-flight duplicate returns `409`;
- keys are agent-scoped and bounded in length;
- streaming replay is not supported.

Use one key per logical request, not one global key.

## System prompts and persistence

System messages are dropped by default in favor of the agent prompt. An agent can allow prompt override; when active, the system message replaces the template and template variables are not substituted.

`/v1` conversations persist hidden. Stateless tool continuations can skip persistence to avoid orphan rows; `docsgpt.persist` can override. Legacy save flags are ignored.

## Choose native instead when

You need native attachment upload, passthrough template variables, explicit conversation reuse, sidebar visibility, or the full native event taxonomy.
