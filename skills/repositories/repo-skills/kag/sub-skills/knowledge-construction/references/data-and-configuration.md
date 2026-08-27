# Data and Configuration

## Purpose

Read this when you need the concrete KAG config keys, builder component names, data-layout assumptions, or the index-selection tradeoffs that influence project setup.

## Project layout that usually matters

A KAG project typically needs these pieces:

- `kag_config.yaml`
- `schema/<Namespace>.schema`
- `builder/`
- `solver/` or `reasoner/` depending on the workflow
- optional local data directories for the project's source documents

## Config sections to watch

### Project

The `project` block usually contains:

- `namespace`
- `id`
- `host_addr`
- `language`
- `biz_scene`

The namespace must line up with the schema filename and the server-side project identity.

### Builder

The builder config usually selects:

- a chain type such as structured, unstructured, or domain injection
- a scanner or reader that matches the source data
- a splitter that creates manageable units
- an extractor that turns data into subgraphs
- an optional vectorizer
- a writer that sends the result to the graph store

### Solver

The solver config usually selects:

- a planner
- one or more executors or retrievers
- a generator
- optional reporter or memory components

## Common builder component names

Verified names from the source include families such as:

- readers: text, dict, docx, pdf, markdown, CSV/JSON-style readers
- splitters: length-based and other document splitters
- extractors: schema-free, schema-constrained, knowledge-unit, table, atomic-query, outline, summary
- vectorizers: mock, OpenAI-compatible, Ollama, local BGE-style, sparse BGE
- writers: KG writers and related graph sinks
- post-processors: KAG post-processing and graph-linking helpers

Use `kag interface --cls <ClassName>` when you need the exact registered subclass names for a family.

## Index-manager tradeoffs

- `chunk_index` is the cheapest option and works well as a baseline.
- `outline_index` and `summary_index` are useful when document structure matters.
- `table_index` is best when answers live in tabular evidence.
- `atomic_query_index` is useful for FAQ-like or atomic fact retrieval.
- `kag_hybrid_index` is the deepest retrieval setup and usually the best fit for multi-hop reasoning over mixed text and graph evidence.

## Validation assumptions

- If the vectorizer dimension changes, an existing project may need to be recreated.
- If a reader depends on external docs or credentials, prefer a local file-based reader for offline validation.
- If a builder writer is configured to delete graph data, treat that as destructive and confirm intent before running it.
- If the builder or schema file uses a custom module, that module must be imported before registry construction.

## Safe inspection helper

Use `scripts/inspect_kag_config.py` to see a redacted summary of the current config without exposing secrets.
