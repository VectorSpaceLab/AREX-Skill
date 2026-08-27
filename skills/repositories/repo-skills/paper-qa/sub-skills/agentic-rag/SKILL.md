---
name: agentic-rag
description: "Use PaperQA's Python API for agentic and manual scientific RAG
  over Docs, Doc, Text, ask, agent_query, evidence retrieval, answers,
  callbacks, and async boundaries."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# PaperQA Agentic RAG API

Use this sub-skill when the task is to run PaperQA from Python: build `Docs`, add `Doc`/`Text` objects or local files/texts, retrieve evidence with `Docs.aget_evidence`, generate answers with `Docs.aquery`, or use `ask`/`agent_query` with fake or ToolSelector agents.

## Route here for

- Manual `Docs` workflows: `aadd`, `aadd_file`, `aadd_url`, `aadd_texts`, `aget_evidence`, `aquery`.
- Agent workflows: `ask`, `agent_query`, `agent_type="fake"`, default `ToolSelector`, agent callbacks, answer/session/status outputs.
- No-network object smokes and pre-chunked text ingestion with deferred embeddings.
- Understanding `PQASession`, `Context`, `AnswerResponse`, citations, references, and source/context outputs.

## Route elsewhere

- CLI commands, index build/search/reuse, `pqa ask/search/index`, manifests: [cli-and-indexing](../cli-and-indexing/SKILL.md).
- Parser choice, PDF/media/Office/code parsing details, impossible/corrupt documents: [docs-and-parsing](../docs-and-parsing/SKILL.md).
- Provider/model/settings tuning, local embeddings, Qdrant, prompts beyond API usage: [settings-and-configuration](../settings-and-configuration/SKILL.md).
- Metadata clients, DOI/title hydration, OpenReview/Zotero/ClinicalTrials sources: [metadata-and-sources](../metadata-and-sources/SKILL.md).

## Start with the bundled references

1. Check verified signatures and return shapes in [references/api-reference.md](references/api-reference.md).
2. Use self-contained recipes in [references/workflows.md](references/workflows.md).
3. Diagnose common runtime failures with [references/troubleshooting.md](references/troubleshooting.md).
4. For a safe no-network smoke, run [scripts/smoke_docs_objects.py](scripts/smoke_docs_objects.py) with `--help`, then `smoke`.

## Operating cautions

- Prefer async APIs (`await docs.aadd_texts(...)`, `await docs.aquery(...)`) in notebooks, web servers, and other running event loops.
- Passing a citation and disabling metadata hydration avoids citation-inference LLM calls and metadata-provider network calls during manual file addition.
- `Settings(parsing={"defer_embedding": True})` defers embeddings at ingest; retrieval/answering can still call the configured embedding and LLM providers.
- The no-network smoke only proves installed object/API construction; it does not validate provider credentials, embeddings, parsing quality, or answer quality.
