# Cross-cutting Troubleshooting

Use this reference for failures that can affect several MemMachine workflows.
For workflow-specific issues, also read the nearest sub-skill troubleshooting
reference.

## Install Or Import Fails

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ModuleNotFoundError: memmachine_client` | Python SDK is not installed in the active environment | Install `memmachine-client` or run inside the environment where it is installed; verify with `python -c "import memmachine_client"`. |
| `ModuleNotFoundError: memmachine_server` | Server package is not installed | Install `memmachine-server` only when server-side APIs/configuration are needed. |
| Server import logs `Decomposer import FAILED` for `spacy` | Optional spaCy multihop dependency is absent | This is non-fatal for base server inspection. Install the documented multihop/spaCy dependencies only when the user needs non-LLM multi-hop decomposition. |
| `sentence_transformers`, `hnswlib`, `qdrant_client`, `pymilvus`, or `nebula` import missing | Optional backend extra not installed | Install only the extra required by the selected backend; do not install all optional backends by default. |
| TypeScript import fails | Node version or package installation problem | Use Node `>=20.19`; reinstall `@memmachine/client`; check ESM/CJS import form. |

## Server Connectivity Fails

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Connection refused to `localhost:8080` | Server is not running or port differs | Ask whether a local server should be started; otherwise use the correct cloud/self-hosted base URL. |
| 404 for TypeScript or raw REST calls | Base URL path prefix mismatch | Self-hosted REST endpoints usually include `/api/v2`; the TS client cloud default ends in `/v2`. Set the base URL to the exact API prefix expected by that client. |
| 401/403 | Missing or wrong bearer API key | Load the API key from a secret source and pass it as a bearer token; do not print it. |
| Health succeeds but memory calls fail | Missing project, bad org/project ID, disabled memory subsystem, or backend resource failure | Check project context, server config, and `/config/resources` when config API is enabled. |

## Configuration And Backend Fails

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Event long-term memory fails at startup | `vector_store` or `segment_store` missing or invalid | Configure both IDs and ensure they exist under `resources.databases`. |
| Declarative long-term memory fails | `vector_graph_store` missing/invalid or graph service unavailable | Configure a graph store resource such as Neo4j/Nebula and verify service credentials. |
| Semantic memory never ingests | semantic memory disabled or missing `llm_model`, `embedding_model`, `database`, or `config_database` | Fill the required fields and check provider/resource readiness. |
| Provider resource not ready | Bad API key, model ID, base URL, region, or quota | Validate credentials outside logs, retry the resource after fixing config, and distinguish provider errors from MemMachine errors. |
| Docker startup hangs | Storage containers not healthy, port conflict, missing env/config file, insufficient resources | Check compose service health/logs, ports, and generated `.env`/config before retrying. |
| `memmachine-configure` prompts unexpectedly in automation | It is an interactive installer/configurer | Do not run it in non-interactive contexts unless the user explicitly wants interactive setup. Use config validation and documented commands instead. |

## Memory API Misuse

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Search returns no useful memories | Wrong metadata context, project, memory type, or query too broad | Confirm `org_id`, `project_id`, user/session metadata, `types`, and filters; search a simple single fact first. |
| Filter parse error | Used SQL-like `==`, invalid quotes, unsupported field, or malformed `IN`/date expression | Use a single `=`, quote strings, and test a simple predicate before composing boolean logic. |
| Memory added but not found | Added to a different project/context/type or async semantic ingestion not complete | Inspect add response IDs, list with the same context, and verify semantic/episodic types. |
| Delete removes too much | IDs or type were ambiguous | Prefer explicit memory IDs and distinguish episodic from semantic deletes; ask before destructive deletes. |

## Safety Rules

- Do not start/stop Docker services, delete volumes, upload memories, call paid
  providers, or delete memories without explicit user permission.
- Do not show secret values. Redact API keys, database passwords, cloud tokens,
  and provider credentials in commands and logs.
- Treat optional GPU/provider/service checks as unverified unless they were
  actually run in the user's intended environment.
