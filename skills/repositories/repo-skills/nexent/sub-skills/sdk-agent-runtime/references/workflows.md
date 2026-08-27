# SDK Agent Runtime Workflows

Use these workflows to complete SDK-runtime tasks without reopening the original source documentation. When a workflow crosses into route/service/database, frontend, knowledge-data, or deployment ownership, stay within this sub-skill for SDK object behavior and route the other half to the appropriate sibling sub-skill.

## 1. Safe runtime inspection

Run the bundled helper from any checkout or installed SDK environment:

```bash
python sub-skills/sdk-agent-runtime/scripts/inspect_sdk_runtime.py --repo-root .
python sub-skills/sdk-agent-runtime/scripts/inspect_sdk_runtime.py --repo-root . --json
```

The helper:

- Adds the checkout's SDK source root to `sys.path` for inspection.
- Imports key SDK modules when dependencies are available.
- Falls back to AST/static summaries when imports fail.
- Prints signatures, model/dataclass fields, selected public methods, MCP transport normalization examples, tool exports, and source file presence.
- Does not start FastAPI, agent runs, Docker/Kubernetes, MCP/A2A sessions, data services, or network/model calls.

## 2. Direct `CoreAgent` versus streaming `agent_run`

Choose the entry point by output contract:

| Need | Preferred entry point | Notes |
| --- | --- | --- |
| Library-style local agent object, direct synchronous run, custom tool objects already created | `CoreAgent` | You construct model/tool instances yourself. Real model calls occur when `agent.run()` invokes the model. |
| Server/UI/event stream, backend-shaped runtime payload, MCP host loading, stop control | `agent_run(AgentRunInfo)` | Builds a `NexentAgent` factory in a background thread and yields observer JSON strings. |
| Factory construction from serializable configs | `NexentAgent.create_single_agent(AgentConfig)` | Converts `ModelConfig` + `ToolConfig` + managed/A2A agents into a `CoreAgent`. |

Minimal direct construction pattern:

```python
from threading import Event

from nexent.core.agents.core_agent import CoreAgent
from nexent.core.models.openai_llm import OpenAIModel
from nexent.core.utils.observer import MessageObserver

observer = MessageObserver(lang="en")
model = OpenAIModel(
    observer=observer,
    model_id="provider-model-name",
    api_key="...",
    api_base="https://provider.example/v1",
)
agent = CoreAgent(
    observer=observer,
    tools=[],
    model=model,
    name="demo_agent",
    description="Answer simple questions.",
    max_steps=5,
)

# This calls the external provider. Do not run it in unit tests without a fake model.
result = agent.run("Say hello")
```

## 3. Streaming `AgentRunInfo` recipe

Production-style streaming uses `ModelConfig`, `AgentConfig`, `MessageObserver`, and `stop_event`:

```python
import asyncio
import json
from threading import Event

from nexent.core.agents.agent_model import AgentConfig, AgentRunInfo, ModelConfig, ToolConfig
from nexent.core.agents.run_agent import agent_run
from nexent.core.utils.observer import MessageObserver

async def stream_once():
    observer = MessageObserver(lang="en")
    stop_event = Event()

    model_config = ModelConfig(
        cite_name="default_llm",
        model_name="provider-model-name",
        api_key="...",
        url="https://provider.example/v1",
        temperature=0.1,
        top_p=0.95,
        timeout_seconds=60,
    )
    agent_config = AgentConfig(
        name="example_agent",
        description="A minimal streaming SDK agent.",
        tools=[],
        max_steps=5,
        model_name="default_llm",  # must match ModelConfig.cite_name
    )
    run_info = AgentRunInfo(
        query="Summarize the SDK runtime contract.",
        model_config_list=[model_config],
        observer=observer,
        agent_config=agent_config,
        stop_event=stop_event,
        history=[],
    )

    async for raw in agent_run(run_info):
        chunk = json.loads(raw)
        yield chunk

# asyncio.run(stream_once()) would call the external model. Use only with a configured provider.
```

### Unit-test version without external model calls

Do not iterate the real `agent_run` in unit tests unless all model/MCP/tool calls are patched. Inject a runner into your application wrapper:

```python
import json
from threading import Event

from nexent.core.agents.agent_model import AgentConfig, AgentRunInfo, ModelConfig
from nexent.core.utils.observer import MessageObserver

async def build_and_stream(query: str, runner):
    run_info = AgentRunInfo(
        query=query,
        model_config_list=[ModelConfig(
            cite_name="fake_llm",
            model_name="fake-model",
            api_key="",
            url="http://example.invalid/v1",
        )],
        observer=MessageObserver(lang="en"),
        agent_config=AgentConfig(
            name="unit_agent",
            description="Construction-only unit test agent.",
            tools=[],
            model_name="fake_llm",
        ),
        stop_event=Event(),
    )
    try:
        async for raw in runner(run_info):
            yield json.loads(raw)
    finally:
        run_info.stop_event.set()

async def fake_runner(received_run_info):
    assert received_run_info.agent_config.model_name == "fake_llm"
    yield json.dumps({"type": "tool", "content": "fake tool event"})
    yield json.dumps({"type": "final_answer", "content": "fake final answer"})
```

This still exercises `AgentRunInfo`, `ModelConfig`, `AgentConfig`, `MessageObserver`, and graceful stop behavior while avoiding provider calls. Native backend NL2Agent/NL2Skill tests use the same pattern: build the run-info object, monkeypatch the streaming runner, assert chunks and `stop_event.set()`.

For lower-level SDK tests around `agent_run_thread`, monkeypatch `NexentAgent` and `ToolCollection.from_mcp`; then assert constructor arguments and normalized MCP host lists.

## 4. Tool configuration workflow

1. Decide tool source.
2. Use `ToolConfig(class_name=..., name=..., source=..., params=..., metadata=...)`.
3. Validate constructor parameters against [`api-reference.md`](api-reference.md) or `inspect_sdk_runtime.py` output.
4. If the tool has `observer`, excluded runtime objects, or security-sensitive clients, inject them via `metadata` or factory code, not model-visible `inputs`.
5. Test tool construction separately from execution when the tool would hit network, credentials, storage, vector DB, or external search services.

### Local SDK tools

```python
ToolConfig(
    class_name="ExaSearchTool",
    name="exa_search",
    source="local",
    params={"exa_api_key": "...", "max_results": 3},
)
```

`NexentAgent.create_local_tool` looks up `class_name` among SDK tool imports. Typical exported tools include web search tools, email tools, file/directory tools, terminal tool, multimodal analysis tools, SQL tools, memory tools, and plan tools. Many external-search tools require API keys and must be mocked in tests.

### Builtin tools

Use `source="builtin"` for SDK runtime tools whose creation has explicit factory branches:

- `RunSkillScriptTool`
- `ReadSkillMdTool`
- `WriteSkillFileTool`
- `ReadSkillConfigTool`
- `CreatePlanTool`
- `UpdatePlanStepTool`
- `CreateScheduledTaskProposalTool`

### MCP tools

Use `source="mcp"` when `class_name` is the remote MCP tool name available in the active MCP collection. The collection is created only when `AgentRunInfo.mcp_host` is non-empty.

### LangChain tools

Use `source="langchain"` and pass the LangChain tool object through `ToolConfig.metadata`; the SDK wraps it with `Tool.from_langchain`.

## 5. MCP URL transport diagnosis

Nexent auto-detects MCP transport using exact URL suffixes after whitespace stripping:

| Input | Normalized transport |
| --- | --- |
| `"http://host/sse"` | `sse` |
| `"http://host/mcp"` | `streamable-http` |
| `"http://host"` | `streamable-http` |
| `{"url": "http://host/sse", "transport": "streamable-http"}` | `streamable-http` because explicit transport wins |

Diagnostic snippet:

```python
from nexent.core.agents.run_agent import _normalize_mcp_config

cases = [
    "http://local-mcp:5011/sse",
    "http://local-mcp:5011/mcp",
    {"url": "http://local-mcp:5011/base/sse", "authorization": "Bearer token"},
]
for item in cases:
    print(_normalize_mcp_config(item))
```

When `/sse` versus `/mcp` appears wrong:

1. Check the literal URL ending. `.../sse/`, `.../sse?x=1`, and `.../mcp/` do not match the suffix rules; supply an explicit `transport` dict or normalize the URL.
2. Check that dict inputs contain `url`; missing `url` raises `ValueError`.
3. Check that explicit `transport` is exactly `sse` or `streamable-http`.
4. Check auth merging: `authorization` becomes `headers.Authorization`; if `headers` also exists, the authorization value overwrites/sets that header in a copy.
5. For backend NL2Agent/NL2Skill flows, route service construction bugs to `backend-services-api`; the SDK normalization contract remains here.

## 6. A2A managed-agent workflow

External A2A agents are configured on `AgentConfig.external_a2a_agents` and become managed-agent tools during `NexentAgent.create_single_agent`.

```python
from nexent.core.agents.agent_model import AgentConfig, ExternalA2AAgentConfig

a2a = ExternalA2AAgentConfig(
    agent_id="search-agent",
    name="SearchAgent",
    url="https://a2a.example/agent",
    api_key="...",
    protocol_type="JSONRPC",
    transport_type="http-streaming",
    raw_card={"skills": [{"name": "web_search", "examples": ["search Nexent"]}]},
)
agent_config = AgentConfig(
    name="coordinator",
    description="Delegates search tasks.",
    tools=[],
    model_name="default_llm",
    external_a2a_agents=[a2a],
)
```

Tests should construct `A2AAgentInfo`/`ExternalA2AAgentConfig` and assert header/payload/endpoint behavior with mocked HTTP clients. Do not call live A2A endpoints in unit tests.

## 7. Sandbox workflow

SDK sandboxing is object-injected:

```python
from nexent.core.agents.sandbox import SandboxConfig, SandboxLevel, SandboxScope, ShellPolicy

sandbox_config = SandboxConfig(
    level=SandboxLevel.DOCKER,
    scope=SandboxScope.SESSION,
    docker_image="nexent/nexent-sandbox:latest",
    memory_limit_mb=512,
    network_disabled=True,
    shell_policy=ShellPolicy.DISABLED,
    timeout_seconds=30,
)
```

Pass the resolved object as `AgentRunInfo.sandbox_config`. Do not add SDK-level environment reads. Application/backend code owns env parsing and config merging.

Design notes:

- `None` means backward-compatible local execution.
- Docker/WASM construction can fall back to local executor if optional dependencies or runtime backends are unavailable.
- Non-local sandboxing with managed agents falls back to local due to SmolAgents executor-sharing constraints.
- Host tools in remote sandboxes are proxied through a token-authenticated bridge; local/builtin/MCP tools are marked as host-executed.
- Shell guard blocks `subprocess`/`os` shell calls when `ShellPolicy.DISABLED` is active.
- Output sync requires `minio_client` when `auto_sync_outputs=True`; route object-storage setup details to deployment/knowledge-data owners as appropriate.

## 8. Verification and guardrail workflow

Attach verification to `AgentConfig`:

```python
from nexent.core.agents.agent_model import AgentVerificationConfig, GuardrailConfig, GuardrailRule

verification_config = AgentVerificationConfig(
    enabled=True,
    step_verification_enabled=True,
    final_verification_enabled=True,
    llm_verification_enabled=False,  # useful for deterministic unit tests
    strictness="balanced",
    critical_events=["tool_precheck", "tool_result", "final_answer"],
    guardrail_config=GuardrailConfig(
        enabled=True,
        rules=[GuardrailRule(name="secret", pattern=r"SECRET-[A-Z0-9]+", severity="mask")],
    ),
)
```

Use deterministic verification (`llm_verification_enabled=False`) in unit tests. Keep LLM-based final verification for integration paths with configured providers.

## 9. Monitoring workflow

At application/request boundaries, bind metadata once and let SDK lifecycle spans do the rest:

```python
from nexent.monitor.monitoring import AgentRunMetadata, MonitoringConfig, get_monitoring_manager

manager = get_monitoring_manager()
manager.configure(MonitoringConfig(
    enable_telemetry=True,
    provider="otlp",
    otlp_endpoint="http://otel-collector:4318",
    trace_content_mode="summary",
))

with manager.start_agent_run(AgentRunMetadata(
    tenant_id="tenant-a",
    user_id="user-1",
    agent_name="example_agent",
    query="summarize",
)):
    # create/run SDK agent here
    ...
```

`NexentAgent` and `OpenAIModel` add model/tool/retriever/context metrics. `KnowledgeBaseSearchTool` and `SearchMemoryTool` become retriever spans automatically.

## 10. Scheduler workflow

Use pure trigger calculation for deterministic tests:

```python
from datetime import datetime, timezone
from nexent.scheduler.triggers import ScheduleMode, ScheduleRuleType, ScheduleSpec, compute_next_fire_at

spec = ScheduleSpec(
    mode=ScheduleMode.RECURRING,
    rule_type=ScheduleRuleType.INTERVAL,
    timezone="UTC",
    start_at=datetime(2025, 1, 1, tzinfo=timezone.utc),
    interval_seconds=3600,
    max_fire_count=3,
)
next_fire = compute_next_fire_at(spec, datetime(2025, 1, 1, 0, 1, tzinfo=timezone.utc), fire_count=0)
```

Use `LeaseScheduler` only when you have a store implementing the lease contract and an async executor. Avoid starting durable schedulers in unit tests unless the store/executor are fake and bounded.

## 11. Skill manager workflow

Use `SkillManager` when SDK runtime code needs tenant-isolated skill metadata or script execution:

```python
from nexent.skills.skill_manager import SkillManager

manager = SkillManager(base_skills_dir="./test-skills")
skills = manager.list_skills(tenant_id="tenant-a")
```

Rules:

- Use a temporary base directory in tests.
- Treat script execution as side-effecting; pass safe params and never rely on credentials.
- Use `SkillLoader.parse` for static `SKILL.md` parsing tests.
- Backend CRUD/service behavior belongs to the backend sub-skill; this workflow covers SDK manager semantics.

## 12. Native verification candidates to remember

For final verification planning, relevant CPU/mocked candidates include:

- Observer and streaming formatting tests.
- Agent model, `agent_run`, `CoreAgent`, `NexentAgent`, A2A proxy, sandbox, planning, and context runtime tests.
- OpenAI model and capacity/prompt-cache tests with mocked provider calls.
- Tool tests for local tool metadata and observer behavior.
- Backend NL2Agent/NL2Skill service/agent tests that construct SDK run-info objects and monkeypatch `agent_run`.

Do not run long benchmarks, live model calls, live MCP/A2A endpoints, live vector DB/memory providers, or deployment stacks as minimum SDK runtime checks.
