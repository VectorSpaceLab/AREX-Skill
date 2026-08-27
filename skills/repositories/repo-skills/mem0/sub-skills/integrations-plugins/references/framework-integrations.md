# Framework Integrations

Use this reference when adding Mem0 to an application framework or agent framework rather than installing an editor plugin.

## Integration Pattern

Most framework integrations follow the same shape:

1. Identify a stable user/application/session scope.
2. Retrieve relevant memories before the model or agent turn.
3. Inject retrieved memories as system/context/tool output in the framework’s native format.
4. Generate or run the agent workflow normally.
5. Store the useful user/assistant interaction back to Mem0 with the same scope.
6. Handle memory errors as degraded context, not as a reason to crash the primary agent workflow unless the user explicitly requires strict memory guarantees.

For direct SDK method details, route to `../sdk-memory/SKILL.md`. For OSS provider/vector/LLM configuration, route to `../provider-configuration/SKILL.md`.

## Python Framework Baseline

The common hosted Platform baseline uses `MemoryClient`:

```python
from mem0 import MemoryClient

mem0 = MemoryClient()
user_id = "alice"

memories = mem0.search("current user request", filters={"user_id": user_id})
context = "\n".join(f"- {m['memory']}" for m in memories.get("results", []))

# Pass context into the framework's prompt/state/tool result here.

mem0.add(
    [
        {"role": "user", "content": "current user request"},
        {"role": "assistant", "content": "assistant response"},
    ],
    user_id=user_id,
)
```

Keep the framework’s own state, thread ID, tools, and callbacks intact. Mem0 should provide long-term context, not replace the framework’s short-term message state unless the integration package explicitly does that.

## LangChain

Typical pattern:

- Install `langchain`, `langchain_openai`, `mem0ai`, and `python-dotenv` as needed.
- Initialize `MemoryClient()` and the LangChain model.
- Search Mem0 with `filters={"user_id": user_id}` before invoking the chain.
- Insert serialized memories into a `SystemMessage`, prompt variable, or `MessagesPlaceholder` context.
- Store the user/assistant messages after the response.

LangChain tool integrations may wrap Mem0 operations as `StructuredTool` instances: add memory, search memory, and get all memories. When building tools, use Pydantic schemas that require scope and avoid ambiguous global deletes.

## LangGraph

Typical pattern:

- Add `mem0_user_id` or equivalent to the graph state.
- In the chatbot/node function, read the latest user message and search Mem0 using that scope.
- Prepend a `SystemMessage` containing relevant memory context before model invocation.
- Store the latest interaction after generation.
- Keep LangGraph thread/checkpointer config separate from Mem0 scope; a `thread_id` is not automatically a Mem0 `user_id`.

If multiple nodes write memories, use consistent metadata such as `app_id` and node/agent name to aid later filtering.

## LlamaIndex

LlamaIndex has a dedicated Mem0 memory integration package:

```bash
pip install llama-index-core llama-index-memory-mem0 python-dotenv
```

Hosted Platform setup:

```python
from llama_index.memory.mem0 import Mem0Memory

memory = Mem0Memory.from_client(
    context={"user_id": "alice"},
    search_msg_limit=4,
)
```

OSS setup uses `Mem0Memory.from_config(context=context, config=config, search_msg_limit=4)` with a Mem0 OSS config dictionary. Provider details belong to `../provider-configuration/SKILL.md`.

The LlamaIndex docs cover `SimpleChatEngine`, `FunctionCallingAgent`, `ReActAgent`, and multi-agent `AgentWorkflow` patterns. Shared multi-agent memory works by giving all agents the same Mem0 context.

## CrewAI

CrewAI can use Mem0 through its `memory_config`:

```python
from crewai import Crew, Process

crew = Crew(
    agents=agents,
    tasks=tasks,
    process=Process.sequential,
    memory=True,
    memory_config={"provider": "mem0", "config": {"user_id": "crew_user_1"}},
)
```

Store seed preferences or prior conversation with `MemoryClient.add(...)` when the workflow needs known context before kickoff. Keep external tools such as Serper separate from Mem0; do not store API keys or raw tool credentials in memory metadata.

## OpenAI Agents SDK

The recommended pattern is memory as agent tools:

- `search_memory(query, user_id)` calls `MemoryClient.search(query, filters={"user_id": user_id}, top_k=...)` and returns a compact string.
- `save_memory(content, user_id)` calls `MemoryClient.add(...)`.
- Specialized agents can share the same memory tools and same user scope through handoffs.
- Store final handoff output once per user turn to avoid duplicate writes.

Make the `user_id` explicit in tool schemas or inject it from trusted application state instead of letting the model invent it.

## Google ADK

Google ADK can integrate Mem0 by implementing a `BaseMemoryService`:

- `search_memory(app_name, user_id, query)` calls Mem0 search with user and app filters, then returns ADK `MemoryEntry` objects.
- `add_session_to_memory(session)` converts session events into user/assistant messages and calls `MemoryClient.add`.
- An after-agent callback calls `callback_context.add_session_to_memory()`.
- ADK’s built-in `load_memory` tool can then retrieve Mem0-backed context.

Use async wrappers such as `asyncio.to_thread` when calling the synchronous Python client from async ADK methods.

## Agno

Agno supports a simple tool-based path:

```python
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.tools.mem0 import Mem0Tools

agent = Agent(
    name="Memory Agent",
    model=OpenAIChat(id="gpt-5-mini"),
    tools=[Mem0Tools()],
)
```

Manual paths use `MemoryClient` directly, including multimodal messages such as `image_url` content. Keep image file reading and base64 conversion inside trusted application code; store only intended memory facts.

## AutoGen

AutoGen examples use `MemoryClient` outside the agent:

- Store prior conversation with `memory_client.add(messages=conversation, user_id=USER_ID)`.
- Search with `memory_client.search(question, filters={"user_id": USER_ID})`.
- Inject memory text into a prompt sent to `ConversableAgent.generate_reply`.
- For multi-agent setups, share the same `MemoryClient` and `USER_ID` across agents, optionally adding agent metadata.

## Multi-Agent Scoping Guidance

- Use one stable `user_id` for the human or tenant.
- Use `app_id` for the product, repository, classroom, or workspace.
- Use `agent_id` for individual specialized agents when their memories should be distinguishable.
- Use `run_id` for ephemeral session recall.
- For shared memory across agents, keep `user_id` and `app_id` consistent and vary `agent_id` only when filtering by agent is useful.

## Framework Troubleshooting Quick Checks

- Empty context: verify the write and search paths use the same `user_id`/`app_id` and that search reads `results` from the returned object.
- Duplicated memories: check whether both framework-native memory and Mem0 writes are storing the same content every turn.
- Slow turns: lower `top_k`, use shorter serialized context, or retrieve only on user turns where memory matters.
- Tool hallucinated user IDs: derive scope from application auth/session state and hide scope parameters from model-visible tools when possible.
- Async errors: use async clients or thread off synchronous SDK calls instead of blocking an event loop.
