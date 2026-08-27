# Data Formats

Use this reference when you need the exact connector payload shapes, metadata assumptions, or file-id conventions.

## Document and section shapes

| Model | Important fields | Notes |
|---|---|---|
| `DocumentBase` / `Document` | `id`, `source`, `semantic_identifier`, `title`, `sections`, `metadata`, `doc_updated_at`, `doc_created_at`, `primary_owners`, `secondary_owners`, `file_id`, `parent_hierarchy_raw_node_id`, `parent_hierarchy_node_id`, `external_access`, `doc_metadata` | `Document.id` is required; `Document.source` must be a `DocumentSource`; metadata is coerced to strings or string lists. |
| `Section` / `TextSection` | `type`, `text`, `link`, `heading` | The inline text section used by the text chunker. |
| `ImageSection` | `image_file_id`, `text`, `link`, `heading` | The image bytes live in the file store; `text` is filled in later by image summarization. |
| `TabularSection` | `csv_file_id`, `link`, `heading` | The table content is staged as CSV in the file store and streamed row-by-row at chunk time. |
| `SlimDocument` | `id`, `external_access`, `parent_hierarchy_raw_node_id`, `doc_created_at` | Used by pruning and permission sync, not by chunking. |
| `ConnectorFailure` | `failed_document`, `failed_entity`, `failure_message`, `exception` | The exception is excluded from serialized output; keep the message concise and actionable. |
| `ConnectorCheckpoint` | `has_more` plus connector-specific fields | Checkpointed connectors should round-trip their checkpoint model exactly. |

## Metadata assumptions

- `metadata` on documents is stored as `dict[str, str | list[str]]`.
- Non-string values are coerced to strings when the model is built.
- List values stay as lists of strings and are flattened into key/value strings for indexing.
- Keep metadata keys and values stable, because search filters depend on the same formatting.
- `doc_updated_at` and `doc_created_at` are UTC timestamps.
- `doc_metadata` is a connector-specific escape hatch for extra structured data that other layers may need.

## File store and user-file ids

- `Document.file_id` points to a persisted raw file in the file store, not to a logical document id.
- `ImageSection.image_file_id` is the file-store id of the stored image blob.
- `TabularSection.csv_file_id` is the file-store id of the staged CSV derived from a sheet or CSV file.
- `FileOrigin.INDEXING_STAGING` is for staged raw bytes that have not yet been promoted to connector-owned storage.
- `UserFile.id` is the logical user-file UUID; `UserFile.file_id` is the backing file-store id.
- If you need the storage object behind a user file, resolve the user-file id to its backing `file_id` first.

## Connector config patterns

- `connector_specific_config` is passed directly into the connector constructor, so the config must be JSON-friendly and stable across saved rows.
- Include boolean feature flags such as `include_attachments` in that stored config, and keep the backend default aligned with the UI default.
- Keep transient objects, callbacks, and open clients out of the stored config; the factory injects those at runtime.
- When a connector needs to hand off staged raw bytes, use the raw-file callback rather than embedding the bytes into the document payload.
- If a connector supports checkpointing, keep the checkpoint payload as a strict Pydantic model so `validate_checkpoint_json()` can reject invalid resumes early.

## Useful reminders

- `parent_hierarchy_raw_node_id` is a source-system id, not a database id.
- `parent_hierarchy_node_id` is resolved later during docfetching when the hierarchy cache is available.
- `external_access` should be omitted when the connector does not support permission sync.
- For attachment-aware sources, make sure the main pass and slim pass agree on the same admission rules.
