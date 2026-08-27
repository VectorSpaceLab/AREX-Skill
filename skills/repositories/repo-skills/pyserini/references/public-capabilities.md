# Public Capability Map

## When To Read

Read this when choosing a Pyserini route, summarizing what the package can do, or mapping a user request to sub-skills.

## Package And Runtime

- Distribution: `pyserini`.
- Version baseline for this skill: `2.3.0`.
- Import root: `pyserini`.
- Python baseline: Python `>=3.12` from package metadata.
- Java baseline: Java 21 for Anserini/Lucene-backed workflows through PyJNIus.
- Optional-heavy dependencies: Faiss is separate from core metadata; Torch/Transformers/ONNX Runtime support neural/dense workflows; OpenAI-backed encoders require credentials; multimodal support uses Pyserini optional dependencies.

## Workflow Families

| Task family | Read first | Key entry points | Validation |
| --- | --- | --- | --- |
| Install/debug runtime | `../sub-skills/install-and-runtime/SKILL.md` | `pip install pyserini`, Java 21, Torch/Faiss choices, runtime checker | `scripts/check_pyserini_install.py` |
| Lucene indexing/search/fetch | `../sub-skills/index-search-fetch/SKILL.md` | `python -m pyserini.index.lucene`, `python -m pyserini.search.lucene`, `LuceneSearcher`, `LuceneIndexer`, `LuceneIndexReader` | JSONL validator and Lucene command builder |
| Dense encoding/Faiss/hybrid | `../sub-skills/dense-encoding/SKILL.md` | `python -m pyserini.encode`, `python -m pyserini.search.faiss`, `FaissSearcher`, `HybridSearcher` | dense JSONL validator and dense command builder |
| Evaluation/fusion/reproducibility | `../sub-skills/evaluation-and-fusion/SKILL.md` | `python -m pyserini.eval.*`, `pyserini.fusion`, TREC/MS MARCO/KILT run formats, RRF/interpolation | TREC run validator and fusion recipe builder |
| REST/MCP serving | `../sub-skills/serving-and-agent-tools/SKILL.md` | `python -m pyserini.server.rest`, `python -m pyserini.server.mcp`, server YAML aliases, API keys, OpenAPI, MCP tools | server config validator |
| Source checkout maintenance | `../sub-skills/repo-development/SKILL.md` | editable install, `tools` submodule, eval tools, Anserini fatjar, focused tests, job manifests | safe test selector |

## Data And Output Formats

- Sparse Lucene indexing commonly uses JSON/JSONL documents with `id` and `contents` fields.
- Query topics are often TSV, prebuilt topic names, KILT, multimodal, MBEIR, or raw JSONL depending on the CLI.
- Search outputs are usually TREC, MS MARCO, or KILT format.
- Dense encoded corpus rows contain document identifiers, text fields, and vector payloads; Faiss indexes need companion docid mappings and generally do not store raw text.
- REST `/v1/{index}/search` returns JSON search results through GET query parameters; MCP tools return rich content parts suitable for agent clients.

## Native Verification Candidates

Safe or bounded native candidates discovered from the repository include:

- CLI help checks for `pyserini.search.lucene`, `pyserini.search.faiss`, `pyserini.encode`, `pyserini.server.rest`, and `pyserini.server.mcp` when dependencies/resources are available.
- Tiny fixture validations from `tests/resources` for JSONL collections, TREC runs, qrels, and fusion inputs.
- Focused tests around server config, TREC tools, evaluation helpers, collection wrappers, and on-the-fly Lucene indexing after Java/fatjar resources are ready.

Do not run prebuilt-index downloads, dense model downloads, broad integration manifests, or full reproduction matrices unless the user explicitly requests heavyweight validation.
