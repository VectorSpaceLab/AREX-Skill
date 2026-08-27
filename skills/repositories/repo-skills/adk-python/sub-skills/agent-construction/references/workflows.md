# Agent Construction Workflows

Use these recipes to build ADK Python agents in a self-contained way. They assume `google-adk` 2.3.0, Python 3.10+, and import root `google.adk`.

## Minimal Python Agent

Create an importable module that exports `root_agent`.

```python
from google.adk import Agent

root_agent = Agent(
    name="assistant",
    model="gemini-3.5-flash",
    instruction="You are a concise assistant. Ask before taking irreversible actions.",
)
```

Checks:

- `name` is an identifier and not `user`.
- `model` is explicit when reproducibility matters.
- `instruction` describes behavior; do not place system text in `generate_content_config.system_instruction`.
- The module can be imported without making network calls.

## Sample App Layout

For Python agent apps, a simple layout is:

```text
my_agent_app/
  __init__.py
  agent.py
```

`__init__.py` should import the agent module so app discovery can load it:

```python
from . import agent
```

`agent.py` should define `root_agent = Agent(...)`. Keep tool implementations importable and side-effect-light. CLI discovery and YAML config details route to `cli-configuration-deployment`.

## Add A Function Tool

```python
from google.adk import Agent


def lookup_order(order_id: str) -> dict[str, str]:
  """Look up a demo order by ID."""
  return {"order_id": order_id, "status": "processing"}

root_agent = Agent(
    name="orders",
    instruction="Use tools to answer order questions.",
    tools=[lookup_order],
)
```

Guidance:

- Give tools docstrings; ADK uses them as descriptions.
- Type parameters and return values when possible.
- Add `ToolContext` only for runtime context needs; ADK hides/injects it.
- If confirmation, auth, toolsets, MCP, OpenAPI, or cloud tools are involved, route deeper work to `tools-and-integrations`.

## Add Generation Settings Safely

```python
from google.adk import Agent
from google.genai import types

root_agent = Agent(
    name="creative_writer",
    model="gemini-3.5-flash",
    instruction="Draft short creative prose.",
    generate_content_config=types.GenerateContentConfig(
        temperature=0.7,
    ),
)
```

Do not put these fields in `generate_content_config` for `LlmAgent`:

- `tools`: use `tools=[...]`.
- `system_instruction`: use `instruction` or `static_instruction`.
- `response_schema`: use `output_schema`.

This is the most common fix for invalid `GenerateContentConfig` errors.

## Add Callbacks

```python
from typing import Any

from google.adk import Agent
from google.adk.agents.callback_context import CallbackContext
from google.adk.models.llm_request import LlmRequest
from google.adk.models.llm_response import LlmResponse
from google.adk.tools import BaseTool, ToolContext
from google.genai import types


def before_model_callback(
    callback_context: CallbackContext,
    llm_request: LlmRequest,
) -> LlmResponse | None:
  if llm_request.contents and llm_request.contents[-1].parts:
    text = llm_request.contents[-1].parts[-1].text or ""
    if text.strip().lower() == "ping":
      return LlmResponse(
          content=types.Content(
              role="model",
              parts=[types.Part.from_text(text="pong")],
          )
      )
  return None


def on_tool_error_callback(
    tool: BaseTool,
    args: dict[str, Any],
    tool_context: ToolContext,
    error: Exception,
) -> dict[str, str] | None:
  return {"error": f"{tool.name} failed: {error}"}

root_agent = Agent(
    name="callback_agent",
    instruction="Use callbacks for safe interception.",
    before_model_callback=before_model_callback,
    on_tool_error_callback=on_tool_error_callback,
)
```

Callback rules:

- Return `None` to continue normal execution.
- Return a response object/dict only when intentionally overriding behavior.
- Plugin callbacks run before agent callbacks.
- Callback lists run in list order until one returns a non-`None` value.
- `after_tool_callback` receives the original tool response and may replace it.
- `on_tool_error_callback` must return a dict to convert an exception into a function response; returning `None` propagates the error.

## Structured Output With `output_schema` And `output_key`

```python
from google.adk import Agent
from pydantic import BaseModel, Field


class Summary(BaseModel):
  answer: str = Field(description="Direct answer to the user")
  confidence: float = Field(ge=0, le=1)

root_agent = Agent(
    name="structured_agent",
    instruction="Return only JSON matching the schema.",
    output_schema=Summary,
    output_key="last_summary",
)
```

Behavior:

- `output_schema` validates the final model response.
- `output_key` saves the final authored output into session state.
- With a schema, the saved value is parsed structured data instead of raw text.
- ADK 2.3.0 supports `output_schema` and tools together by allowing tools during the reasoning loop and enforcing structure on the final response.
- If the model emits non-JSON final text when a schema is expected, guide it to produce JSON only.

## Build A `single_turn` Helper Sub-Agent

Use this for isolated, stateless sub-tasks such as classification, rewriting, extraction, or validation.

```python
from google.adk import Agent
from pydantic import BaseModel, Field


class RewriteRequest(BaseModel):
  text: str = Field(description="Text to rewrite")
  tone: str = Field(default="concise")


class RewriteResult(BaseModel):
  rewritten: str

rewriter = Agent(
    name="rewriter",
    description="Rewrites provided text in the requested tone.",
    mode="single_turn",
    include_contents="none",
    input_schema=RewriteRequest,
    output_schema=RewriteResult,
    instruction="Rewrite only the provided text and return JSON.",
)

root_agent = Agent(
    name="editor",
    instruction="Use the rewriter tool for isolated rewrite requests.",
    sub_agents=[rewriter],
)
```

Semantics:

- As a sub-agent, `single_turn` is exposed as a tool named after the child agent.
- It is not a `transfer_to_agent` target.
- It runs in a sub-branch and normally sees only the immediate tool input.
- Set `include_contents="default"` only when the helper must see parent conversation history.

## Build A `task` Sub-Agent

Use this for a delegated job that may need multiple model/tool turns, user clarification, and structured completion.

```python
from google.adk import Agent
from google.adk.tools.function_tool import FunctionTool
from pydantic import BaseModel, Field


class ResearchInput(BaseModel):
  topic: str = Field(description="Research topic")
  depth: str = Field(default="brief")


class ResearchOutput(BaseModel):
  summary: str
  open_questions: list[str] = []


def approve_expensive_search(topic: str) -> str:
  """Ask the user to confirm an expensive search."""
  return f"Approved search for {topic}."

researcher = Agent(
    name="researcher",
    description="Researches a topic and returns a concise structured summary.",
    mode="task",
    input_schema=ResearchInput,
    output_schema=ResearchOutput,
    instruction=(
        "Research the requested topic. Ask the user if the task is unclear. "
        "When complete, call finish_task with the final JSON output."
    ),
    tools=[FunctionTool(approve_expensive_search, require_confirmation=True)],
)

root_agent = Agent(
    name="writer",
    instruction="Delegate research to the researcher before drafting.",
    sub_agents=[researcher],
)
```

Semantics:

- A `task` child is exposed as a tool, not a transfer target.
- Calling the task child suspends the parent while the child runs.
- The child must call the built-in `finish_task` tool to complete.
- `finish_task` validates `output_schema` when present.
- If the task asks the user a question instead of finishing, ADK pauses and resumes the task on the next user reply.
- Do not use task mode as a root runner agent or workflow graph node.

## Multi-Agent Delegation Design

```python
from google.adk import Agent

billing_agent = Agent(
    name="billing_agent",
    description="Answers invoice, payment, and refund questions.",
    instruction="Handle billing questions only.",
)

technical_agent = Agent(
    name="technical_agent",
    description="Troubleshoots product setup and usage issues.",
    instruction="Handle technical support questions only.",
)

root_agent = Agent(
    name="support_coordinator",
    instruction=(
        "Triage the user's request. Transfer chat questions to the best "
        "specialist when ongoing conversation is needed. Use tool-like "
        "task or single-turn helpers only for bounded delegated work."
    ),
    sub_agents=[billing_agent, technical_agent],
)
```

Design checklist:

- Give every sub-agent a unique `name` and discriminative `description`.
- Use chat children for conversational specialists and transfer-like routing.
- Use `task` children for bounded delegated jobs with completion criteria.
- Use `single_turn` children for stateless helper calls.
- Make parent instructions mention when and how to delegate.
- If a child lacks context, decide whether it should receive explicit input fields or `include_contents="default"`; do not assume sub-branch history is visible to the parent.

## Convert A Basic Agent To `single_turn` With Schema And Tool Callbacks

Use this pattern for the difficult case where a user wants single-turn structured output, callbacks, and safe generation config.

```python
from typing import Any

from google.adk import Agent
from google.adk.tools import BaseTool, ToolContext
from google.genai import types
from pydantic import BaseModel


class Classification(BaseModel):
  label: str
  reason: str


def before_tool_callback(
    tool: BaseTool,
    args: dict[str, Any],
    tool_context: ToolContext,
) -> dict[str, str] | None:
  if not args:
    return {"error": "missing tool arguments"}
  return None

classifier = Agent(
    name="classifier",
    mode="single_turn",
    include_contents="none",
    instruction="Classify the input and return JSON only.",
    output_schema=Classification,
    output_key="classification",
    before_tool_callback=before_tool_callback,
    generate_content_config=types.GenerateContentConfig(temperature=0),
)
```

Validation points:

- `response_schema` is not set in `GenerateContentConfig`.
- Tool callbacks return dicts or `None`.
- If this agent is run by `Runner` as a root, change it to `mode="chat"` or put it under a chat parent.
- If it is a child helper, provide explicit input through `input_schema` or set `include_contents="default"` intentionally.

## Debug A Sub-Agent That Lacks Context

When a child seems to miss parent context:

1. Identify the child's `mode`.
2. For `single_turn`, assume `include_contents="none"` in sub-agent/tool contexts unless explicitly set otherwise.
3. For `task`, ensure the parent passed all required fields in the tool call and the `input_schema` describes those fields.
4. Check the child `description`; poor descriptions cause the parent to choose the wrong delegate or pass vague requests.
5. Remember that sub-agent internals run on a sub-branch. Parent state can be passed forward, but parent event history does not automatically include child internal chatter.
6. Prefer explicit schema fields for necessary context over broad history visibility.

A robust fix is often to add an `input_schema` such as `request`, `constraints`, and `known_context`, then update the parent instruction to pass those fields when calling the child.

## Local Constructor Inspection

Run the bundled script to inspect the installed API without network calls. From this sub-skill directory, use:

```bash
python scripts/inspect_agent_api.py
```

From the root `adk-python` skill directory, use:

```bash
python sub-skills/agent-construction/scripts/inspect_agent_api.py
```

Expected behavior:

- Imports `google.adk`.
- Prints installed version when available.
- Prints signatures for `Agent`, `Runner.run`, `RunConfig`, and `FunctionTool` when available.
- Constructs a minimal in-memory `Agent` object without model execution.
