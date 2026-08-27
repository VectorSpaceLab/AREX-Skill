# Capability Map

Use this map when a task spans multiple OpenAI Agents Python surfaces.

## Ownership Matrix

| Capability | Primary owner | Supporting owner |
| --- | --- | --- |
| Create an `Agent`, set instructions/output type/model/tools, run sync/async | `core-runtime` | `models-providers`, `tools-handoffs-guardrails` |
| Stream runs and interpret stream events/new items | `core-runtime` | `tracing-observability` for span/usage visibility |
| Pause for approvals and resume from `RunState` | `core-runtime` | `tools-handoffs-guardrails`, `sessions-memory` |
| Function tools, schemas, docstring parsing, strict mode | `tools-handoffs-guardrails` | `core-runtime` |
| Hosted tools, tool search, hosted shell, local shell/computer/apply-patch | `tools-handoffs-guardrails` | `models-providers`, `sandbox-agents` |
| Handoffs, agents-as-tools, manager-style orchestration | `tools-handoffs-guardrails` | `core-runtime` |
| Input/output/tool guardrails and tripwire behavior | `tools-handoffs-guardrails` | `tracing-observability` for logging/trace hygiene |
| Client-side sessions and storage backends | `sessions-memory` | `core-runtime` |
| Server-managed continuation with `conversation_id` or `previous_response_id` | `sessions-memory` | `core-runtime`, `models-providers` |
| OpenAI provider, OpenAI-compatible endpoints, websocket transport | `models-providers` | `core-runtime` |
| Non-OpenAI adapters, LiteLLM, any-llm, retry settings | `models-providers` | `tracing-observability` for usage/reporting caveats |
| MCP stdio/SSE/streamable HTTP servers and hosted MCP tools | `mcp-and-hosted-tools` | `tools-handoffs-guardrails`, `models-providers` |
| Realtime text/audio sessions, telephony, interruption playback | `realtime-voice` | `models-providers`, `tools-handoffs-guardrails` |
| VoicePipeline STT-agent-TTS workflows | `realtime-voice` | `tracing-observability` |
| SandboxAgent, manifests, workspace materialization, clients, snapshots | `sandbox-agents` | `tools-handoffs-guardrails`, `core-runtime` |
| Trace export, custom processors, usage, graph visualization, debug logging | `tracing-observability` | `models-providers`, `core-runtime` |
| Repository editing, tests, docs, compatibility, PR handoff | `repo-development` | the affected runtime sub-skill |

## Common Multi-Skill Routes

### Build a production chat app

Read in order:

1. `core-runtime` for `Agent`, `Runner`, output types, streaming, and run config.
2. `sessions-memory` for conversation history and backend choice.
3. `tools-handoffs-guardrails` for function tools, approvals, handoffs, and guardrails.
4. `models-providers` for model/provider/env setup.
5. `tracing-observability` for trace/usage hygiene.

### Add a workspace-capable coding agent

Read in order:

1. `sandbox-agents` for `SandboxAgent`, `Manifest`, capabilities, clients, and workspace safety.
2. `tools-handoffs-guardrails` only if shell/computer/apply-patch tools are used outside sandbox-native capabilities.
3. `core-runtime` for running and resuming the agent.
4. `repo-development` if the task edits this repository.

### Build a realtime voice workflow

Read in order:

1. `realtime-voice` for session lifecycle, audio config, events, interruption tracking, and voice extras.
2. `tools-handoffs-guardrails` for function tools, approvals, handoffs, and guardrails inside realtime sessions.
3. `models-providers` for provider/key/model setup.
4. `tracing-observability` for trace and audio-data privacy.

### Integrate external tool servers

Read in order:

1. `mcp-and-hosted-tools` for MCP server transport, hosted MCP, filtering, approval, retries, and metadata.
2. `tools-handoffs-guardrails` for generic tool-selection and approval patterns.
3. `models-providers` for Responses-only hosted tool support and unsupported Chat Completions features.
4. `tracing-observability` when tool payload privacy matters.

## Optional Extras Quick Map

| Extra | Typical owner | Enables |
| --- | --- | --- |
| `voice` | `realtime-voice` | `agents.voice`, NumPy-backed voice pipeline helpers |
| `realtime` | `realtime-voice` | websocket dependency for realtime paths, already included by base dependency in this checkout |
| `redis`, `sqlalchemy`, `mongodb`, `dapr`, `encrypt` | `sessions-memory` | optional session backends/wrappers |
| `litellm`, `any-llm` | `models-providers` | third-party model adapter integrations |
| `docker`, hosted sandbox provider extras | `sandbox-agents` | non-default sandbox clients |
| `viz` | `tracing-observability` | Graphviz-based agent visualization |

Install only the extra required by the selected workflow. Do not install broad optional groups to solve a narrow import or configuration problem.
