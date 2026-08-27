---
name: chunking-and-types
description: "Use Chonkie local chunkers, tokenizers, and data contracts for
  deterministic text, table, code, and optional model-dependent chunking."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Chonkie chunking and types

Use this sub-skill when the task is about selecting or configuring Chonkie chunkers, interpreting `Chunk`/`Sentence`/recursive/markdown data objects, or running deterministic local chunking checks.

## Route here

- Fixed-size chunks by token count: `TokenChunker`.
- General-purpose local document chunking: `RecursiveChunker`.
- Sentence-boundary chunking: `SentenceChunker`.
- Byte-throughput chunking: `FastChunker`.
- Markdown/HTML table chunks: `TableChunker`.
- Source-code chunks: `CodeChunker` when the `code` extra and tree-sitter grammars are available.
- Interpreting chunk fields, tokenizer behavior, `RecursiveRules`, `MarkdownDocument`, `MarkdownTable`, `MarkdownCode`, and code rule dataclasses.

## Route elsewhere

- Pipeline orchestration, chefs, refineries, fetchers, and CHOMP ordering: `../pipelines-and-processing/`.
- Embedding/model/provider setup for `SemanticChunker`, `LateChunker`, `NeuralChunker`, or `SlumberChunker`: `../embeddings-and-generative/`.
- CLI commands, HTTP API schemas/routes, local serving, and cloud wrappers: `../interfaces-and-deployment/`.
- JSON/datasets/vector-database export or handshakes: `../integrations-and-storage/`.

## Required operating references

1. Start with `references/chunker-api-reference.md` for constructor signatures, selection rules, deterministic versus optional chunkers, and common examples.
2. Use `references/tokenizers-and-types.md` when chunk offsets, token counts, metadata, recursive rules, or markdown/code/table object contracts matter.
3. Use `references/troubleshooting.md` for import, optional dependency, model-download, grammar-cache, chunk-size, and boundary problems.
4. For a safe local diagnostic, run `scripts/chunking_smoke.py --help` first, then run the smoke with deterministic defaults.

## Safe defaults

Prefer this deterministic baseline before any model/provider chunker:

```python
from chonkie import RecursiveChunker

chunker = RecursiveChunker(tokenizer="character", chunk_size=512, min_characters_per_chunk=24)
chunks = chunker.chunk(text)
```

If strict maximum token count matters more than natural boundaries, switch to `TokenChunker`. If topic-coherent or model-trained boundaries are requested, route dependency and model decisions to `../embeddings-and-generative/` and keep a deterministic fallback ready.
