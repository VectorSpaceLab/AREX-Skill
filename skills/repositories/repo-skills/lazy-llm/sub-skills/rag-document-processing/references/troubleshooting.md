# RAG Troubleshooting

## Missing RAG dependencies

**Symptom**: importing `Document`, `DocNode`, RAG readers, or BM25 raises an error listing packages and suggesting `lazyllm install rag`.

**Recovery**

```bash
lazyllm install rag
python ../../scripts/check_lazyllm_env.py --require-rag
python scripts/rag_bm25_smoke.py
```

If the task uses vector DBs, OCR, embeddings, or media, a heavier extra may still be required after local RAG imports pass.

## Retrieval returns no useful context

**Likely causes**: wrong node group, empty chunks, mismatched language/tokenizer, cutoff too strict, wrong index, embeddings not built, or output contract mismatch.

**Recovery**

1. Test with two or three `DocNode` objects and BM25.
2. Print node text and metadata before retrieval.
3. Reduce cutoffs and increase `topk` temporarily.
4. Verify language/tokenizer choice for Chinese/English.
5. Only then add embeddings/vector store/reranker.

## Reader cannot parse a file

**Likely causes**: missing optional parser dependency, encrypted/binary file, unsupported extension, external OCR dependency missing, or invalid path/URL.

**Recovery**

- Confirm the file type and reader dependency.
- Try a plain text fixture first.
- Keep OCR/audio/media parsing optional and route model/media dependencies to model-deployment.

## Parser service health fails

**Likely causes**: parser URL unavailable, worker not started, callback URL unreachable, DB config invalid, or service dependency missing.

**Recovery**

- Use mocked parser client or local SQLite tests for planning.
- For real service execution, ask for parser URL, worker command, database config, callback URL, and data directory.
- Check status transitions and idempotency before bulk upload.

## Vector database connection fails

**Likely causes**: missing advanced extra, service not running, wrong collection/index, credentials/network blocked, or schema mismatch.

**Recovery**

- Keep local BM25 validation separate from vector DB validation.
- Verify connection and collection lifecycle with a tiny fixture.
- Ask before creating/deleting production collections.

## Reranker/model backend fails

Rerankers may wrap model modules. If retrieval works but reranking fails, route the backend issue to model-deployment and preserve the retriever output fixture for debugging.
