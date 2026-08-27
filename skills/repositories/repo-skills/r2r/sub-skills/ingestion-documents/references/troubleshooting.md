# Ingestion Troubleshooting

## Common issues

- **Unsupported file or parser**: confirm the file type is one of the documented supported examples and switch to a compatible ingestion mode.
- **Metadata shape errors**: metadata should be a dictionary, not a flat string or list.
- **Bad filter results**: ensure nested metadata fields use the correct dotted path and that `$and` / `$or` expressions wrap a list of subfilters.
- **Delete-by-filter surprises**: start with a list or search call using the same filter before deleting anything.
- **Chunk problems**: verify that `chunks` is a list of strings and that each chunk is not empty.
- **Collection membership confusion**: remember that `collection_ids` attaches the document to collections during ingest; collection add/remove helpers operate on existing documents.
- **Indexing delay**: ingestion may succeed before search results become visible.

## Recovery path

1. Validate the payload with `scripts/ingestion_payload_builder.py`.
2. Check whether the issue is ingestion, retrieval, or graph extraction.
3. If the issue is provider or server setup, switch to `server-configuration`.
