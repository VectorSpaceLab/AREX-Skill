---
name: vector-corpus
description: "Ground STORM article runs on a user CSV or local corpus with
  VectorRM and Qdrant, including schema validation, offline/online vector
  stores, device choices, and STORMWikiRunner integration."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# vector-corpus

Use this sub-skill when the task asks to run or prepare STORM over a user-owned CSV/local corpus rather than Internet search. It covers `VectorRM`, Qdrant offline/online stores, CSV validation, corpus chunking, embedding device choices, and the handoff into `STORMWikiRunner`.

## Route here when

- The user has a CSV corpus with `content` and `url` columns and wants STORM grounded on those rows.
- The user needs to create or update a Qdrant collection for `VectorRM` from CSV documents.
- The user already has a local Qdrant directory or Qdrant Cloud URL and needs `VectorRM` to retrieve from it.
- The user asks about `VectorRM.__init__`, `init_offline_vector_db`, `init_online_vector_db`, `get_vector_count`, `forward`, or `QdrantVectorStoreManager.create_or_update_vector_store`.

## Route elsewhere

- Internet-search STORM workflows, search retriever selection, stage resume, and article output inspection belong in `../storm-wiki/`.
- Co-STORM collaborative discourse, warm start, turn-taking, mind maps, and report generation belong in `../co-storm/`.

## Bundled references

- [references/workflows.md](references/workflows.md): end-to-end commands for validating CSVs, creating offline/online Qdrant stores, and plugging `VectorRM` into STORM.
- [references/data-formats.md](references/data-formats.md): exact CSV schema, chunking arguments, and validation symptoms.
- [references/api-reference.md](references/api-reference.md): API signatures and behavior for `VectorRM` and `QdrantVectorStoreManager`.
- [references/troubleshooting.md](references/troubleshooting.md): symptoms, causes, and fixes for CSV, Qdrant, embedding, device, and STORM runner issues.

## Bundled scripts

- `scripts/validate_vector_corpus_csv.py`: standard-library CSV schema checker. Use `--strict-unique-url` before indexing.
- `scripts/process_kaggle_arxiv_abstract_dataset.py`: converts Kaggle arXiv abstracts CSVs into the `VectorRM` CSV schema.
- `scripts/run_storm_wiki_with_vector_rm.py`: safe helper for corpus-grounded STORM with current `LitellmModel`; supports `--dry-run` and `--validate-only` without embedding, Qdrant, LLM, or network calls.

## Minimum safe workflow

1. Validate the corpus with `python scripts/validate_vector_corpus_csv.py --input-path corpus.csv --strict-unique-url`.
2. Choose Qdrant mode:
   - offline: local filesystem directory with `--vector-db-mode offline --offline-vector-db-dir ./vector_store`;
   - online: Qdrant URL plus `QDRANT_API_KEY` with `--vector-db-mode online --online-vector-db-url https://...`.
3. Start with `--device cpu`; use `cuda` or `mps` only for embedding acceleration when available.
4. Use `--dry-run` or `--validate-only` first, then run the full helper with explicit STORM stage flags.

The runtime scripts assume the public `knowledge-storm` package is installed for full runs. Help, dry-run, and validate-only paths avoid package imports where possible.
