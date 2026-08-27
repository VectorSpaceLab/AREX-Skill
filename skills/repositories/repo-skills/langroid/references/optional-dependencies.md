# Optional Dependencies and Backend Boundaries

## Purpose

Langroid is intentionally broad: one base package covers many agent patterns,
while optional extras unlock heavier parser, embedding, vector-store, database,
UI, or service workflows. Use this map to avoid installing or claiming more
than the task needs.

## Optional dependency categories

| Category | What it unlocks | Typical verification |
| --- | --- | --- |
| Provider APIs | OpenAI-compatible calls, Gemini, Groq, Cerebras, Portkey, LangDB, LiteLLM, local/Ollama endpoints | Config construction without calls; live call only with keys/server. |
| Embeddings | OpenAI/Azure/Gemini embeddings, HuggingFace/SentenceTransformer, FastEmbed, llama.cpp server | Import config; tiny embed only when model/server/cache is available. |
| Document parsers | PDF/DOCX/PPTX/XLSX, OCR, marker/docling/unstructured/markitdown | Import parser and parse tiny local fixture; skip OCR/model downloads unless approved. |
| Vector stores | Qdrant, LanceDB, Chroma, Pinecone, PGVector, Weaviate, MeiliSearch | Config/import check; backend-specific service or storage smoke when selected. |
| SQL/graph agents | SQLAlchemy DB connections, PostgreSQL/MySQL, Neo4j, ArangoDB | Validator/config import; live DB query only with a test service/URI. |
| UI/logging | Chainlit callbacks, HTML logs, status/quiet output | Callback/config import; do not launch long-running web service as a default smoke. |
| MCP/search integrations | FastMCP transports, built-in search tools, file tools | In-memory/local no-network MCP smoke; external transports/search calls need credentials or local binaries. |

## Backend criticality guidance

- Core `ChatAgent`, `Task`, `ToolMessage`, `MockLM`, provider config objects,
  parser config objects, and most security validators are CPU-only.
- GPU is optional unless the user specifically selects Torch/HF model execution,
  GPU embeddings, local LLM inference, or a backend whose CPU substitute is not
  equivalent.
- Service backends such as Neo4j, ArangoDB, PostgreSQL, Weaviate, Pinecone, and
  remote search/provider APIs are optional unless the user asks to run that live
  service workflow.
- A successful import of an optional class is not a live service proof. It only
  proves the package-side API is available.

## Missing-extra error pattern

Langroid raises `LangroidImportError` messages that name the missing package or
extra and show install commands such as:

```text
If you want to use it, please install langroid with the `sql` extra.
```

When this appears:

1. Confirm the task really needs that workflow.
2. Install only the named extra or a narrower dependency set.
3. Re-run a no-network import/config check.
4. Run service or model smokes only after credentials, data, binaries, and
   hardware are available.
