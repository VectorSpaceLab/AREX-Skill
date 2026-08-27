---
name: agents-and-workflows
description: "Build LlamaIndex agents and workflows with tools, memory, chat
  engines, multi-agent handoff, streaming, and structured output routing."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# LlamaIndex Agents And Workflows

Use this sub-skill when the task is to build an agentic LlamaIndex application: `FunctionAgent`, `ReActAgent`, `AgentWorkflow`, function/query-engine tools, memory-aware chat, handoff, event streaming, or agent-as-tool orchestration.

## Route First

- Use `FunctionAgent` when the configured LLM supports function/tool calling; it calls `llm.achat_with_tools()` or `llm.astream_chat_with_tools()` and raises `ValueError("LLM must be a FunctionCallingLLM")` if the model metadata is not function-calling capable.
- Use `ReActAgent` when the LLM does not expose native tool-calling but can follow the ReAct text format; its parser expects `Thought`, `Action`, `Action Input`, or final `Answer` blocks.
- Use `QueryEngineTool` when retrieval already exists as a query engine; create/query/index construction belongs in `../indexing-and-querying/SKILL.md`, then wrap the resulting query engine here.
- Use chat engines for conversational RAG over one index (`index.as_chat_engine()`, `chat()`, `stream_chat()`); use agents when the application must choose tools, hand off, call multiple systems, or route between capabilities.
- Route Pydantic schemas, output parser customization, and detailed structured-output validation to `../customization-and-structured-outputs/SKILL.md`; route provider installs and vector-store packages to `../integrations-and-storage/SKILL.md`.

## Core Agent Pattern

1. Define small, deterministic Python functions with typed parameters and docstrings that describe when to use the tool and what each argument means.
2. Convert functions explicitly with `FunctionTool.from_defaults(...)` when you need `name`, `description`, `return_direct`, callbacks, `partial_params`, or schema inspection; otherwise `FunctionAgent(tools=[callable])` auto-converts callables.
3. Build `FunctionAgent(name=..., description=..., system_prompt=..., tools=[...], llm=..., streaming=True)` for function-calling models; set `streaming=False` if the provider fails on streaming.
4. Call `handler = agent.run(user_msg="...")`, consume `async for event in handler.stream_events(): ...` when progress, tool calls, or streaming deltas matter, then `response = await handler`.
5. Pass memory per run with `memory=ChatMemoryBuffer.from_defaults(...)` or `memory=Memory(token_limit=..., token_flush_size=...)` when chat state must survive a run.

```python
from llama_index.core.agent.workflow import FunctionAgent
from llama_index.core.tools import FunctionTool


def calculate_discount(price: float, percent: float) -> str:
    """Calculate a discount for a product price. Args: price: Original price. percent: Discount percentage from 0 to 100."""
    return f"{price * (1 - percent / 100):.2f}"

agent = FunctionAgent(
    name="pricing_agent",
    description="Answers pricing questions using deterministic pricing tools.",
    system_prompt="Use tools for arithmetic; explain the result briefly.",
    tools=[FunctionTool.from_defaults(fn=calculate_discount)],
    llm=llm,
    streaming=False,
)
response = await agent.run(user_msg="What is 15% off 49.99?")
```

## RAG As A Tool

Wrap a query engine with `QueryEngineTool.from_defaults(query_engine, name=..., description=...)` when an agent should decide whether retrieval is needed. Give the tool a domain-specific name and description; vague names like `query_engine_tool` make routing unreliable.

```python
from llama_index.core.agent.workflow import FunctionAgent
from llama_index.core.tools import QueryEngineTool

policy_tool = QueryEngineTool.from_defaults(
    query_engine=policy_query_engine,
    name="policy_knowledge_base",
    description=(
        "Answer questions about internal support policies. Input should be a full "
        "natural-language policy question, not keywords."
    ),
    return_direct=False,
)
agent = FunctionAgent(
    name="support_agent",
    description="Uses policy retrieval and deterministic tools to answer support questions.",
    tools=[policy_tool],
    llm=llm,
)
```

Use `return_direct=True` when the raw tool response should end the loop, such as a trusted retrieval answer or status lookup. Keep it `False` when the agent must synthesize, compare tools, or ask a follow-up.

## Multi-Agent Handoff

Use `AgentWorkflow` when multiple specialists should hand off control. Every agent in a multi-agent workflow needs a unique `name` and useful `description`; `root_agent` is required when more than one agent is supplied. Use `can_handoff_to` to constrain routing and improve debuggability.

```python
from llama_index.core.agent.workflow import AgentWorkflow, FunctionAgent

triage = FunctionAgent(
    name="triage",
    description="Classifies requests and hands technical questions to docs.",
    system_prompt="If the question requires documentation lookup, hand off to docs.",
    can_handoff_to=["docs"],
    llm=llm,
)
docs = FunctionAgent(
    name="docs",
    description="Answers documentation questions using the docs knowledge base.",
    tools=[docs_query_tool],
    can_handoff_to=["triage"],
    llm=llm,
)
workflow = AgentWorkflow(
    agents=[triage, docs],
    root_agent="triage",
    initial_state={"handoffs": []},
    timeout=120,
)
handler = workflow.run(user_msg="Which retention policy applies to archived tickets?")
async for event in handler.stream_events():
    print(type(event).__name__, getattr(event, "current_agent_name", ""))
result = await handler
```

For stricter orchestration, expose sub-agent `run()` calls as tools on a top-level `FunctionAgent` instead of enabling peer handoff. This keeps all control flow returning to the orchestrator.

## Memory And Chat Engines

- Default agent runs use `ChatMemoryBuffer`; pass your own `ChatMemoryBuffer.from_defaults(token_limit=...)` when token budgets are known.
- Use `Memory(token_limit=30000, token_flush_size=3000, memory_blocks=[...])` when short-term history should waterfall into longer-lived blocks; keep `token_flush_size` smaller than `token_limit`.
- Use `index.as_chat_engine()` for stateful conversation over one data source, `chat_engine.chat(...)` for normal response, and `chat_engine.stream_chat(...)` plus `response_gen` for token streaming.
- If a chat engine only needs a standalone answer, prefer a query engine; if it needs tool choice or handoff, wrap its query engine as a tool and use an agent.

## Streaming And Events

Agent workflows are workflows: `run()` returns a handler that can be awaited and can stream events. Look for `AgentInput`, `AgentStream`, `ToolCall`, `ToolCallResult`, `AgentOutput`, and handoff-induced changes to `current_agent_name`. If a stream appears incomplete, always drain `handler.stream_events()` before awaiting the final handler in examples and tests.

For human-in-the-loop tools, accept `ctx: Context` in the tool signature and call `ctx.wait_for_event(...)`. `FunctionTool` detects a `Context` parameter and injects the active workflow context automatically.

## Use The Bundled Script

Start from `scripts/agent_tool_skeleton.py` for local, no-network tool and agent scaffolding:

```bash
python sub-skills/agents-and-workflows/scripts/agent_tool_skeleton.py --help
python sub-skills/agents-and-workflows/scripts/agent_tool_skeleton.py --print-code
```

The script prints safe templates for `FunctionTool`, `QueryEngineTool`, `FunctionAgent`, `ReActAgent`, streaming events, and multi-agent handoff. It does not call an LLM or network by default.

## References

- `references/agent-workflow-recipes.md` for copyable recipes and routing decisions.
- `references/api-reference.md` for high-value constructors, fields, events, and imports.
- `references/troubleshooting.md` for common failure modes and recovery steps.
