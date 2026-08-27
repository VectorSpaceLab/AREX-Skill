# Decorators and Agent Factory Basics

This reference covers the core decorator and factory features that a local app author needs. It intentionally stops before workflow pattern selection and durable execution strategy; route that deeper design work to sibling `workflow-patterns` or `durable-execution`.

## Decorator Overview

`MCPApp` exposes engine-aware decorators that register tools, workflows, tasks, and signals:

| Decorator | Target | Core use |
| --- | --- | --- |
| `@app.tool` | sync or ordinary function | Expose a blocking/local function as an MCP tool and create a workflow-backed endpoint. |
| `@app.async_tool` | async function | Expose a long-running async tool and publish workflow run/status handles. |
| `@app.workflow` | `Workflow` subclass | Register a workflow class and apply engine-specific wrappers. |
| `@app.workflow_run` | async method | Mark a workflow entrypoint. |
| `@app.workflow_task` | async function/method | Register reusable async work as an activity/task. |
| `@app.workflow_signal` | async method | Register an inbound signal handler. |

Both tool decorators accept:

- `name`: exported tool name; defaults to function name.
- `title`: display label for clients.
- `description`: human-readable description; docstring is used when omitted.
- `annotations`: MCP `ToolAnnotations` or mapping.
- `icons`: `Icon` objects or mappings.
- `meta`: arbitrary metadata forwarded to FastMCP.
- `structured_output`: hint that the return value is structured JSON.

## Local Tool Decorators

Use `@app.tool` for work that returns within one MCP call:

```python
from pydantic import BaseModel
from mcp_agent.app import MCPApp

app = MCPApp(name="reporting")

class Summary(BaseModel):
    title: str
    verdict: str

@app.tool(description="Summarize a document deterministically.", structured_output=True)
def summarize_document(text: str) -> Summary:
    """Return a compact title and review verdict."""
    return Summary(
        title=text.splitlines()[0][:80] if text else "Untitled",
        verdict="APPROVED" if "ship it" in text.lower() else "NEEDS REVIEW",
    )
```

Use `@app.async_tool` for coroutine work or flows that should expose workflow status:

```python
from mcp_agent.core.context import Context

@app.async_tool(name="classify_text", description="Classify text with local logic.")
async def classify_text(text: str, app_ctx: Context | None = None) -> str:
    logger = app_ctx.app.logger if app_ctx else app.logger
    label = "urgent" if "asap" in text.lower() else "normal"
    logger.info("classified", data={"label": label})
    return label
```

Decorator validation guidance:

- Add type hints for every parameter and return value. Missing or unsupported annotations can raise schema validation errors at import time.
- Keep defaults JSON-serializable where possible.
- Use Pydantic models for structured output.
- If a tool needs runtime context, name a parameter `app_ctx` or annotate it with `mcp_agent.core.context.Context`; the app's wrapper can inject it when available.
- For CPU-heavy sync work, offload inside the function to avoid blocking the app event loop.

## Workflow Decorator Basics

This sub-skill only covers the mechanics needed to recognize and register workflows. For choosing router/orchestrator/parallel/evaluator/swarm patterns, use `workflow-patterns`.

```python
from datetime import timedelta
from mcp_agent.executor.workflow import Workflow, WorkflowResult

@app.workflow
class ReviewWorkflow(Workflow[WorkflowResult[str]]):
    @app.workflow_task(schedule_to_close_timeout=timedelta(minutes=5))
    async def draft(self, topic: str) -> str:
        return f"Draft for {topic}"

    @app.workflow_signal(name="editor_feedback")
    async def editor_feedback(self, notes: str) -> None:
        self.state.feedback = notes or ""

    @app.workflow_run
    async def run(self, topic: str) -> WorkflowResult[str]:
        draft = await self.draft(topic)
        return WorkflowResult(value=draft)
```

Mechanics:

- `@app.workflow` stores the class on `app.workflows` and attaches an app reference.
- `@app.workflow_run` wraps initialization/tracing and maps to engine-specific run decorators when available.
- `@app.workflow_task` requires async functions; wrap blocking work with `asyncio.to_thread`.
- `@app.workflow_signal` supports optional custom names and works for asyncio and Temporal-compatible execution.
- Switching `execution_engine` changes engine wrappers, but durable operations and worker deployment are outside this sub-skill.

## AgentSpec

Verified `AgentSpec` fields:

```python
AgentSpec(
    name: str,
    instruction: str | None = None,
    server_names: list[str] = [],
    connection_persistence: bool = True,
)
```

`AgentSpec` allows extra fields, so factory loaders can include `functions` and `human_input_callback` programmatically or from trusted dotted references.

YAML spec shape:

```yaml
agents:
  - name: finder
    instruction: You can read files and fetch URLs.
    server_names: [filesystem, fetch]
  - name: coder
    instruction: Inspect and modify code files in the repository.
    server_names: [filesystem]
```

Markdown and JSON are also supported by the loaders. Markdown can provide YAML frontmatter or fenced YAML/JSON blocks.

## Factory Helpers

Core factory helpers from `mcp_agent.workflows.factory`:

```python
from mcp_agent.workflows.factory import (
    create_agent,
    agent_from_spec,
    create_llm,
    load_agent_specs_from_text,
    load_agent_specs_from_file,
    load_agent_specs_from_dir,
)
```

`create_agent(spec, context=None)` and `agent_from_spec(spec, context=None)`:

- Convert an `AgentSpec` into an `Agent`.
- Copy `name`, `instruction`, `server_names`, `connection_persistence`, and optional extra `functions`.
- Use `spec.human_input_callback` when present, otherwise inherit `context.human_input_handler` when context is supplied.

```python
spec = AgentSpec(
    name="finder",
    instruction="Find facts with configured MCP tools.",
    server_names=["fetch"],
)
agent = create_agent(spec, context=running_app.context)
```

`create_llm(...)` can create an `AugmentedLLM` from an `Agent`, `AgentSpec`, or agent-name fields:

```python
from mcp_agent.workflows.factory import create_llm

llm = create_llm(
    agent=spec,
    provider="openai",
    model="gpt-4o-mini",
    context=running_app.context,
)
```

Alternate call by name:

```python
llm = create_llm(
    agent_name="single_agent",
    instruction="Answer with local tools only.",
    server_names=[],
    provider="openai",
    model="openai:gpt-4o-mini",
    context=running_app.context,
)
```

Model/provider behavior:

- Supported LLM providers in the factory include `openai`, `anthropic`, `azure`, `google`, `bedrock`, and `ollama`.
- A model string may be prefixed as `provider:model-name` to infer provider.
- `RequestParams` passed to `create_llm` is merged with selected/configured model defaults when possible.
- Provider wrapper imports still require corresponding optional packages and credentials before real generation.

## Loading Agent Specs

Use text loaders for generated specs or tests:

```python
yaml_text = """
agents:
  - name: reviewer
    instruction: Review changes for correctness.
    server_names: [filesystem]
"""
specs = load_agent_specs_from_text(yaml_text, fmt="yaml", context=running_app.context)
```

Use file/dir loaders when specs are external app assets:

```python
specs = load_agent_specs_from_file("agents.yaml", context=running_app.context)
more_specs = load_agent_specs_from_dir("agents", pattern="**/*.yaml", context=running_app.context)
```

Loader behavior:

- YAML/JSON accepts a list, `{agents: [...]}`, `{agent: {...}}`, or a single dict with `name`.
- Markdown accepts YAML frontmatter or fenced YAML/JSON blocks.
- `servers` is accepted as an alias for `server_names`.
- If no `server_names` are present, a `tools` string/list may be interpreted as server names.
- `functions` entries may be callables or trusted dotted references such as `package.module:function`.
- Invalid specs are skipped by loaders rather than raising from the whole file in most parsing paths.

## Decorators with Agents

A common app-level async tool wraps a local agent:

```python
from mcp_agent.agents.agent import Agent
from mcp_agent.core.context import Context
from mcp_agent.workflows.llm.augmented_llm import RequestParams
from mcp_agent.workflows.llm.augmented_llm_openai import OpenAIAugmentedLLM

def add_numbers(a: int, b: int) -> int:
    """Add two integers."""
    return a + b

@app.async_tool(name="calculate")
async def calculate(expr: str, app_ctx: Context | None = None) -> str:
    context = app_ctx or app.context
    agent = Agent(
        name="math_agent",
        instruction="Use the local functions for arithmetic.",
        functions=[add_numbers],
        context=context,
    )
    async with agent:
        llm = await agent.attach_llm(OpenAIAugmentedLLM)
        return await llm.generate_str(
            expr,
            request_params=RequestParams(
                model="gpt-5.1",
                reasoning_effort="none",
                tool_filter={"non_namespaced_tools": {"add_numbers"}},
            ),
        )
```

For pure smoke tests, avoid attaching a real provider and only verify that the app, decorator, `Agent`, and `RequestParams` objects can be constructed.

## Boundary Reminders

This file covers core syntax and basic factories only:

- Use `workflow-patterns` for choosing routers, orchestrators, parallel LLMs, evaluator-optimizer, swarm, intent classifiers, and deep orchestration.
- Use `mcp-server-integration` for exposing the app as an MCP server, server auth internals, FastMCP details, and client/server deployment.
- Use `durable-execution` for Temporal workers, task queues, durable retries, and production run/resume operations.
- Use `observability-integrations` for provider-wrapper internals, tracing exporters, metrics, and token-accounting details.
