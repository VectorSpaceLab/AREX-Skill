---
name: metadata-and-sources
description: "Use PaperQA metadata clients and external paper/trial source
  helpers safely without local parsing or RAG querying."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Metadata and Sources

Use this sub-skill when the task is about PaperQA metadata hydration or external source acquisition, not about parsing local documents or answering over an existing `Docs` collection.

## Route here for

- Looking up paper metadata with `DocMetadataClient` from `title`, `doi`, `authors`, and requested `fields`.
- Choosing `DEFAULT_CLIENTS`, `ALL_CLIENTS`, or a custom ordered provider set for Crossref, Semantic Scholar, OpenAlex, Unpaywall, journal quality, and retraction checks.
- Understanding how `Docs.aadd(..., title=..., doi=..., authors=...)` uses metadata hydration and how `upgrade_doc_to_doc_details` merges metadata back into a `Doc`.
- Enabling ClinicalTrials.gov search through PaperQA settings and the `clinical_trials_search` tool.
- Using OpenReview or Zotero helpers after the user has authorized network access, downloads, optional extras, and credentials.

## Route away from here

- Local PDF/text/HTML/Office/image parsing, chunking, and parser extras: use the `docs-and-parsing` sub-skill.
- Asking questions over loaded papers, `Docs.aquery`, `ask`, `agent_query`, evidence, and answer generation: use the `agentic-rag` sub-skill.
- `pqa` CLI and index build/search workflows: use the `cli-and-indexing` sub-skill.
- Model, embedding, prompt, LiteLLM, and settings JSON details outside source-specific tool selection: use the `settings-and-configuration` sub-skill.

## Operating sequence

1. Identify the source intent: metadata-only hydration, metadata during `Docs.aadd`, ClinicalTrials.gov search, OpenReview paper discovery, Zotero library ingestion, or third-party paper acquisition advice.
2. For metadata clients, read [metadata-clients.md](references/metadata-clients.md) before composing providers or selecting `fields`.
3. For ClinicalTrials.gov, OpenReview, Zotero, and paper-acquisition boundaries, read [clinical-trials-and-literature-sources.md](references/clinical-trials-and-literature-sources.md).
4. For failures, read [troubleshooting.md](references/troubleshooting.md) before retrying live services.
5. Prefer the bundled no-network scripts for local inspection and formatting checks:
   - `scripts/inspect_metadata_clients.py`
   - `scripts/mock_clinical_trials_format.py`

## Safety defaults

- Do not run live metadata, ClinicalTrials.gov, OpenReview, Zotero, or paper-download calls unless the user explicitly wants network access and accepts provider terms, credentials, and rate-limit implications.
- Use `DEFAULT_CLIENTS` or a small custom provider list before `ALL_CLIENTS` for fast DOI/title hydration.
- Do not recommend third-party scraping as a default paper acquisition path. Prefer user-supplied PDFs, authorized APIs, institutional access, OpenReview, Zotero, and direct open-access URLs.
