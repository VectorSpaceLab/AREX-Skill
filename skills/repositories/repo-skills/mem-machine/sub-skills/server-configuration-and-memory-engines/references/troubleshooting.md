# Server Troubleshooting

## Startup And Config

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Server exits on config load | YAML syntax error, missing top-level section, bad resource reference | Parse YAML, run `server_config_doctor.py`, then resolve each referenced resource ID. |
| Event backend fails | Missing `vector_store` or `segment_store` | Add both fields under `episodic_memory.long_term_memory` and define matching resources. |
| Declarative backend fails | Missing/invalid `vector_graph_store` or graph service unavailable | Configure a graph resource and verify service URI/auth. |
| Semantic memory disabled or inert | Missing `llm_model`, `embedding_model`, `database`, or `config_database` | Fill required fields and verify provider/database resources. |
| `memmachine-configure` prompts/EOFs | Interactive installer invoked in automation | Use explicit config files and doctors in non-interactive workflows; run the installer only with user approval. |

## Storage Services

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Postgres connection refused | DB service down, wrong host/port, container network mismatch | Check service health from the server's network, not only the host shell. |
| Neo4j auth failure | Wrong user/password or URI | Verify Bolt URI, credentials, and container/environment values. |
| Qdrant/Milvus unavailable | Optional client installed but service absent | Start or point to the service only after user approval; otherwise choose a local/dev backend. |
| SQLite vector issues | Path permissions or concurrent writers | Use a writable path and avoid multi-process writes for dev SQLite workflows. |

## Provider And Model Resources

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| OpenAI-compatible error | Bad base URL/model/API key or API shape mismatch | Confirm whether the provider uses Responses or Chat Completions style and the correct base URL. |
| AWS Bedrock error | Missing credentials, region, model ID, or permissions | Validate credentials securely and check model availability in the region. |
| Cohere reranker error | Missing/invalid API key or quota | Verify key/quota and retry only after fixing config. |
| Sentence-transformer load slow/fails | Optional model dependency missing or model download blocked | Install optional dependency and provide/cache model only when local embeddings are required. |

## MCP

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| MCP client cannot start stdio server | Command not on PATH or environment lacks server package | Check `memmachine-mcp-stdio` availability in the intended environment. |
| HTTP MCP unreachable | Wrong host/port, firewall, server not started | Use explicit `--host`/`--port`; check process logs and health. |
| MCP memory tool returns wrong user's data or none | Missing/wrong `org_id`, `proj_id`, `user_id` context | Configure the MCP client context and compare with a CLI search using the same values. |

## Docker/Compose Safety

- `start` creates/starts services and persistent volumes.
- `stop` stops services but may leave data volumes.
- `clean` or `down -v` removes data and is destructive.
- Provider setup prompts may write `.env`/config files.

Ask before any Docker/Compose/Helm operation that mutates services, volumes, or
secrets.

## Optional spaCy Decomposer Warning

A base server import can log a warning similar to `Decomposer import FAILED` if
spaCy is not installed. Treat it as non-fatal unless the user specifically needs
spaCy-based multi-hop decomposition. Recovery options:

1. Continue with LLM-based/fallback query splitting.
2. Install the documented multihop/spaCy dependencies if Python version supports
   them.
3. Disable or avoid the workflow that requires the local decomposer.
