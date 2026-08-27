# Template catalog

This is the distilled built-in template map used by `create` and `list`.

| Template | Language | Deployment targets | Key traits | Best fit |
| --- | --- | --- | --- | --- |
| `adk` | Python | `agent_engine`, `cloud_run`, `gke`, `none` | Minimal ADK ReAct agent; requires sessions in deployed projects | General starting point for a simple agent |
| `adk_a2a` | Python | `agent_engine`, `cloud_run`, `gke`, `none` | ADK plus A2A protocol support and related dependencies | Interoperable agent workflows |
| `adk_live` | Python | `agent_engine`, `cloud_run`, `gke`, `none` | Real-time multimodal/live agent with frontend support | Voice/video/text live experiences |
| `agentic_rag` | Python | `agent_engine`, `cloud_run`, `gke`, `none` | RAG template with data ingestion and session setup | Document Q&A and retrieval-backed agents |
| `langgraph` | Python | `agent_engine`, `cloud_run`, `gke`, `none` | LangGraph-based agent with A2A/inspector support | Bring-your-own-framework workflows |
| `adk_go` | Go | `cloud_run`, `gke`, `none` | Go template with separate agent directory and Go tooling | Go-based agents with cloud deployment |
| `adk_java` | Java | `cloud_run`, `gke`, `none` | Java/Maven template with package-path layout | Java-based agents with cloud deployment |
| `adk_ts` | TypeScript | `cloud_run`, `gke`, `none` | TypeScript template with Node tooling and frontend/runtime files | TypeScript-based agents with cloud deployment |

## Shared template traits
- `agentic_rag` is the only built-in template that automatically requires data ingestion.
- `adk_live` is the only built-in template with a React frontend.
- `adk_go`, `adk_java`, and `adk_ts` do not target `agent_engine`.
- `langgraph` is the main choice when the user wants to keep a non-ADK framework.

## Generation-time choices that matter
- Deployment target: `agent_engine`, `cloud_run`, `gke`, or `none`.
- CI/CD runner: `google_cloud_build`, `github_actions`, or `skip`.
- Datastore: `vertex_ai_search` or `vertex_ai_vector_search` when data ingestion is needed.
- Session type: `in_memory`, `cloud_sql`, or `agent_engine` where supported.
- Agent directory: usually `app`, but some templates use `agent` or `src/main/java`.

## Where the template facts came from
- Built-in template config files under `agent_starter_pack/agents/*/.template/templateconfig.yaml`
- The CLI `list` command and `get_available_agents()` helper
- README and CLI documentation for creation-time options
