# Writer Artifact Formats

## Core models

| Model | Purpose |
| --- | --- |
| `WriterDocument` | Top-level document artifact with document ID, stage, title, blocks, revision, metadata, and provider bindings. |
| `WriterBlock` | Structured block such as heading or paragraph, with node ID, type, content, children, spans, stage, numbering, provider binding, and provider payload. |
| `WriterSpan` | Inline span text with optional style metadata. |
| `WritingContext` | Context object saved alongside document artifacts. |
| `ResourceProfile` | Resource/background item metadata for writer tools. |
| `ToolResult` | Result envelope with artifact paths, summary, counts, schema names, and other metadata. |

## Artifact envelope

Writer JSON artifacts should preserve an envelope with at least:

- `schema`
- `schema_version`
- `data`
- `meta`

`meta.created_by` can identify the tool/step that wrote the artifact. Keep schema names explicit when saving lists, such as resource profile lists.

## Nested document structure

A document may contain nested blocks. Tests verify depth-first traversal and block lookup:

- `WriterDocument.iter_blocks()` traverses parent blocks before children.
- `WriterDocument.block_by_id("id")` can find nested blocks.
- block spans preserve style dictionaries.
- provider bindings/payloads survive JSON round trips.

## Provider fields

- `provider_binding` should store stable external IDs such as provider name, document ID, or block ID.
- `provider_payload` should store raw provider fields needed by adapters.
- Local workflows should preserve these fields without calling the provider.

## Safe serialization pattern

1. Build Pydantic writer models.
2. Use `.model_dump_json()` / `.model_validate_json()` for in-memory checks.
3. Use `save_artifact_json` / `load_artifact_json` or `WriterToolBase._save_artifacts` for tool output.
4. Assert schema names and counts in `ToolResult.metadata`.
5. Only then pass artifacts to adapters or LLM-backed writer pipelines.
