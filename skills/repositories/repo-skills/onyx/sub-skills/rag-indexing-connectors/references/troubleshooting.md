# Troubleshooting

Use this reference when connector validation, credential refresh, slim-doc sync, chunking, embeddings, or OpenSearch behavior is not doing what you expect.

## Quick triage order

1. Run the registry smoke check script to separate import problems from runtime problems.
2. Check the connector-specific unit tests or daily tests for the source you changed.
3. If the code imports cleanly but live calls fail, inspect the relevant Onyx service logs.
4. If the service is healthy but search quality is off, inspect the indexing and OpenSearch settings next.

## Symptom matrix

| Symptom | Likely cause | What to check | Likely fix |
|---|---|---|---|
| Connector not found or wrong input type | Missing `DocumentSource` value, registry entry, or interface inheritance | `DocumentSource`, connector registry, and whether the class subclasses the right base interface | Add the mapping and inherit from the correct interface. |
| Validation fails with missing credentials | The connector never received credentials or expected keys are absent | Connector settings, credential JSON, and the factory path for credentials providers | Fix the credential payload or switch the connector to the provider path. |
| Credentials keep expiring or refreshing incorrectly | Dynamic credentials are not using the provider/lock path | Credential audit logs and the connector's `set_credentials_provider()` behavior | Use the DB-backed provider for rotating secrets. |
| Permission sync returns empty ACLs or stale ACLs | Slim permission path does not match the main pass, or `validate_perm_sync()` is too weak | `retrieve_all_slim_docs_perm_sync()`, `external_access`, and parent hierarchy ids | Make slim admission mirror the main pass and emit ACL data consistently. |
| Attachment docs become ghosts or disappear from pruning | `include_attachments` or `allow_images` differs between main and slim passes | The attachment admission rule in both passes | Make the slim pass use the exact same inclusion rule as the main pass. |
| Docs look empty or too small | The source really had no text, raw-file staging was not available, or image summarization is disabled | File store reads, raw-file callback usage, and vision-model availability | Preserve raw file staging and enable the needed model/service. |
| Tabular files fail to index | The CSV staging path is missing or the sheet could not be streamed | `csv_file_id`, staged CSV contents, and file store availability | Stage the tabular file first and keep the raw-file callback wired in. |
| Search ranking looks strange | Hybrid normalization, candidate count, or title boost assumptions are off | OpenSearch normalization pipeline, subquery weights, and candidate counts | Tune the search settings; do not try to add time decay inside the query phase. |
| Embeddings fail or vector dimensions do not match | The embedding service or model settings do not match the index | Embedding model server, model name, and index dimensions | Align the embedder and index configuration before reindexing. |
| Import smoke test fails on one source only | A service-specific SDK or optional dependency is missing | The source module import error printed by the helper script | Install the missing dependency or mark the source as service-dependent. |

## Credential refresh and validation notes

- Credential decrypts are audited best-effort; an audit entry does not mean the connector validated successfully.
- Static connectors load their credentials once; dynamic connectors should expect the provider to refresh or rewrite them during the run.
- `validate_connector_settings()` should fail fast and clearly when the base URL, scopes, or required keys are wrong.
- `validate_perm_sync()` is the right place for ACL-only checks that should not block non-sync connector use cases.

## Search and scoring notes

- OpenSearch hybrid search combines independent keyword and vector phases, so low candidate counts can hide good docs before normalization.
- The title is already part of the indexed content, so title boosting is mild by design.
- Time decay is intentionally applied outside the OpenSearch query layer.
- If a search change only looks wrong in the ranking layer, inspect the search settings before touching the connector.
