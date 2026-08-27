# Agent And Workflow Recipes

These recipes assume `llama-index-core` and `llama-index-workflows` are installed and importable. They intentionally avoid provider-specific API keys; plug in a compatible LLM object from the integration sub-skill when running against a real model.

## Choose The Right Interface

| Need | Use | Why |
| --- | --- | --- |
| One-shot retrieval over indexed data | query engine | Lower latency, fewer moving parts. |
| Multi-turn conversation over indexed data | chat engine | Maintains conversational history around one data source. |
| LLM must choose deterministic functions | `FunctionAgent` | Uses native tool/function calling and tool schemas. |
| LLM lacks native function calling | `ReActAgent` | Prompts the LLM to emit `Thought`/`Action`/`Answer` text. |
| Agent should decide when to retrieve | `QueryEngineTool` in an agent | Retrieval becomes one selectable tool. |
| Multiple specialist agents | `AgentWorkflow` | Built-in handoff, state, memory, event stream. |
| Centralized routing with specialists | orchestrator agent with sub-agent tools | All control returns to one planner. |
| Custom event graph | `Workflow`, `Event`, `@step` | Use when agent abstractions are too high-level. |

## FunctionTool With Explicit Metadata

Use explicit metadata whenever a model chooses the wrong tool or passes malformed arguments.

```python
from typing import Annotated
from llama_index.core.tools import FunctionTool


def lookup_order(
    order_id: Annotated[str, "External order id, such as ORD-1234"],
) -> str:
    """Look up fulfillment status for a single order id."""
    return "shipped"

order_tool = FunctionTool.from_defaults(
    fn=lookup_order,
    name="lookup_order_status",
    description=(
        "Use only for checking one order's fulfillment status. "
        "Do not use for refund policy, shipping policy, or account questions."
    ),
    return_direct=False,
)
print(order_tool.metadata.get_parameters_dict())
```

Checklist:

- Name tools with verbs and domain nouns, not generic names.
- Add `Annotated` argument descriptions for ambiguous strings, IDs, or enums.
- Keep return values concise; large outputs should be summarized, indexed, or split behind a retrieval tool.
- Use `return_direct=True` only for trusted terminal outputs.

## Convert A RAG Query Engine Into An Agent Tool

Build or load the index/query engine with the indexing sub-skill, then wrap it here.

```python
from llama_index.core.agent.workflow import FunctionAgent
from llama_index.core.tools import QueryEngineTool

# Built elsewhere:
# query_engine = index.as_query_engine(similarity_top_k=4)

kb_tool = QueryEngineTool.from_defaults(
    query_engine=query_engine,
    name="handbook_search",
    description=(
        "Answer employee handbook questions. Input must be a complete question "
        "about benefits, leave, expenses, conduct, or escalation policy."
    ),
    return_direct=False,
    resolve_input_errors=True,
)

agent = FunctionAgent(
    name="hr_support",
    description="Answers HR questions using handbook retrieval and safe calculations.",
    system_prompt=(
        "Use handbook_search for policy facts. If the handbook does not contain "
        "the answer, say what is missing instead of guessing."
    ),
    tools=[kb_tool],
    llm=llm,
    streaming=False,
)
```

Debug the wrapped tool independently before adding it to an agent:

```python
print(kb_tool.metadata.name)
print(kb_tool.metadata.description)
print(kb_tool.call(input="What is the parental leave policy?"))
```

## FunctionAgent With Streaming Events

```python
from llama_index.core.agent.workflow import FunctionAgent
from llama_index.core.agent.workflow import AgentStream, ToolCall, ToolCallResult

agent = FunctionAgent(
    name="assistant",
    description="Uses tools to answer operational questions.",
    tools=[status_tool],
    llm=llm,
    streaming=True,
)

handler = agent.run(user_msg="Check the status and summarize it.", max_iterations=8)
async for event in handler.stream_events():
    if isinstance(event, AgentStream):
        print(event.delta, end="")
    elif isinstance(event, ToolCall):
        print(f"\nCalling {event.tool_name}: {event.tool_kwargs}")
    elif isinstance(event, ToolCallResult):
        print(f"\n{event.tool_name} returned error={event.tool_output.is_error}")

result = await handler
print(str(result.response))
```

If the provider errors on streaming, instantiate the agent with `streaming=False`. If tool calls loop forever, lower `max_iterations` during debugging and inspect `ToolCallResult` outputs.

## ReActAgent For Non-Function-Calling Models

```python
from llama_index.core.agent.workflow import ReActAgent
from llama_index.core.tools import FunctionTool

agent = ReActAgent(
    name="calculator",
    description="Performs simple arithmetic with tools.",
    system_prompt="Always use tools for arithmetic. Finish with a concise Answer.",
    tools=[FunctionTool.from_defaults(fn=add), FunctionTool.from_defaults(fn=subtract)],
    llm=llm,
    streaming=False,
)
response = await agent.run(user_msg="What is 7 plus 23?")
```

ReAct failures usually mean the LLM emitted text outside the expected format. The built-in workflow sends retry messages for empty output and parser errors, but you should still tighten the system prompt and tool descriptions.

## Multi-Agent Handoff

```python
from llama_index.core.agent.workflow import AgentWorkflow, FunctionAgent

support = FunctionAgent(
    name="support",
    description="Triage support requests and answer general questions.",
    system_prompt="Route product documentation questions to docs. Route billing math to billing.",
    can_handoff_to=["docs", "billing"],
    llm=llm,
)
docs = FunctionAgent(
    name="docs",
    description="Answers product documentation questions using documentation retrieval.",
    tools=[docs_tool],
    can_handoff_to=["support"],
    llm=llm,
)
billing = FunctionAgent(
    name="billing",
    description="Computes invoices, discounts, and refunds with billing tools.",
    tools=[invoice_tool, refund_tool],
    can_handoff_to=["support"],
    llm=llm,
)

workflow = AgentWorkflow(
    agents=[support, docs, billing],
    root_agent="support",
    initial_state={"case_id": "demo", "handoff_notes": []},
    timeout=120,
    early_stopping_method="generate",
)
handler = workflow.run(user_msg="Find the API limit and compute the pro-rated refund.")
async for event in handler.stream_events():
    name = getattr(event, "current_agent_name", None)
    if name:
        print(f"[{name}] {type(event).__name__}")
result = await handler
```

Handoff routing depends on agent names, descriptions, `can_handoff_to`, and each agent's system prompt. If the wrong agent handles a task, make the root agent's routing policy explicit and constrain `can_handoff_to` rather than relying on open-ended handoff.

## Orchestrator Agent With Sub-Agents As Tools

Use this when handoff is too autonomous and you need the orchestrator to decide every step.

```python
from llama_index.core.agent.workflow import FunctionAgent
from llama_index.core.workflow import Context

async def call_docs_agent(ctx: Context, question: str) -> str:
    """Ask the docs specialist a product documentation question."""
    result = await docs_agent.run(user_msg=question)
    state = await ctx.store.get("state", default={})
    state.setdefault("docs_answers", []).append(str(result))
    await ctx.store.set("state", state)
    return str(result)

orchestrator = FunctionAgent(
    name="orchestrator",
    description="Plans which specialist agent or tool should handle each step.",
    system_prompt="Call specialist tools as needed. Do not answer from memory when a specialist is available.",
    tools=[call_docs_agent, call_billing_agent],
    initial_state={"docs_answers": []},
    llm=llm,
)
```

A `Context` parameter is automatically injected into a `FunctionTool` during workflow execution, so it should not appear in the generated tool schema.

## Chat Engine Routing

```python
chat_engine = index.as_chat_engine()
response = chat_engine.chat("Summarize the last answer with one more detail.")

streaming_response = chat_engine.stream_chat("Explain this step by step.")
for token in streaming_response.response_gen:
    print(token, end="")
```

Use a chat engine directly when the application is a conversation with one indexed corpus. Wrap a query engine as a tool when the chat system must choose among retrieval, calculators, APIs, handoff, or other capabilities.

## Human-In-The-Loop Tool

```python
from llama_index.core.workflow import Context, InputRequiredEvent, HumanResponseEvent

async def request_approval(ctx: Context, action: str) -> str:
    """Ask a human to approve a sensitive action before continuing."""
    response = await ctx.wait_for_event(
        HumanResponseEvent,
        waiter_id=f"approve:{action}",
        waiter_event=InputRequiredEvent(prefix=f"Approve {action}? "),
    )
    return "approved" if response.response.strip().lower() == "yes" else "denied"
```

When running, watch for `InputRequiredEvent` from `handler.stream_events()` and respond with `handler.ctx.send_event(HumanResponseEvent(...))`.
