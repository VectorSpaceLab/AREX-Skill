---
name: integrations-and-storage
description: "Export Chonkie chunks to files/datasets and use vector datastore
  handshakes safely."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Integrations and Storage

Use this sub-skill when the task is about persisting, exporting, or handing off
Chonkie chunks/documents after chunk creation:

- write chunks as JSON/JSONL with `JSONPorter`;
- create or save Hugging Face `Dataset` objects with `DatasetsPorter`;
- route `Pipeline.export_with(...)` and `Pipeline.store_in(...)` steps;
- prepare Chonkie vector/datastore handshakes without accidental live writes;
- diagnose optional Chroma, Qdrant, LanceDB, Milvus, MongoDB, Pgvector,
  Pinecone, Turbopuffer, Weaviate, or Elasticsearch dependency issues.

## First routing decisions

1. If the user has not created chunks yet, load `../chunking-and-types/` for
   chunk/data-shape guidance and `../pipelines-and-processing/` for CHOMP
   pipeline composition before choosing storage.
2. If a vector datastore handshake needs `embedding_model`, load
   `../embeddings-and-generative/` before selecting the model, dimensions, or
   provider credentials.
3. If the user asks for CLI syntax, handshaker flags, serving, or deployment
   wiring, load `../interfaces-and-deployment/` and then return here for
   storage-specific constructor arguments and safety gates.
4. Prefer local, no-network exports (`JSONPorter` or `DatasetsPorter` with a
   caller-chosen path) unless the user explicitly asks for a datastore.
5. For vector/datastore integrations, run `scripts/handshake_dependency_probe.py`
   first when dependency availability is uncertain. Do not instantiate a live
   datastore client or write chunks until the target service, credentials, and
   write scope are explicit.

## Reference map

- `references/porter-workflows.md` — JSON/JSONL and Hugging Face Dataset
  workflows, pipeline export examples, and output-shape notes.
- `references/handshakes-reference.md` — BaseHandshake contract, dependency
  extras, constructor argument tables, random naming behavior, embedding model
  gates, search outputs, and safe mocked/in-memory alternatives.
- `references/troubleshooting.md` — import failures, credential/service safety,
  embedding and vector-dimension problems, metadata quirks, duplicate writes,
  and pipeline parameter mistakes.
- `scripts/handshake_dependency_probe.py` — no-network probe for optional client
  packages and Chonkie handshake/porter class imports with installation hints.

## Safety defaults

- Treat every handshake write as a datastore mutation. Avoid live writes by
  default; use mocked clients, in-memory clients, or local temporary paths for
  usability tests.
- Do not rely on default constructors for Milvus, MongoDB, Pgvector, Weaviate,
  or Elasticsearch unless the user confirms a local service is intentionally
  running and writable.
- Do not use Pinecone or Turbopuffer with real credentials unless the user
  confirms the target index/namespace and accepts remote writes.
- Prefer explicit collection/index/table/namespace names for repeatable work.
  Use `"random"` only for isolated experiments where discoverability is not
  required.
- Never paste secrets into examples. Read credentials from the user's approved
  secret manager or environment only when a live-service run is explicitly
  authorized.
