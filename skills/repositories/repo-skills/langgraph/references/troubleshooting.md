# LangGraph Cross-Cutting Troubleshooting

## Import and Installation Failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ModuleNotFoundError: langgraph` | Core package is not installed in the active Python | Install `langgraph` in the environment actually running the code; rerun a minimal `StateGraph` smoke check. |
| `ModuleNotFoundError: langgraph_cli` or command `langgraph` missing | CLI package is separate | Install `langgraph-cli`; use `langgraph --help` to verify the console script. |
| `ImportError: no pq wrapper available` from `psycopg` | Postgres checkpoint package has `psycopg` but no binary/system `libpq` provider | Install `psycopg[binary]` or configure a supported system `libpq` installation. |
| Provider model import fails | LangGraph does not bundle model providers | Install the matching LangChain provider package and configure credentials outside code. |

## Version or Package Boundary Confusion

- The Python SDK is for calling a running LangGraph API server; it is not needed to compile and invoke a local graph.
- The JS SDK content in this repository has moved to the standalone LangGraph.js repository; use this skill only for the relocation/status and Python SDK guidance.
- `langgraph-prebuilt` is bundled with `langgraph`, but it can still be installed as a separate distribution for narrow dependency control.

## State, Runtime, and Persistence Confusion

- A `StateGraph` builder cannot be invoked directly; call `.compile()` first.
- Persistent runs need a `thread_id` under `config={"configurable": {"thread_id": "..."}}`.
- Use the same checkpointer and same `thread_id` when validating resume behavior.
- Keep state updates compatible with the declared schema; parallel writes to the same key usually need a reducer.

## CLI and Deployment Confusion

- Validate `langgraph.json` before starting a server or building an image.
- `langgraph dev` is for local hot-reload development; `langgraph up` is Docker-based and defaults to a different server style and port behavior.
- Avoid committing secrets in `env` mappings; prefer `.env` files or deployment secret stores.
- Docker-based commands require a working container runtime and may need network access to pull base images.

## Security Notes

- For checkpoint data from untrusted or shared stores, set `LANGGRAPH_STRICT_MSGPACK=true` or configure an explicit serializer allowlist.
- Do not place API keys in examples, bundled scripts, generated config fixtures, or test cases.
- Do not run arbitrary source notebooks or deployment scripts as verification unless their network, credential, hardware, and side-effect requirements are understood.

## Where to Drill Down

- Graph compile/runtime errors: `../sub-skills/graph-runtime/references/troubleshooting.md`
- Tool-call or prebuilt agent errors: `../sub-skills/prebuilt-agents/references/troubleshooting.md`
- Checkpointer/store errors: `../sub-skills/persistence/references/troubleshooting.md`
- CLI/config/deployment errors: `../sub-skills/cli-deployment/references/troubleshooting.md`
- SDK/auth/streaming errors: `../sub-skills/sdk-clients/references/troubleshooting.md`
