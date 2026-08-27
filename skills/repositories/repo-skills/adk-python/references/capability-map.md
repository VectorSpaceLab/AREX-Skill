# ADK Python Capability Map

Use this map when the user's request spans multiple ADK surfaces or when you need the fastest route to the right sub-skill.

| User request family | Route | Use first | Useful bundled diagnostics | Validation expectation |
| --- | --- | --- | --- | --- |
| Create or modify an `Agent`, `LlmAgent`, model config, instruction, callback, output schema, task agent, or sub-agent | `agent-construction` | `sub-skills/agent-construction/SKILL.md` | `sub-skills/agent-construction/scripts/inspect_agent_api.py` | Import/signature check; focused agent tests for repo edits |
| Build a graph with `Workflow`, `BaseNode`, function nodes, routes, joins, parallel workers, dynamic nodes, HITL, or retry | `workflow-orchestration` | `sub-skills/workflow-orchestration/SKILL.md` | `sub-skills/workflow-orchestration/scripts/inspect_workflow_api.py` | Tiny no-LLM workflow construction; workflow/event tests for repo edits |
| Add or debug tools, `ToolContext`, function tools, toolsets, MCP, OpenAPI, Google API, A2A, auth, or optional integration extras | `tools-and-integrations` | `sub-skills/tools-and-integrations/SKILL.md` | `sub-skills/tools-and-integrations/scripts/inspect_tooling.py` | Optional-extra diagnostic; mocked tool/auth/integration tests when safe |
| Configure `Runner`, `App`, sessions, memory, artifacts, plugins, telemetry, code executors, or environment services | `runtime-services` | `sub-skills/runtime-services/SKILL.md` | `sub-skills/runtime-services/scripts/check_runtime_services.py` | Import/service diagnostic; avoid touching user databases by default |
| Use `adk run`, `adk web`, `adk api_server`, YAML config, app discovery, service URIs, or deployment commands | `cli-configuration-deployment` | `sub-skills/cli-configuration-deployment/SKILL.md` | `sub-skills/cli-configuration-deployment/scripts/inspect_adk_cli.py` | `--help` and schema-resource checks before servers/deployments |
| Build eval sets, JSON tests, `adk test`, `adk eval`, session/event summaries, traces, or debugging reports | `evaluation-debugging` | `sub-skills/evaluation-debugging/SKILL.md` | `sub-skills/evaluation-debugging/scripts/summarize_adk_events.py` | Static JSON/event checks first; model-backed evals only with credentials |
| Change ADK Python source, docs, samples, schemas, or tests in a checkout | `repo-development` | `sub-skills/repo-development/SKILL.md` | `sub-skills/repo-development/scripts/select_adk_tests.py` | Focused pytest/style/docs/sample/schema commands based on changed area |

## Cross-route Patterns

- **Agent app end-to-end:** start in `agent-construction`, then use `cli-configuration-deployment` for app layout and `evaluation-debugging` for JSON test/eval fixtures.
- **Workflow app with services:** start in `workflow-orchestration`, then use `runtime-services` for `Runner`, sessions, memory, artifacts, and plugins.
- **Tool-heavy app:** start in `tools-and-integrations`, then use `agent-construction` for agent binding and `cli-configuration-deployment` for local runs.
- **Repository bug fix:** start in `repo-development`, then route to the capability sub-skill that owns the changed behavior for API and troubleshooting depth.
- **Deployment issue:** start in `cli-configuration-deployment`, then use `runtime-services` for service URI choices and `tools-and-integrations` for credentialed toolsets.

## Optional Extras Cheat Sheet

Base `google-adk` intentionally does not install every integration. Use the narrow extra for the selected task:

- `db`: SQLAlchemy-backed database session services and migration-related checks.
- `mcp`: MCP toolsets and session managers.
- `eval`: evaluator and optimization workflows with additional metrics/data dependencies.
- `gcp`: Google Cloud integrations, storage, BigQuery, Pub/Sub, Agent Engine, and cloud telemetry surfaces.
- `extensions`: third-party model/tool/code-execution integrations such as LiteLLM, Claude, Docker/Kubernetes-related helpers, LangGraph, LangChain, CrewAI, and optional parsers.
- `a2a`, `agent-identity`, `slack`, `toolbox`, `tools`, `e2b`, and provider-specific extras: install only when the selected workflow requires them.
