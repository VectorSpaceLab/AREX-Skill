# LangGraph Package Map

## Packages and Import Roots

| Distribution | Import modules | Primary use | Install notes |
| --- | --- | --- | --- |
| `langgraph` | `langgraph`, `langgraph.graph`, `langgraph.types`, `langgraph.store` | Core graph runtime, state graphs, Pregel runtime, store interfaces, bundled prebuilt dependency | Most users install this first. |
| `langgraph-prebuilt` | `langgraph.prebuilt` | ReAct-style agent factory, `ToolNode`, `ValidationNode`, interrupt schemas | Bundled by `langgraph`; install directly only for focused dependency management. |
| `langgraph-checkpoint` | `langgraph.checkpoint` | Base checkpoint interfaces, in-memory saver, serde | Included by `langgraph`; use directly for custom saver work. |
| `langgraph-checkpoint-sqlite` | `langgraph.checkpoint.sqlite` | SQLite checkpoint savers and async SQLite saver | Good for local development and lightweight persistence. |
| `langgraph-checkpoint-postgres` | `langgraph.checkpoint.postgres` | Postgres checkpoint savers | Install a Psycopg implementation such as `psycopg[binary]` or system `libpq` support. |
| `langgraph-cli` | `langgraph_cli`, command `langgraph` | Project templates, local dev server, Docker, build, config validation | Use `langgraph-cli[inmem]` for in-memory development server mode. |
| `langgraph-sdk` | `langgraph_sdk` | Python clients for LangGraph API server/deployments | Requires a reachable API server for most operations. |

## Version Facts from Repository Snapshot

- `langgraph`: `1.2.6`
- `langgraph-prebuilt`: `1.1.0`
- `langgraph-checkpoint`: `4.1.1`
- `langgraph-checkpoint-sqlite`: `3.1.0`
- `langgraph-checkpoint-postgres`: `3.1.0`
- `langgraph-cli`: `0.4.30`
- `langgraph-sdk`: `0.4.2`

## Selection Guide

- For graph building and local invocation, install `langgraph` and use the `graph-runtime` sub-skill.
- For a tool-calling chat agent, start with `langgraph` plus `langchain` model/provider packages and use `prebuilt-agents`.
- For durable execution or human-in-the-loop resume, combine `graph-runtime` with `persistence`.
- For app serving or containerization, install `langgraph-cli` and use `cli-deployment`.
- For remote API interactions from Python, install `langgraph-sdk` and use `sdk-clients`.

## Optional Dependency Pitfalls

- `langgraph-checkpoint-postgres` depends on `psycopg` but may need `psycopg[binary]` or system `libpq` for imports to work on a fresh machine.
- `langgraph dev` hot-reload/in-memory server mode needs the CLI `inmem` extra.
- Model providers such as OpenAI, Anthropic, or local LLM integrations are not provided by LangGraph itself; install the relevant LangChain provider package.
- SDK streaming over WebSocket is async-only; sync streaming uses SSE.
