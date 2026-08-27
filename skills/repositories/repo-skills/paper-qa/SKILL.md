---
name: paper-qa
description: "Use PaperQA/PaperQA2 for scientific literature RAG, document
  parsing, metadata hydration, CLI indexing, Settings configuration, and
  external paper/trial source workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# PaperQA Repo Skill

Use this repo skill when a task involves PaperQA/PaperQA2: high-accuracy retrieval-augmented question answering over scientific papers and local documents, the `pqa` CLI, document parsing/chunking, metadata providers, named `Settings`, model/embedding configuration, and literature-source helpers.

## Install and readiness

PaperQA requires Python 3.11+. For normal use install the public package:

```bash
python -m pip install "paper-qa>=5"
```

Use optional extras only for the workflows you need:

```bash
python -m pip install "paper-qa[local]"          # sentence-transformers local embeddings
python -m pip install "paper-qa[qdrant]"         # Qdrant vector store
python -m pip install "paper-qa[office]"         # docx/xlsx/pptx parsing
python -m pip install "paper-qa[pymupdf]"        # PyMuPDF PDF reader
python -m pip install "paper-qa[docling]"        # Docling PDF reader
python -m pip install "paper-qa[nemotron]"       # NVIDIA nemotron-parse reader API
python -m pip install "paper-qa[zotero]"         # Zotero helper
python -m pip install "paper-qa[openreview]"     # OpenReview helper
```

Minimal import check:

```bash
python - <<'PY'
import paperqa
from paperqa import Docs, Settings
print(paperqa.__version__)
print(Settings().answer.evidence_k)
PY
```

For a broader no-network readiness check, run [scripts/check_paperqa_env.py](scripts/check_paperqa_env.py).

## Choose a sub-skill

| Task intent | Read |
| --- | --- |
| Use Python APIs such as `Docs`, `ask`, `agent_query`, `Docs.aadd_texts`, `Docs.aget_evidence`, `Docs.aquery`, callbacks, contexts, answers, or sessions | [agentic-rag](sub-skills/agentic-rag/SKILL.md) |
| Parse and chunk PDFs, text, Markdown/code, HTML, Office docs, images, multimodal media, or choose a PDF reader extra | [docs-and-parsing](sub-skills/docs-and-parsing/SKILL.md) |
| Operate the `pqa` CLI, build/search/reuse indexes, validate manifest CSVs, manage `PQA_HOME`, or inspect CLI flags | [cli-and-indexing](sub-skills/cli-and-indexing/SKILL.md) |
| Configure `Settings`, named configs, LiteLLM providers, local model servers, embeddings, prompts, vector stores, or optional dependency choices | [settings-and-configuration](sub-skills/settings-and-configuration/SKILL.md) |
| Use metadata clients, DOI/title hydration, Crossref/Semantic Scholar/OpenAlex/Unpaywall, ClinicalTrials.gov, OpenReview, or Zotero helpers | [metadata-and-sources](sub-skills/metadata-and-sources/SKILL.md) |

## Common operating routes

- For a local folder of PDFs and a natural-language question, use `pqa ask` or `paperqa.ask` after configuring provider credentials and index paths.
- For a controlled Python pipeline, build a `Docs()` object, add `Doc`/`Text` objects or local files, then call `await docs.aget_evidence(...)` or `await docs.aquery(...)`.
- For no-network tests, use pre-chunked `Text` objects with `Settings(parsing={"defer_embedding": True})` and the bundled smoke scripts; do not treat these as answer-quality validation.
- For custom providers, update every active model role: `llm`, `summary_llm`, `agent.agent_llm`, `embedding`, and any parser enrichment LLM.
- For reproducible indexes, set `PQA_HOME` or `agent.index.index_directory`, decide whether the paper directory should remain relative, and validate manifest CSVs before long indexing runs.

## Cross-cutting cautions

- Default answering workflows call LLM, embedding, and sometimes metadata-provider services. Confirm credentials, network policy, rate limits, and cost before running `pqa ask`, `Docs.aquery`, `ask`, or `agent_query`.
- Passing citation/title/DOI metadata and disabling metadata hydration can prevent unintended metadata-provider calls during controlled local ingestion.
- Optional parser extras vary by dependency weight, service credentials, output quality, and license; choose them deliberately rather than installing all extras.
- If a task names PaperQA source staleness or repository edits, first read [references/repo-provenance.md](references/repo-provenance.md) and compare the current package/repo version to this skill's baseline.
- For install/import/provider/index failures that cut across sub-skills, use [references/troubleshooting.md](references/troubleshooting.md) before drilling into workflow-specific troubleshooting.

## Provenance and routing metadata

- [references/repo-provenance.md](references/repo-provenance.md) records the source version, branch/tag, package version, and evidence paths used to build this skill.
- [references/repo-routing-metadata.json](references/repo-routing-metadata.json) contains structured scenario metadata for managed `repo-skills-router` import.
