---
name: retrieval-graph-search
description: "Operate M-flow retrieval modes, graph-routed Bundle Search,
  episodic tuning, and storage backend diagnostics."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Retrieval graph search

Use this sub-skill when a task is about retrieving from already-memorized M-flow data:

- choose `RecallMode` or simplified `query(mode=...)` routing;
- tune `SearchConfig`, `top_k`, `wide_search_top_k`, `triplet_distance_penalty`, episodic display modes, hybrid search, time bonus, direct-hit/noise behavior, and adaptive weights;
- understand graph-routed Bundle Search outputs over `Episode`, `Facet`, `FacetPoint`, `Entity`, and semantic `edge_text`;
- configure or diagnose graph, vector, relational, and cache storage backends without mutating data;
- troubleshoot empty/noisy search results, backend import/config failures, Cypher safety, or LLM endpoint issues that affect triplet answers.

Route elsewhere:

- add/memorize/ingest/delete/dataset core workflows → [../core-memory-api/SKILL.md](../core-memory-api/SKILL.md);
- loader choice, content routing, custom pipeline stages, and `preferred_loaders` → [../ingestion-pipelines/SKILL.md](../ingestion-pipelines/SKILL.md);
- API server, UI, MCP, Docker, auth, and service startup topology → `service-integrations` if available.

## First decisions

1. **Confirm data is already memorized.** Retrieval reads graph/vector/relational stores; if the user has not run ingestion/memorization, route to `core-memory-api` or `ingestion-pipelines` before tuning search.
2. **Pick the smallest recall mode.** Use `EPISODIC` for event/context recall, `TRIPLET_COMPLETION` for LLM answers over graph context, `CHUNKS_LEXICAL` for exact term lookup, `PROCEDURAL` for how-to/workflow memory, and `CYPHER` only for explicit graph queries.
3. **For noisy broad answers, tune output before changing stores.** Prefer `display_mode="highly_related_summary"` or `"detail"`, lower `top_k`, inspect `verbose=True`, and review Bundle Search scoring/direct-hit penalties in [references/retrieval-architecture.md](references/retrieval-architecture.md).
4. **For backend switches, probe without connecting first.** Run [scripts/backend_config_probe.py](scripts/backend_config_probe.py) to validate provider names, environment/config visibility, and optional import availability. It does not connect to remote services or mutate databases.
5. **Treat migrations as reference-only.** Timestamp migration scripts are unsafe for routine search troubleshooting unless the user explicitly requests a dry-run migration plan; see [references/storage-backends.md](references/storage-backends.md).

## Safe bundled probe

From this sub-skill directory or with an explicit path:

```bash
python scripts/backend_config_probe.py --help
python scripts/backend_config_probe.py --json
python scripts/backend_config_probe.py --provider neo4j
python scripts/backend_config_probe.py --kind vector --provider pgvector --json
```

The probe reports recognized providers, selected environment/config keys, required fields, optional-extra hints, and missing Python imports. It masks secrets and never initializes graph/vector adapters, opens database connections, or writes data.

## Reference map

- [references/api-reference.md](references/api-reference.md): `search()`, `query()`, REST/CLI forms, `RecallMode`, `SearchConfig`, and episodic knobs.
- [references/retrieval-architecture.md](references/retrieval-architecture.md): graph-routed Bundle Search, inverted cone topology, path costs, direct-hit penalty, adaptive scoring, output shapes.
- [references/storage-backends.md](references/storage-backends.md): default SQLite/LanceDB/Kuzu stack, Neo4j/pgvector and other providers, env vars/extras, dry-run migration cautions.
- [references/troubleshooting.md](references/troubleshooting.md): empty/noisy results, missing extras, external service errors, Cypher gating, and LLM/embedding endpoint issues.
