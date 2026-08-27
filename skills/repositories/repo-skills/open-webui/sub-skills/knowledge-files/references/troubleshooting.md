# Knowledge and File Troubleshooting

## File not processed

- **Symptom**: upload succeeds, but the content is unavailable for question answering.
- **Likely causes**: unsupported format, loader error, extraction timeout, or the content was not indexed into the expected collection.
- **Recovery**: try a tiny fixture first, then check the loader/backend settings and any storage restrictions.

## File too large

- **Symptom**: the backend rejects or truncates the file.
- **Likely causes**: the file exceeds the configured content or view limit.
- **Recovery**: split the file, reduce the input size, or increase the relevant limit only if the deployment can support it.

## Duplicate or empty content

- **Symptom**: the backend reports duplicate or empty content.
- **Likely causes**: the document was uploaded twice, or the extractor produced no usable text.
- **Recovery**: confirm the document is unique and that the loader can actually extract text from the format.

## Retrieval returns nothing

- **Symptom**: the knowledge base exists, but answers never cite the uploaded content.
- **Likely causes**: the wrong collection scope, the wrong backend, or an indexing failure after upload.
- **Recovery**: verify the collection and backend selection, then reprocess a smaller document.

## Storage/provider problems

- **Symptom**: files vanish, cannot be read back, or processing fails with storage errors.
- **Likely causes**: the selected storage provider is not writable or the credentials are missing.
- **Recovery**: route the issue to the admin sub-skill if the storage backend itself is wrong, then retry the file flow.

## Safe checks to repeat

- Upload a tiny text fixture before testing a large or complex document.
- Re-run the question in a plain chat only after confirming the retrieval path has content.
