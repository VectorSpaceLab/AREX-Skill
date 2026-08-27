---
name: agents-and-awel
description: "Build and debug DB-GPT agents, tools, skills, teams, and AWEL
  workflows, including deterministic local DAG runs and HTTP-trigger topology
  without assuming an LLM, credential, or external service."
metadata:
  disco-role: operating
license: Apache 2.0
disable-model-invocation: true
---

# DB-GPT agents and AWEL

Use this route when the task mentions `dbgpt.agent`, `ConversableAgent`, profiles,
agent context or memory, tools, skills, middleware, teams, prompts, AWEL/DAG/flow,
`MapOperator`, HTTP triggers, flow variables, or local workflow execution. Keep the
work local and deterministic unless the user explicitly supplies a model, service, and
credentials. Route these elsewhere:

- datasource, document loading, chunking, embeddings, retrieval, and knowledge-space
  implementation -> `data-and-rag`;
- provider installation, model backends, controller/worker deployment, and GPU setup ->
  `models-and-serving`;
- HTTP CRUD endpoint semantics, Python client calls, file APIs, and sandbox service
  execution -> `apis-client-and-sandbox`.

## Operating workflow

1. **Classify the target.** Decide whether this is (a) a single agent conversation,
   (b) tool/resource or skill registration, (c) multi-agent/team planning, (d) a
   programmatic AWEL DAG, (e) an HTTP-triggered DAG, or (f) a serialized Flow UI
   definition. Do not treat graph construction as deployment.
2. **Establish a profile and lifecycle.** A `ConversableAgent` needs a
   `ProfileConfig` (unless a subclass supplies one). Bind the `AgentContext` before
   `build()`. Bind the LLM configuration and required memory/resources/actions before
   `build()` as described in [agent-api-reference.md](references/agent-api-reference.md).
   `bind()` is synchronous and returns the same agent; `build()` is async.
3. **Make dependencies explicit.** Define tools with a docstring and typed arguments,
   put them in a `ToolPack`, and bind the pack before an action that consumes it is
   built. A `Skill` sets the agent's prompt when bound, but its declared
   `required_tools` and `required_knowledge` are not a substitute for binding and
   checking actual resources.
4. **Construct AWEL in a DAG context.** Create `DAG("stable-id")`, instantiate
   operators inside `with dag:`, use explicit `task_id`/`task_name` where serialized
   identity matters, and connect nodes with `>>`. Inspect `root_nodes`, `leaf_nodes`,
   and `trigger_nodes` before running. Follow the stream and join constraints in
   [awel-workflows.md](references/awel-workflows.md).
5. **Validate without side effects first.** Instantiate pydantic request/response
   bodies, inspect the resolved endpoint and router metadata, and call a local leaf
   with a tiny fixture. Use `scripts/awel_smoke.py` for an independent no-model/no-
   network topology and execution check. Only then mount into the application's
   supported router or start a development server.
6. **Separate runtime modes.** `leaf.call()`/`call_stream()` use a local runner in the
   current process. An `HttpTrigger` mounted on an app invokes the leaf through the
   HTTP request path. A production DB-GPT service must register/load the DAG and
   provide the application lifecycle; `setup_dev_environment()` is a development
   helper and can start a blocking Uvicorn process.
7. **Verify failure paths.** Check duplicate IDs/names, invalid pydantic input, missing
   action resources, malformed tool schemas, missing skills, serialization boundaries,
   context budget state, and async/sync mismatches. Use the actionable checks in
   [troubleshooting.md](references/troubleshooting.md); do not claim provider or MCP
   coverage from a CPU-only local run.

## Quick patterns

### Local deterministic map

```python
from dbgpt.core.awel import DAG, InputOperator, MapOperator, SimpleInputSource

with DAG("double-local") as dag:
    source = InputOperator(SimpleInputSource(21), task_name="source")
    doubled = MapOperator(lambda value: value * 2, task_name="doubled")
    source >> doubled

result = await doubled.call()
# result == 42
```

For a callable that is not known to be serializable, use it only for local
experimentation. Serialized/deployed flows should use registered operator classes,
metadata, stable IDs, and serializable callables; see [awel-workflows.md](references/awel-workflows.md).

### HTTP trigger topology

```python
from dbgpt._private.pydantic import BaseModel, Field
from dbgpt.core.awel import DAG, HttpTrigger, MapOperator

class RequestBody(BaseModel):
    name: str = Field(..., description="User name")
    age: int = Field(18, description="User age")

class Greeting(MapOperator[RequestBody, str]):
    async def map(self, body: RequestBody) -> str:
        return f"Hello, {body.name}; age={body.age}"

with DAG("greeting-flow") as dag:
    trigger = HttpTrigger(
        "/examples/greeting/{dag_id}", methods="POST", request_body=RequestBody
    )
    leaf = Greeting(task_name="greeting")
    trigger >> leaf
```

The trigger normalizes a missing leading slash, resolves `{dag_id}` from its DAG, and
requires exactly one leaf when it runs through HTTP. POST/PUT-style routes receive a
pydantic body; GET/DELETE model fields become query parameters. Mounting on a plain
FastAPI `APIRouter` is suitable for inspection via `mount_to_router`; DB-GPT's app
mount path uses its supported priority router. Do not infer a live server from router
registration alone.

### Skill and middleware boundary

The core skill API is exported from `dbgpt.agent.skill`: `Skill`, `SkillMetadata`,
`SkillType`, `SkillBuilder`, `SkillLoader`, `SkillManager`, `initialize_skill`, and
`get_skill_manager`. A file-based `SKILL.md` must begin with YAML frontmatter and have
`name` and `description`; its instructions are the remainder of the file. A
`SkillsMiddleware` exposes metadata first and reads full content on demand. Later
configured directories override earlier names. Skill matching is simple keyword
matching, not semantic routing, so always verify the selected skill explicitly.
Details and safe fixture rules are in [skills-and-tools.md](references/skills-and-tools.md).

## API and safety notes

- `AgentContext` carries `conv_id`, language, round/retry limits, generation settings,
  and opt-in context management. `ContextBudgetConfig.effective_budget` is
  `max_context_tokens - reserved_tokens`; the default maximum is 120000 and the
  default reserved output space is 4096.
- `ConversableAgent.check_available()` requires context, action resources where an
  action declares `resource_need`, and an LLM config/client for non-human,
  non-team agents. `build()` preloads resources, performs this check, initializes
  actions and memory, and wraps the configured LLM client.
- `AgentMessage` is the communication object. Preserve `content`, `role`, `context`,
  `action_report`, `review_info`, `current_goal`, and success state when forwarding
  or serializing messages. Use `to_llm_message()` only when the reduced LLM shape is
  intended.
- `@tool` creates a `FunctionTool` wrapper with `._tool`; synchronous and async
  functions must be executed through their matching `execute`/`async_execute` path.
  Missing docstrings/descriptions and malformed explicit `args` are validation errors.
- `MiddlewareManager` executes registered middleware in registration order and skips
  disabled middleware. Hook return dictionaries are merged; system-prompt hooks are
  applied sequentially. Middleware state is not automatically agent state.
- `DAG` IDs are caller-supplied strings; node IDs default to UUIDs. Node names must be
  unique inside a DAG. `MapOperator` expects one parent during normal graph execution,
  `JoinOperator` accepts multiple parents, and `ReduceStreamOperator` requires stream
  input. `call_stream()` wraps a non-stream output as a one-item async stream.
- `HttpTrigger` itself does not support direct `trigger()` execution. It delegates to
  the DAG's single leaf; streaming uses `call_stream()` and normally returns
  `text/event-stream` unless response settings override it.
- Never put API keys, personal filesystem paths, private checkout paths, or live MCP
  URLs in a skill recipe. Treat `MCPToolPack`, code/shell tools, personal skill
  scripts, and provider-backed agent examples as optional side-effectful integrations.

## Progressive disclosure

- [agent-api-reference.md](references/agent-api-reference.md) — signatures and
  lifecycle for profiles, agents, teams, memory/context, tools, and middleware.
- [awel-workflows.md](references/awel-workflows.md) — DAG/operators/runners,
  pydantic HTTP triggers, flow variables, serialization, and deployment boundaries.
- [skills-and-tools.md](references/skills-and-tools.md) — tool schema rules, packs,
  skill builder/loader/manager, SKILL.md middleware, and optional MCP.
- [troubleshooting.md](references/troubleshooting.md) — symptom-to-check recovery
  table for binding, async loops, schemas, IDs, serialization, skills, and HTTP.
- `scripts/awel_smoke.py` — safe local topology, router metadata, pydantic validation,
  and tiny-fixture DAG execution; it never starts a server or calls a model.
