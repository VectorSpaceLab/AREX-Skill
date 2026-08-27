# Repository Provenance

## Source snapshot

- Repository: Future-House PaperQA / PaperQA2
- Public package name: `paper-qa`
- Canonical skill id: `paper-qa`
- Git branch: `main`
- Git commit: `57e89f7223b0960d5ee5ea048c69e3c47e088572`
- Exact tag at generation: `v2026.08.12`
- Remote URL: `https://github.com/Future-House/paper-qa.git`
- Working tree state at evidence capture: clean before generated skill artifacts were written
- Installed package versions inspected for runtime facts: `paper-qa==2026.8.12`, `paper-qa-pypdf==2026.8.12`
- Python support from package metadata: Python `>=3.11`
- Generated skill output: self-contained PaperQA repo skill for DisCo Researcher

## Evidence paths used

These paths are relative to the source repository snapshot above and are recorded only to support future refresh/staleness decisions.

| Evidence path | Evidence role |
| --- | --- |
| `pyproject.toml` | package metadata, dependencies, extras, console script, Python support, workspace sources |
| `uv.lock` | workspace local package relationships and dependency groups |
| `README.md` | primary user workflows: install, CLI, library APIs, models, embeddings, multimodal, indexing, clients, sources, settings |
| `docs/tutorials/settings_tutorial.md` | settings/model-role tutorial and provider pitfalls |
| `docs/tutorials/querying_with_clinical_trials.md` | ClinicalTrials.gov tool and named configs |
| `docs/tutorials/where_do_I_get_papers.md` | OpenReview, Zotero, paper acquisition boundaries |
| `src/paperqa/__init__.py` | public exports |
| `src/paperqa/docs.py` | `Docs` ingestion, evidence, query, retrieval, deletion, text-index behavior |
| `src/paperqa/agents/__init__.py` | CLI entry point and `ask`/index wrappers |
| `src/paperqa/agents/main.py` | `agent_query`, fake agent, ToolSelector/agent execution flow |
| `src/paperqa/agents/search.py` | search index storage, manifest/index internals, query/build behavior |
| `src/paperqa/agents/tools.py` | agent tool names and ClinicalTrials integration surface |
| `src/paperqa/settings.py` | `Settings`, sub-settings, named config loading, parser resolver, model factories |
| `src/paperqa/readers.py` | parser dispatch, chunking, text/html/office/image/PDF reader interfaces |
| `src/paperqa/llms.py` | vector stores, Qdrant optional dependency, embedding behavior |
| `src/paperqa/types.py` | `Doc`, `DocDetails`, `Text`, `Context`, `PQASession` data models |
| `src/paperqa/clients/*` | metadata provider and post-processor behavior |
| `src/paperqa/sources/clinical_trials.py` | ClinicalTrials.gov API/search/formatting source |
| `src/paperqa/contrib/openreview_paper_helper.py` | OpenReview helper prerequisites and flow |
| `src/paperqa/contrib/zotero.py` | Zotero helper prerequisites and flow |
| `src/paperqa/configs/*.json` | bundled named settings |
| `packages/paper-qa-pypdf/*` | default PyPDF reader package, media/enhanced extras |
| `packages/paper-qa-pymupdf/*` | optional PyMuPDF reader package and license/dependency evidence |
| `packages/paper-qa-docling/*` | optional Docling reader package |
| `packages/paper-qa-nemotron/*` | optional NVIDIA nemotron-parse reader package |
| `tests/test_cli.py` | CLI/index native behavior candidates |
| `tests/test_configs.py` | settings/config native behavior candidates |
| `tests/test_paperqa.py` | Docs, parsing, retrieval, metadata, vector-store behavior candidates |
| `tests/test_clients.py` | metadata provider behavior candidates |
| `tests/test_clinical_trials.py` | no-network ClinicalTrials formatting/API behavior candidates |
| `tests/stub_data/` | tiny fixture evidence for final native verification |

## Selected scope baseline

Included runtime capabilities:

- Python API RAG workflows (`Docs`, `ask`, `agent_query`, `PQASession`, evidence and answer objects).
- Document parsing/chunking and parser-extra selection.
- `pqa` CLI, search indexes, manifests, settings save/view, and answer index search.
- `Settings`, named configs, model/provider/embedding/prompt/vector-store configuration.
- Metadata clients and external source helpers for ClinicalTrials.gov, OpenReview, and Zotero.

Explicitly non-required or optional at generation:

- Live provider calls, model quality evaluation, metadata network checks, ClinicalTrials.gov live HTTP, OpenReview downloads, Zotero account access, Qdrant service connection, local model server execution, and Nemotron API/SageMaker calls.
- CUDA/ROCm/MPS/vendor hardware backends. The selected required scope is CPU/any.
- Broad repository maintenance, linting, release, CI, benchmark, or paper-reproduction workflows.

## Refresh triggers

Refresh this skill if any of these change materially:

- Public `paperqa` exports, `Docs`/`Settings` signatures, `pqa` CLI commands/flags, `DocMetadataClient` behavior, parser interfaces, named config names/defaults, optional extras, or supported Python versions.
- Default PDF reader policy or parser-extra dependency/licensing/service requirements.
- Search index layout, manifest columns, `PQA_HOME` behavior, or answer index storage.
- ClinicalTrials.gov, OpenReview, or Zotero helper APIs and prerequisites.
- Package version moves beyond the provenance tag and user tasks depend on changed PaperQA behavior.
