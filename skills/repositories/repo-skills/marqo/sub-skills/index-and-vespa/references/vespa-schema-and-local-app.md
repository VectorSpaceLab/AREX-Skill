# Vespa schema generation, index management, and local app package

This reference owns the Marqo ↔ Vespa boundary. It does not replace the API payload references or the local-development test runner; it gives the internal schema/deployment facts needed to reason about index work.

## Dispatch map

| Input object | Schema generator | Stored index result | Notes |
|---|---|---|---|
| `StructuredMarqoIndexRequest` | `StructuredVespaSchema` | `StructuredMarqoIndex` | Explicit fields and tensor fields are generated up front. |
| `UnstructuredMarqoIndexRequest` for legacy versions before `2.13.0` | `UnstructuredVespaSchema` | `UnstructuredMarqoIndex` | Legacy compatibility only. |
| `UnstructuredMarqoIndexRequest` for current versions | `SemiStructuredVespaSchema` | `SemiStructuredMarqoIndex` | Public unstructured/semi-structured flexibility becomes the semi-structured schema. |
| Stored `StructuredMarqoIndex` | `StructuredVespaIndex` | Document/query converter | Query behavior is stable but future new work should not extend structured unless necessary. |
| Stored `SemiStructuredMarqoIndex` | `SemiStructuredVespaIndex` | Document/query converter | Primary path for flexible schema growth, partial updates, schema-template features, custom-score support. |
| Stored `UnstructuredMarqoIndex` | `UnstructuredVespaIndex` | Document/query converter | Legacy only. |

## Structured Vespa schema shape

Structured schema generation creates deterministic fields from the declared `allFields` and `tensorFields`.

| Marqo concept | Vespa shape |
|---|---|
| Document id | `marqo__id` string, attribute + summary, fast-search, rank filter. |
| Lexical field | `marqo__lexical_<field>` with Vespa type mapped from Marqo field type, indexed and summarized, BM25 enabled. |
| Filter field | `marqo__filter_<field>` with Vespa type mapped from Marqo field type, attribute + summary, fast-search, rank filter. |
| Plain stored field | Original field name, summary-only, when no lexical/filter feature is present. |
| Score modifiers | Numeric score-modifier tensors are added when any field has the score-modifier feature. |
| Tensor chunks | `marqo__chunks_<tensorField>` as `array<string>`, attribute + summary. |
| Tensor embeddings | `marqo__embeddings_<tensorField>` as `tensor<float>(p{}, x[dimension])`, attribute + index + summary, with HNSW settings from `annParameters`. |
| Vector count | `marqo__vector_count` integer attribute + summary. |

Structured field type mapping includes strings for text/media/custom-vector content, bytes for bools, integer/long/float/double scalar and array types, map types for multimodal and numeric maps, and tensors for embeddings. Note that the structured embeddings field is generated as `tensor<float>` in the inspected implementation; if a task claims structured `bfloat16` support, verify the generated schema before promising it.

## Semi-structured Vespa schema shape

Semi-structured schema generation starts with fixed fields and then renders discovered lexical, string-array, tensor, and collapse fields from the stored `SemiStructuredMarqoIndex`.

| Field or section | Purpose |
|---|---|
| `marqo__id` | Stable Marqo document id, attribute + summary, fast-search, rank filter. |
| `marqo__version_uuid` | Partial-update/version tracking. |
| `marqo__field_types` | Map from Marqo field name to a string field-type marker used by partial updates and conversion. |
| `marqo__int_fields`, `marqo__float_fields`, `marqo__bool_fields` | Dynamic numeric/bool fields stored in typed maps with key/value attributes where applicable. |
| `marqo__short_string_fields` | Short string filter support up to `filterStringMaxLength`. |
| `marqo__score_modifiers` | Numeric score-modifier tensor for dynamic numeric values. |
| `marqo__multimodal_params` | Serialized multimodal parameter metadata. |
| Direct collapse field | One configured collapse field rendered as a string attribute + summary + fast-search field. |
| `marqo__lexical_<field>` | Discovered text lexical fields with BM25. Can include language-setting and stemming directives when configured and version-supported. |
| `marqo__string_array_<field>` | Separate filterable string-array fields for partial-update-capable schema templates. Older templates use a combined legacy string-array field. |
| `marqo__chunks_<field>` | Tensor chunks for each discovered tensor field. |
| `marqo__embeddings_<field>` | Tensor embeddings for each discovered tensor field, using `tensor<float>` or `tensor<bfloat16>` according to `vectorNumericType`, with HNSW settings and distance metric. |
| `marqo__vector_count` | Vector-count attribute/summary. |
| Rank/query inputs | Base rank profile inputs for lexical/tensor query flags, BM25 aggregator, query embedding, score modifiers, sort weights, recency, collapse sort weights, and custom-score rerank weights. |

Semi-structured templates are version-sensitive. Partial-update-capable indexes use the newer template family; schema-template-dependent features are checked through `schema_template_version` when present.

## Legacy unstructured schema

Legacy unstructured indexes use a fixed schema with shared maps/arrays for strings, short/long strings, bools, ints, floats, chunks, embeddings, score modifiers, summaries, BM25, and embedding-similarity rank profiles. Use it only to read or migrate old indexes. Do not add new flexible-index behavior there unless the task explicitly targets a pre-semi-structured index.

## Query conversion boundary

`VespaIndex` exposes these conversion methods:

| Method | Purpose |
|---|---|
| `to_vespa_document()` | Convert a Marqo document into a Vespa document payload. |
| `to_marqo_document()` | Convert a Vespa document/result into Marqo document form, optionally including highlights. |
| `to_vespa_query()` | Convert an internal `MarqoQuery` object into Vespa YQL/query features/ranking parameters. |
| `to_vespa_partial_document()` | Convert partial-update payloads when the index supports partial updates. |
| `get_vector_count_query()` | Build query used to count vectors. |
| `get_vespa_id_field()` | Return the Vespa field used for Marqo document id. |

Semi-structured query conversion checks `MarqoHybridQuery` before tensor or lexical because hybrid inherits behavior from both. It also mutates `attributes_to_retrieve` to include fixed backing fields needed to reconstruct Marqo documents, appends `marqo__id`, appends the collapse field for hybrid collapse retrieval, and adds tensor chunk fields when tensor field names are retrieved.

High-level query facts:

- Tensor queries use nearest-neighbor YQL per tensor field with `targetHits`, `approximate`, and `hnsw.exploreAdditionalHits` derived from limit/offset, rerank depth, and `efSearch`.
- Lexical terms use contains/weakAnd/AND/OR variants and field-specific lexical names. Ranking-only lexical terms defensively return empty strings when no lexical field survives, preventing invalid YQL.
- Hybrid queries route through the Marqo custom searcher rank profile and pass additional `marqo__...` query features for lexical/tensor ranking, RRF, relevance cutoff, facets, collapse, recency, sorting, and custom-score reranking.
- Detailed search payload and ranking parameter choices belong to `search-and-ranking`; this reference is for diagnosing whether the generated Vespa query is consistent with the stored index schema.

## Index management deployment flow

`IndexManagement` owns mutation of the Vespa application package. It must be constructed with `enable_index_operations=True` before create/delete/update/rollback operations can run.

| Operation | What happens | Safety notes |
|---|---|---|
| `bootstrap_vespa()` | Adds/updates Marqo configuration in the Vespa application package and may migrate existing settings. | Uses a deployment lock. Skips when the configured version is already current or newer. |
| `create_index()` / `batch_create_indexes()` | Generates the main schema, generates a typeahead schema, stores index settings, and deploys all schema/settings changes together. | Batch create is intended for tests rather than production usage. Requires lock; can fail on existing index or invalid application package. |
| `delete_index_by_name()` / batch delete | Removes stored index settings plus main/typeahead schemas. | Requires lock and existing index. |
| `update_index()` | Updates semi-structured index settings and schema after dynamic field discovery. | Only supports `SemiStructuredMarqoIndex`. If another thread already deployed equivalent fields, it returns without redeploying. |
| `update_index_settings_by_settings_dict()` | Updates settings without schema regeneration. Currently only `modelProperties` are allowed. | Supports `dry_run` and `force`. `dimensions` and `type` must not change; updated properties must include current keys. |
| `apply_latest_schema_template()` | Regenerates a semi-structured index schema from the latest template, diffs current versus new schema, prepares deployment to inspect Vespa `configChangeActions`, then optionally activates. | Only semi-structured indexes created with Marqo `2.23.0+`. `dry_run` never deploys. Without `force`, required restart/refeed/reindex actions block activation. |
| `rollback_vespa()` | Rolls back the Vespa application package to the previous version backed up inside the app package. | Requires a valid backup and lock. Treat as operational recovery, not a normal edit loop. |

Locking behavior:

- If a Zookeeper client is provided, index operations use a distributed deployment lock.
- If the lock cannot be acquired before timeout, Marqo raises an operation-conflict style error telling the caller to retry shortly.
- If no Zookeeper client is provided, Marqo logs a warning and proceeds without distributed locking; concurrent index operations can race.
- If index operations are not enabled, the index manager raises an internal error instead of mutating Vespa.

## Vespa application package store selection

Marqo chooses how to read/write the Vespa app package based on Vespa version and whether binary files are needed.

| Vespa version behavior | Consequence |
|---|---|
| Below binary-upload support threshold | May use a file-based store when binary support is needed. Schema-template prepare-only/activate paths that require deployment sessions may not be available. |
| At or above deployment-session support | Uses deployment-session content APIs for safer prepare/activate flows. |
| Below fast-file-distribution recommendation | Marqo logs warnings because index create/add-doc workflows can be slower. |

When debugging schema update failures, record the Vespa version, which store path was selected, whether binary custom-searcher files are involved, and whether the failed operation attempted prepare-only activation.

## Vespa client endpoints and failure domains

`VespaClient` receives three base URLs and strips trailing slashes:

| URL | Used for |
|---|---|
| `config_url` | Deploy API, deployment sessions, application downloads, prepare/activate, service convergence, Vespa version. |
| `document_url` | Feed, get, delete, update documents and index-setting documents. |
| `query_url` | Search/query requests. |

The API service constructs these from environment variables for config, document, query, content-cluster name, pools, search timeout, and optional Zookeeper hosts/timeout.

Common routing mistakes:

- Pointing config URL at the document/query port, or document/query URL at the config port.
- Forgetting trailing-path expectations; base URL should be just scheme/host/port and Marqo appends Vespa REST paths.
- Running multi-node Vespa without sticky config-server session behavior and then seeing deployment-session content reads return 404 from a different config node.
- Leaving Zookeeper hosts unset in a multi-instance deployment, which removes distributed deployment locking.

## Local Vespa app package facts

The local Vespa helper is intentionally not bundled because it starts/stops containers and deploys an app package. Distilled facts:

| Mode | Behavior | Side effect level |
|---|---|---|
| `full-start` | Start local Vespa, generate a dummy application package, deploy it via REST, then wait for readiness/convergence. Supports shard/replica counts. | Starts/removes containers and deploys. |
| `start` | Start local Vespa only. Single-node uses one container; multi-node generates a compose file with config/content/API nodes. | Starts/removes containers and may write compose files. |
| `restart` | Restart existing local Vespa. | Service mutation. |
| `deploy-config` | Deploy config from the helper directory using Vespa CLI behavior. | Requires Vespa CLI and deploys. |
| `stop` | Stop local Vespa containers. | Destructive service stop. |
| `generate-and-deploy` | Generate and deploy an application package; used by production-style launcher flow. | Writes files and deploys. |

Single-node local Vespa facts:

- Config/deploy API: port `19071`.
- Document/query API: port `8080`.
- Zookeeper: port `2181`.
- Debug: loopback `5005`.
- Default Vespa version comes from environment with a fallback observed as `8.513.17`.
- Disk utilization limit comes from environment with fallback `0.75`.
- The generated dummy package includes a simple test schema and `services.xml`; it is removed after zipping/deploying in the full flow.
- Vespa CLI is not required for `full-start` because deployment uses REST; it is relevant to the separate config deploy mode.

Use the bundled read-only inspector before any service-mutating work:

```bash
python scripts/inspect_vespa_local.py --repo-root <marqo-repository-root>
```

## Custom Java searcher package

The Vespa custom searcher package contains `HybridSearcher` and related Java code used by hybrid/RRF/facet/collapse/custom-score behavior. Build/deploy facts:

| Fact | Value / implication |
|---|---|
| Maven group/artifact/version | `ai.marqo:marqo-custom-searchers:1.0.0`. |
| Packaging | `container-plugin`. |
| Java source/target | Java `17`; local work should use JDK 17 and Maven. |
| Output jar expected by Docker/local packaging | `marqo-custom-searchers-deploy.jar` under Maven target output. |
| Parent Vespa dependency | Pinned to a conservative Vespa Cloud tenant base version for compatibility, even if local runtime Vespa is newer. |
| Bundle-name caution | If the Maven artifact/bundle name changes, the Vespa services configuration must change consistently. |

Operational rule: after changing `HybridSearcher.java` or any custom-searcher code, run the Maven package build from the Vespa app package directory, then redeploy the Vespa application package, then rerun the relevant integration/API scenario. A passing Python unit test without rebuilding/redeploying the Java bundle does not prove live hybrid search behavior.

## Read-only prerequisite checklist

Before deploying local Vespa or validating a custom searcher, check:

- Expected local Vespa helper file exists.
- Semi-structured schema templates exist, including the partial-update-capable template.
- Vespa app package `pom.xml` exists and declares the expected artifact, packaging, Java version, and Vespa parent.
- Custom searcher Java source exists.
- Index-settings config definition exists.
- Host has Docker available before service start, Java and Maven before custom-searcher build, and curl or equivalent before health checks.
- No one has asked the agent to run Docker/Vespa/Maven yet; inspection alone is safe.
