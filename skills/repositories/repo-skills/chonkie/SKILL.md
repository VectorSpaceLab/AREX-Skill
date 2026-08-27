---
name: chonkie
description: "Use Chonkie for text/document chunking, pipelines, embeddings,
  CLI/API serving, and storage integrations."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Chonkie repo skill

Use this skill when a task involves the `chonkie` Python package: chunking text/documents, building local processing pipelines, choosing optional embedding/model/provider integrations, operating the CLI/API/cloud wrappers, or exporting chunks to files and vector stores.

## Start here

1. Confirm Chonkie is installed and importable:

   ```python
   import chonkie
   print(chonkie.__version__)
   ```

2. If the environment or optional extras are unclear, run:

   ```bash
   python scripts/check_chonkie_environment.py --help
   python scripts/check_chonkie_environment.py --json
   ```

3. Route the task to the closest sub-skill. Prefer deterministic local workflows unless the user explicitly asks for model downloads, provider APIs, cloud calls, or datastore writes.

## Sub-skill routes

- `sub-skills/chunking-and-types/` — local chunker selection and chunk/type contracts: `TokenChunker`, `SentenceChunker`, `RecursiveChunker`, `FastChunker`, `TableChunker`, `CodeChunker`, optional model-dependent chunkers, tokenizers, recursive rules, and `Chunk`/markdown/code/table objects.
- `sub-skills/pipelines-and-processing/` — `Pipeline` workflows, CHOMP ordering, file fetching, chefs, local document processing, overlap/embedding refineries, and local JSON/dataset export from pipelines.
- `sub-skills/embeddings-and-generative/` — embeddings, provider wrappers, `EmbeddingsRefinery`, semantic/late/neural/slumber chunking, genies, optional dependency/model-cache/API-key decisions, and deterministic fallbacks.
- `sub-skills/interfaces-and-deployment/` — `chonkie` CLI commands, local FastAPI API schemas/server, Chonkie Cloud wrappers, logging/config, API keys, and deployment/serving guidance.
- `sub-skills/integrations-and-storage/` — `JSONPorter`, `DatasetsPorter`, vector/datastore handshakes, dependency probes, credential/service gates, and safe no-live-write storage planning.

## Shared references

- `references/package-overview.md` — package surface map, install extras, public entry points, and verified support boundaries.
- `references/troubleshooting.md` — cross-cutting install/import, optional dependency, model download, credentials, logging, CLI/API, and service safety issues.
- `references/repo-provenance.md` — source snapshot used to produce this skill; read before deciding whether to refresh.
- `references/repo-routing-metadata.json` — structured router metadata consumed by repo-skill import tooling.

## Safe defaults for future agents

- For local chunking, start with `RecursiveChunker(tokenizer="character" or "word", chunk_size=...)` before model-dependent chunkers.
- For pipelines, use `Pipeline().process_with("text").chunk_with("recursive", ...)` or a `fetch_from("file", ...)` pipeline before adding optional refineries, exporters, or storage.
- For CLI examples, specify `--chunker recursive`, `--chunker token`, or `--chunker sentence` unless semantic/model extras are known to be installed.
- For cloud/provider/vector-store tasks, do not make live network calls or writes until the user has explicitly provided credentials, endpoint/service scope, and permission to use them.
- Treat optional extras (`semantic`, `st`, `neural`, `openai`, `api`, `handshakes`, etc.) as capability gates, not as evidence that the user's current environment is ready.

## Import policy for this generated candidate

This production run was requested as `not import`. The runtime skill tree can be verified, but do not import it into the live managed repo-skill library unless a later user explicitly asks for import/export.
