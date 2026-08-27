# Agent Core Workflows

## 1) Quickstart agent

Use this pattern when you need the smallest useful Atomic Agent:

```python
import instructor
from openai import OpenAI
from pydantic import Field
from atomic_agents import AtomicAgent, AgentConfig, BaseIOSchema
from atomic_agents.context import ChatHistory, SystemPromptGenerator

class InputSchema(BaseIOSchema):
    """User input for the agent."""
    message: str = Field(..., description="User message")

class OutputSchema(BaseIOSchema):
    """Agent response."""
    reply: str = Field(..., description="Response text")

client = instructor.from_openai(OpenAI())
agent = AtomicAgent[InputSchema, OutputSchema](
    AgentConfig(client=client, model="gpt-5-mini", history=ChatHistory())
)
result = agent.run(InputSchema(message="Hello"))
```

Use this for:

- basic chatbots
- structured prompt/response contracts
- first-pass provider integration

## 2) Streaming and async

- Use `run_stream()` when the client is synchronous and you want partial structured chunks.
- Use `run_async()` / `run_async_stream()` only with `AsyncInstructor` clients.
- Keep sync and async client types aligned; the agent asserts on the wrong combination.

## 3) Memory and custom history backends

- Use `ChatHistory` for in-memory conversation state.
- Implement `BaseChatHistory` directly or subclass `ChatHistory` when you need persistence.
- Override `copy()` on custom backends so `reset_history()` preserves the backend type and state.
- Use `delete_turn_id()` to remove complete turns, not individual messages.

## 4) Context providers and prompt shaping

- Build prompt sections through `SystemPromptGenerator(background=..., steps=..., output_instructions=...)`.
- Register a `BaseDynamicContextProvider` for runtime info that should be injected into the system prompt.
- Use `get_context_provider()` when a downstream task needs to inspect a registered provider.

## 5) Token counting and context trimming

- Call `get_context_token_count()` when you need the exact prompt + history + schema/tool overhead.
- Set `max_context_tokens` in `AgentConfig` when you need automatic turn trimming.
- The agent trims whole turns from the oldest to newest order and raises if a single turn alone exceeds the cap.

## 6) Multimodal content

- `ChatHistory` serializes images, audio, PDFs, and `VideoURL` content parts into provider-ready message payloads.
- Keep multimodal content inside `BaseIOSchema` fields so the serializer can extract it recursively.
- Use the `VideoURL.to_openai()` helper if you need to supply video content.

## 7) Hooks and debugging

- Register Instructor hooks with `register_hook(event, handler)`.
- Typical events include parse errors, completion kwargs, completion responses, and token-counted events.
- Use hooks for logging, retries, and fine-grained monitoring rather than for business logic.

## 8) Common input / output patterns

- One input field such as `message` or `query` is enough for a simple start.
- Add output fields for confidence, suggested follow-ups, or structured analysis when the downstream task benefits from typed responses.
- Keep field descriptions explicit; they feed the schema and prompt.
