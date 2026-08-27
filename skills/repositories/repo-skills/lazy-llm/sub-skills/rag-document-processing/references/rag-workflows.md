# RAG Workflows

## Minimal local retrieval smoke

Use this when the user needs a dependency/environment check or a tiny retrieval example without embeddings or external services.

```python
from lazyllm.tools.rag.component.bm25 import BM25
from lazyllm.tools.rag.doc_node import DocNode

nodes = [DocNode(text="alpha beta"), DocNode(text="beta gamma")]
hits = BM25(nodes, language="en", topk=1).retrieve("alpha")
assert hits[0][0] is nodes[0]
```

The bundled [rag_bm25_smoke.py](../scripts/rag_bm25_smoke.py) runs this pattern for English and Chinese.

## Local document workflow

1. Install/check `rag` extra.
2. Identify source files/URLs and whether readers are local-only or remote.
3. Choose chunking/transform logic and node-group names.
4. Build a `Document` or lower-level `DocNode` collection.
5. Choose retrieval:
   - BM25/local lexical retrieval for smoke checks,
   - vector store/embedding retrieval for semantic retrieval,
   - reranker only after retriever output is stable.
6. Add model answer generation only after retrieval is validated.

## Retriever planning

`Retriever` accepts a document object, `group_name`, similarity and cutoff options, `index`, `topk`, optional `embed_keys`, `target`, output format, joining behavior, and weighting/priority. Use it when the document/index is already configured.

Questions to answer before building:

- Which node group contains searchable chunks?
- Is similarity lexical, vector, or hybrid?
- Does the caller need raw nodes, joined strings, metadata, or a custom output format?
- Should retrieval target only one field or multiple embedded fields?
- Does a reranker change the final ordering?

## Reranker planning

`Reranker(name='ModuleReranker', *args, **kwargs)` may depend on model modules or backend packages. Keep reranker optional until base retrieval works. If the reranker uses a local or online model, route backend checks to model-deployment.

## Parser service / document service workflow

Parser-service examples split document ingestion into service and worker processes. Treat this as external-service work:

1. Define parser URL and health behavior.
2. Configure document service database (SQLite for local tests; external DB only with connection details).
3. Upload/transfer/reparse/delete documents through typed request models.
4. Track task callbacks and document/node-group status.
5. Mock parser client calls for local unit tests unless a real service is approved.

## Vector database escalation

Milvus/OpenSearch/Elasticsearch/Redis backends are optional. Before using them, collect:

- package extra and connection URL/credentials,
- collection/index naming plan,
- schema and metadata fields,
- lifecycle policy for creating/deleting collections,
- small fixture query and expected result.

If those details are missing, keep the task at local BM25 or planning level.

## Combining RAG with flows, models, and agents

- Flow app: build retrieval as a deterministic callable, validate shape, then insert into `pipeline`/`parallel`.
- Chat app: configure model backend in model-deployment after retrieval is stable.
- Agent app: expose retrieval as a registered tool via agents-tools and keep tool result schemas explicit.
