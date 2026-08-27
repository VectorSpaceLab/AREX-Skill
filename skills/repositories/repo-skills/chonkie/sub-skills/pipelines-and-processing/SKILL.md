---
name: pipelines-and-processing
description: "Build local Chonkie Pipeline workflows with fetchers, chefs,
  refineries, and porters."
disable-model-invocation: true
metadata:
  disco-role: operating
  package: chonkie
  package-version: "1.7.0"
  responsibility: pipelines-and-processing
license: MIT
---

# pipelines-and-processing

Use this sub-skill when the user wants to transform raw text or local files into Chonkie `Document` objects with chunks, optional refinement, and local export. It covers the fluent `Pipeline` API, CHOMP step ordering, local file fetching, chefs, overlap/embedding refineries, and porter/export choices.

## Route within this sub-skill

- Start with [references/pipeline-workflows.md](references/pipeline-workflows.md) for `Pipeline().fetch_from().process_with().chunk_with().refine_with().run()`, CHOMP ordering, validation rules, direct text vs file input, batch returns, config/recipe patterns, and export chaining.
- Use [references/processing-components.md](references/processing-components.md) for component aliases, constructor/call arguments, return contracts, optional dependency gates, and when to choose `TextChef`, `MarkdownChef`, `TableChef`, `LiteParse`, `MistralOCR`, `FileFetcher`, `OverlapRefinery`, `EmbeddingsRefinery`, `JSONPorter`, or `DatasetsPorter`.
- Use [references/troubleshooting.md](references/troubleshooting.md) for missing chunker/input errors, multiple chefs, wrong parameters, path/extension surprises, optional dependencies, OCR/API key gates, embedding/model-download hazards, and export return-shape surprises.
- Run [scripts/pipeline_smoke.py](scripts/pipeline_smoke.py) to verify deterministic local pipeline behavior without network calls, model downloads, credentials, or persistent outputs.

## Stay in this sub-skill for

- Local ingestion from `texts=...`, one file, or a directory of files.
- Ordering and validation of pipeline steps: fetch, vision, process, chunk, refine, export, write.
- Choosing a chef before chunking: text, markdown, table, local document parsing, or OCR boundary decisions.
- Adding overlap context or attaching embeddings as a pipeline refinement step.
- Exporting pipeline chunks to JSON/JSONL or Hugging Face `Dataset` objects/files.

## Cross-skill routing

- Raw chunker selection, tokenizers, `Chunk`/`Document` data contracts, table/code chunking internals, and deterministic chunking details: `../chunking-and-types/`.
- Provider embeddings, local model downloads, semantic/late/neural chunking, and generative workflows: `../embeddings-and-generative/`.
- CLI/API `chonkie pipeline` command construction, API schemas, local server, Chonkie Cloud wrappers, and deployment: `../interfaces-and-deployment/`.
- Live vector database handshakes, datastore credentials/services, and storage-specific write/search behavior: `../integrations-and-storage/`.

## Safe operating defaults

Prefer a deterministic local pipeline unless the user explicitly asks for model-backed or cloud-backed processing:

```text
Pipeline().process_with("text").chunk_with("recursive", tokenizer="word", chunk_size=512)
```

For RAG ingestion without model downloads, add overlap refinement before any embedding/vector-store step:

```text
...chunk_with("recursive", tokenizer="word", chunk_size=512).refine_with("overlap", tokenizer="word", context_size=50)
```

Do not start live OCR, provider embedding, Chonkie Cloud, or vector database operations unless the user provides the required dependency, credential, network, and service constraints.
