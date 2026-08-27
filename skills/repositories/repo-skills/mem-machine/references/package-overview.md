# MemMachine Package Overview

MemMachine is an open-source long-term memory layer for AI agents. It uses a
client-server architecture: application code talks to a MemMachine API server,
and the server manages episodic, semantic/profile, and short-term memory over
configured storage and model-provider resources.

## Public Package Surfaces

| Surface | Package or command | Typical use |
| --- | --- | --- |
| Python SDK | `memmachine-client` / `memmachine_client` | Project creation, memory add/search/list/delete, semantic categories/tags/features, config API wrappers, CLI entry points. |
| Shared models | `memmachine-common` / `memmachine_common` | Pydantic REST payload/response models, enums, validators, filter/data contracts. |
| Server | `memmachine-server` / `memmachine_server` | FastAPI server, REST API v2, MCP stdio/HTTP, memory engines, storage/provider config. |
| Meta package | `memmachine` | Convenience package depending on client and server. |
| TypeScript client | `@memmachine/client` | Node/TypeScript REST client for project and memory operations. |

Python package metadata at this skill's source baseline reports version
`0.1.dev1+g2d28c1c1e` for `memmachine`, `memmachine-client`,
`memmachine-common`, and `memmachine-server`.

## Runtime Architecture

1. **Application/client layer**: Python SDK, TypeScript client, CLI, REST calls,
   framework integrations, or MCP clients submit memory operations.
2. **API/server layer**: the server exposes REST API v2 and optional MCP tools,
   validates request models, and routes operations to memory engines.
3. **Memory engines**:
   - episodic memory stores conversation-style event history;
   - semantic/profile memory stores durable user facts and categories;
   - short-term memory summarizes recent session state when enabled;
   - retrieval-agent mode can decompose/rerank queries when configured.
4. **Resource layer**: databases, vector/graph stores, embedders, language
   models, rerankers, metrics, and provider credentials are selected by server
   configuration.

## Install And Import Checks

For application code that only uses the Python client:

```bash
python -m pip install memmachine-client
python - <<'PY'
from memmachine_client import MemMachineClient
print(MemMachineClient)
PY
```

For a full local Python server package:

```bash
python -m pip install memmachine-server
memmachine-server --help
```

For the TypeScript REST client:

```bash
npm install @memmachine/client
node -e "import('@memmachine/client').then(m => console.log(Object.keys(m)))"
```

Use this skill's bundled checker for read-only inspection of a Python
environment:

```bash
python scripts/check_memmachine_install.py --summary
```

## Optional Dependency Groups And Services

Treat these as optional unless the user's task specifically requires them:

| Optional surface | Why it may be needed | Verification caution |
| --- | --- | --- |
| `sentence-transformers` / server `gpu` extra | Local sentence-transformer embedder | The extra name does not by itself prove GPU execution; verify model/device behavior separately. |
| `hnswlib` extra | HNSW vector search engine | Requires wheel/compiler compatibility. |
| `qdrant`, `milvus`, `nebula` extras | External vector/graph stores | Usually require a running service or separate server/lite runtime. |
| `litellm` extra | LiteLLM language-model provider path | Requires provider configuration and often credentials. |
| spaCy multihop group | Non-LLM query decomposition | When absent, server imports may log a decomposer warning and use fallback behavior. |
| Docker services | Local Postgres/Neo4j/Qdrant/MemMachine stack | Starting/stopping services is a side effect; ask before running. |
| Provider credentials | OpenAI, OpenAI-compatible/Ollama, AWS Bedrock, Cohere | Never echo secrets; provider calls are not safe smoke tests. |

## Safe Validation Order

1. Import packages and inspect versions.
2. Run CLI `--help` or `--version` checks.
3. Validate config shape without starting services.
4. Run health checks against an already-running server only after the user
   confirms the endpoint.
5. Run memory add/search/list/delete only after the user confirms the target
   project and whether writes/deletes are allowed.
6. Run Docker/provider/integration benchmarks only with explicit credentials,
   endpoint, and side-effect approval.
