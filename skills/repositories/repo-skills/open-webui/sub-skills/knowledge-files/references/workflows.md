# Knowledge and File Workflows

## Typical flow

1. Start Open WebUI.
2. Upload a file or organize it into a folder or knowledge area.
3. Wait for processing or extraction to finish.
4. Ask a question that can only be answered from the uploaded content.
5. Check whether the result came from retrieval, memory, or general chat behavior.

## Files and folders

- Uploaded files are processed by the backend and stored according to the configured storage provider.
- Folder organization affects how content is grouped and displayed.
- If files are not visible after upload, the issue may be in the storage layer rather than retrieval.

## Notes and memories

- Notes are user-facing content separate from the chat transcript.
- Memories are meant to persist useful facts across chats.
- If a memory appears missing, check the account scope and persistence settings before assuming the model failed.

## Retrieval and RAG

- Open WebUI supports retrieval-oriented flows that combine document processing, embeddings, and backend search.
- Retrieval behavior depends on the selected backend, collection scope, and how the document was chunked.
- If the answer is empty or vague, verify that the document was actually processed and that the target collection was used.

## Useful configuration signals

- `ENABLE_RETRIEVAL_UNSCOPED_COLLECTIONS`
- `KB_EXEC_MAX_OUTPUT_CHARS`
- `KB_EXEC_MAX_GREP_FILES`
- `VIEW_FILE_MAX_CHARS`
- `VIEW_FILE_DEFAULT_MAX_CHARS`
- `OFFLINE_MODE`
- `STORAGE_PROVIDER`

## Data-layout questions to ask

- Where is the file stored?
- Was it processed successfully?
- Is the content in the right knowledge collection?
- Is the storage provider writable?
- Is the retrieval backend available for this instance?

## Useful distinctions

- **Upload failure**: the file never made it into the app or storage.
- **Processing failure**: the file was stored, but extraction/chunking failed.
- **Retrieval failure**: the file exists, but the chat answer does not use it.
- **Storage failure**: the backend cannot read or write the chosen storage backend.
