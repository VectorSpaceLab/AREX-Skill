---
name: retrieval-and-rag
description: "Index documents, query document stores, configure
  retrievers/rankers/joiners/writers/readers, and assemble local or
  provider-backed Haystack RAG pipelines."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Retrieval and RAG

Use this sub-skill when the task is about making Haystack return the right `Document` objects before generation or reading: document stores, writers, metadata filters, retrievers, rankers, joiners, readers, and RAG pipeline wiring.

## Route here

- Build an `InMemoryDocumentStore`, write `Document` objects, choose duplicate policies, or inspect document counts.
- Configure `DocumentWriter`, `InMemoryBM25Retriever`, `InMemoryEmbeddingRetriever`, `FilterRetriever`, `MultiQueryTextRetriever`, `MultiQueryEmbeddingRetriever`, `SentenceWindowRetriever`, or `AutoMergingRetriever`.
- Combine and reorder retrieval results with `DocumentJoiner`, `MetaFieldRanker`, `LostInTheMiddleRanker`, or similarity rankers.
- Wire retrieval into `Pipeline` or `AsyncPipeline` for RAG, including local smoke tests before adding provider-backed generators.
- Select retrieval metrics such as recall, MRR, or NDCG for validation planning.

## Reroute

- Raw file conversion, cleaning, splitting, embedding documents, or ingestion pipelines: use `../data-ingestion/SKILL.md`.
- Prompt templates, prompt builders, chat generators, provider model credentials, and answer generation details: use `../generation-and-model-components/SKILL.md`.
- Implementing evaluator components or full evaluation harnesses: use `../evaluation-and-observability/SKILL.md`.
- Agents, tools, tool-calling RAG, human-in-the-loop flows: use `../agents-tools-and-hitl/SKILL.md`.

## Start fast

1. Pick the store and retrieval family: BM25 needs text only; embedding retrieval needs matching document and query embeddings.
2. Write documents through `DocumentWriter(document_store=store, policy=DuplicatePolicy.SKIP|OVERWRITE|FAIL)` or `store.write_documents(...)`.
3. Use Haystack filter syntax consistently: `{"field": "meta.lang", "operator": "==", "value": "en"}` for nested metadata, or simple field names where the store supports them.
4. Run a narrow retrieval check before connecting generation: assert `count_documents()`, output length, top document content/id, and score behavior.
5. Add rankers/joiners only after base retrieval is correct; then connect retrieved documents into prompt builders or readers.

Run the bundled smoke check from this sub-skill directory to validate a local BM25 RAG skeleton without network credentials:

```bash
python scripts/rag_smoke_check.py
```

If working in the Haystack repository checkout, follow the repository’s Hatch policy for execution, for example:

```bash
hatch -e test run python skills/disco/haystack/sub-skills/retrieval-and-rag/scripts/rag_smoke_check.py
```

## References

- `references/api-reference.md` lists public imports, constructor parameters, run inputs/outputs, and metric-selection guidance.
- `references/workflows.md` gives copyable local BM25, embedding, hybrid, multi-query, sentence-window, auto-merging, ranker, reader, and RAG wiring patterns.
- `references/troubleshooting.md` maps common import, optional dependency, credential/backend, API misuse, data/config, and workflow failures to checks and fixes.
