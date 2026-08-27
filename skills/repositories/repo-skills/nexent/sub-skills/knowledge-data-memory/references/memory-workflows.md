# Memory Workflows Reference

Nexent's current memory system has three levels and two persistence styles:

- **Tenant long-term memory**: shared within the tenant, manually/versioned, loaded as full context.
- **User long-term memory**: scoped to one user, manually/versioned or produced by Dreaming, loaded as full context.
- **Agent short-term memory**: scoped to tenant + user + agent + optional conversation, vector indexed, retrieved by similarity, and eligible for Dreaming promotion.

Agent debug mode disables memory retrieval/writes in product behavior, so use normal chat flows or pure service tests when verifying cross-conversation memory.

## SDK Models and Policies

| Model / policy | Contract |
| --- | --- |
| `MemoryLayer` | `tenant`, `user`, `agent`. |
| `MemoryType` | `short_term`, `long_term`. |
| `MemoryRecord` | Protocol record with tenant/user/agent/conversation scope, content, tags, recall stats, idempotency, and status. |
| `MemorySearchRequest` | Query, scope, layers, top_k, threshold, optional embedding, hybrid flag, and accurate-search weight. |
| `MemorySearchResult` | Normalized internal/external search hit with content, score, layer, source, and metadata. |
| `MemorySearchContext` | Prompt-ready buckets for tenant long-term, user long-term, agent short-term, and external memory. |
| `MemoryAccessPolicy` | Agents can write only agent short-term memory; agents can read all layers; Dreaming can write user long-term memory. |
| `MemoryStoragePolicy` | Agent memory requires vector index; tenant/user long-term memory is PostgreSQL/version storage only. |
| `MemoryRetrievalPolicy` | Tenant/user use full-context injection; agent uses vector search; `top_k` is clamped to a maximum of 100. |

`MemoryService` is a backend-agnostic SDK facade. It validates policy, creates idempotency keys, optionally computes embeddings through an injected embedding model, and delegates actual persistence/search to injected async backend hooks. Without hooks it can still be used in pure tests for payload normalization.

## Agent Memory Tools

| Tool | Behavior |
| --- | --- |
| `StoreMemoryTool` | Stores important information as agent short-term memory through `MemoryService`; enforces one agent scope and at most three successful stores per run. If embedding is not configured, service is missing, policy denies, or backend fails, it returns a graceful failure string. |
| `SearchMemoryTool` | Searches agent short-term memory. Prefer wiring `MemoryContextService` so retrieval goes through the full pipeline; direct `MemoryService` mode is still supported for tests. Missing embedding returns an empty list string. Pipeline failures do not fall back to direct retrieval. |
| `KnowledgeBaseSearchTool` | Not a memory tool, but often coexists with memory in agents. Use [vector and storage](vector-and-storage.md#knowledge-base-search-tool) for details. |

## Backend Memory APIs

Routes are under `/memory`, `/memory/dreaming`, and `/memory/long-term`.

| Area | Route shape | Contract |
| --- | --- | --- |
| Config | `GET /memory/config/load` | Load memory switch, Dreaming switch, share mode, and disabled-agent lists for the current user. |
| Embedding status | `GET /memory/config/embedding-status` | Return whether tenant embedding is configured and the current memory ES index name. |
| Config update | `POST /memory/config/set` | Supports memory switch, Dreaming switch, and agent-share mode (`always`, `ask`, `never`). |
| Disable lists | `POST`/`DELETE /memory/config/disable_agent...` and `/disable_useragent...` | Manage per-user disabled memory scopes. |
| Agent records | `POST/GET/PATCH/DELETE /memory/records...` | Manual/system access for agent-layer records. Tenant/user record creation/listing is gone from this route family. |
| Search | `POST /memory/records/search` | Runs scoped retrieval with optional hybrid search and accurate-search weight. |
| Prompt context | `GET /memory/context` | Builds `MemorySearchContext` and returns `prompt_text`. |
| Long-term versions | `/memory/long-term/{tenant|user}` | Active version, version list, version detail, create version, activate version. Tenant mutations require admin. |
| Dreaming | `/memory/dreaming/...` | Parameters, schedule get/update, manual run, and audit listing. |

Tenant and user long-term memory now use versioned Markdown endpoints, not the legacy `/memory/add` or `/memory/search` routes.

## Retrieval Pipeline

`MemoryContextService.build_context` composes prompt memory:

1. Resolve target layers from query parameters or defaults.
2. Resolve tenant embedding model and compute query embedding if needed.
3. Retrieve tenant/user full-context versions and agent short-term vector hits.
4. If pipeline is enabled and results exist, run `RetrievalPipeline`.
5. Convert pipeline output to `MemorySearchContext` and prompt text.

Pipeline stages:

| Stage | What it does | Key parameters |
| --- | --- | --- |
| Normalize | Converts internal and external hits to `PipelineMemoryRecord`. | Created-at map can provide record age. |
| Score fusion | Applies source weights. | `W_AGENT_SHORT_TERM`, `W_EXTERNAL`. |
| Temporal decay | Decays eligible agent short-term memory by age. | `AGENT_SHORT_TERM_HALF_LIFE_DAYS`. |
| MMR deduplication | Removes near-duplicates and balances relevance/diversity. | `MMR_LAMBDA`, candidate/final top-k, duplicate threshold. |
| Token budget | Keeps highest-score records that fit budget. | `MEMORY_TOKEN_BUDGET`. |

The default `PipelineConfig` mirrors backend constants: lambda `0.7`, candidate top-k `10`, final top-k `5`, duplicate threshold `0.92`, half-life `14` days, agent weight `1.0`, external weight `0.8`, and token budget `2000` unless overridden.

## Dreaming

Dreaming promotes useful agent short-term memories into user long-term memory.

1. **Light phase** aggregates retrieval-hit statistics for a time window and updates recall counts, daily counts, grounded counts, query hashes, recall days, and light-hit markers.
2. **REM phase** loads active agent short-term records within the age window, extracts candidate tags/noise signals, and marks non-noise records.
3. **Deep/summarization phase** selects candidates using minimum promotion score, recall count, unique-query count, recency half-life, and source limits. It builds a new user long-term Markdown version with summarizer retry/fallback and evidence IDs.
4. Audits record status, phase counts, decisions, published version, lock-busy skips, and failures. Schedule rows control automatic runs.

Important defaults include Light Sleep window `7` days, promotion score `0.75`, recall count `3`, unique queries `3`, Dreaming source limit `10`, long-term max chars `10000`, and summarization attempts `2` unless configured otherwise.

## Pure and Mocked Memory Tests

Use this pattern when asked to test memory retrieval scoring without a live provider:

1. Build plain `MemorySearchResult` fixtures for tenant, user, and agent layers. Add `ExternalMemoryItem` fixtures only if external-memory fusion is under test.
2. Instantiate `RetrievalPipeline(PipelineConfig(...))` with small deterministic parameters.
3. Provide `created_at_for_id` timestamps for temporal decay; omit them for no-decay cases.
4. Assert final ordering, duplicate removal, token budget truncation, and bucket placement through `into_memory_search_context()`.
5. For service-layer tests, inject mocked `MemoryRetrievalService`, `MemoryIndexService`, backend store/search hooks, fake embedding model, and fake database helpers at their import sites.
6. Avoid real embeddings by passing explicit vectors or fake `get_embeddings()` implementations.

This covers scoring behavior better than a live external memory provider because it isolates all weights, thresholds, and tie-breakers.
