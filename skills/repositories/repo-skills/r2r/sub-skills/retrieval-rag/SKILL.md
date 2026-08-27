---
name: retrieval-rag
description: "Use R2R search, RAG, agent, completion, embedding, streaming
  citations, and retrieval troubleshooting workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Retrieval RAG

Use this sub-skill when the user wants to search R2R content, run RAG or agent flows, handle streaming citations, or tune retrieval settings.

## What it owns

- search modes and search settings
- RAG, agent, completion, and embedding calls
- streaming event handling and citation handling
- retrieval-focused troubleshooting

## Start here

```python
from r2r import R2RClient

client = R2RClient(base_url="http://localhost:7272")
response = client.retrieval.search(query="What is in the corpus?")
print(response.results)
```

## Route out when the work becomes another topic

- Preparing or validating the ingested corpus: `../ingestion-documents/SKILL.md`
- Building or repairing graph data: `../graph-workflows/SKILL.md`
- Server/provider setup needed for RAG to work: `../server-configuration/SKILL.md`
- JavaScript client usage: `../javascript-sdk/SKILL.md`

## Bundled assets

- `references/search-rag-agent-reference.md`
- `references/streaming-and-citations.md`
- `references/troubleshooting.md`
- `scripts/retrieval_request_builder.py`
