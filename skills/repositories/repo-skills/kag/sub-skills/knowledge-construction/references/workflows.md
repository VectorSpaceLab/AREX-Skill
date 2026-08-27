# Knowledge Construction Workflows

## Purpose

Read this when you need to create, restore, update, or validate a KAG project, or when you need to decide which builder chain and index manager fit a source corpus.

## Typical workflow

1. Inspect the project config with `scripts/inspect_kag_config.py`.
2. Validate the project layout with `scripts/validate_project_layout.py`.
3. Restore or create the project with `knext project ...`.
4. Commit the schema with `knext schema commit`.
5. Run the builder entry point for the project.
6. Check checkpoints and retry only when the failure is safe to resume.

## Project setup commands

### Create

Use project creation when you are starting from a new config and want the tool to generate a project folder.

```bash
knext project create --config_path ./kag_config.yaml
```

The source checks require the project namespace to be a short capitalized alphanumeric name.

### Restore

Use restore when the project folder already exists and you want to recover local metadata or sync a local project directory back to the server.

```bash
knext project restore --host_addr http://127.0.0.1:8887 --proj_path .
```

### Update

Use update after editing the project config.

```bash
knext project update --proj_path .
```

### Schema commit

Commit the local schema once the namespace and schema filename agree.

```bash
knext schema commit
```

If you also maintain concept rules, register them separately with `knext schema reg_concept_rule --file <dsl-file>`.

## Builder chain shapes

### Structured data

Use a structured chain when the source is already tabular or field-mapped.

Typical shape:

- mapping
- optional vectorizer
- graph writer

### Unstructured data

Use an unstructured chain when the source is text, documents, or OCR-like content.

Typical shape:

- reader
- splitter
- extractor
- optional vectorizer
- optional post-processor
- writer

### Domain graph injection

Use a domain-graph injection chain when a project needs prebuilt domain graph nodes before or during unstructured build-time extraction.

Typical shape:

- external graph loader
- optional vectorizer
- writer

## Index manager choice

Index managers describe what gets indexed and how the query side should retrieve it.

- `chunk_index` — lowest-cost chunk retrieval for general RAG
- `outline_index` — heading-aware retrieval for structured documents
- `summary_index` — retrieval through generated summaries
- `table_index` — table-heavy documents
- `atomic_query_index` — fine-grained fact or FAQ style retrieval
- `kag_hybrid_index` — combined graph + text retrieval for deeper multi-hop QA

## What to inspect in the config

- `project.namespace`, `project.host_addr`, and `project.id`
- `kag_builder_pipeline.chain.type`
- `kag_builder_pipeline.scanner.type`
- `kag_builder_pipeline.chain.reader.type`
- `kag_builder_pipeline.chain.extractor.type`
- `kag_builder_pipeline.chain.vectorizer.type`
- `kag_builder_pipeline.chain.writer.type`
- `kag_solver_pipeline` if the same project will be queried later

## Checkpoint guidance

Builder writers and readers may create checkpoint directories. If a task resumes cleanly, keep the checkpoint. If a layout bug or namespace mismatch caused the failure, fix the config before deleting checkpoints.
