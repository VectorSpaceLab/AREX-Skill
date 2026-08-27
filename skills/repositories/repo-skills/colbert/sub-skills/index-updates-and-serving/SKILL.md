---
name: index-updates-and-serving
description: "Mutate existing ColBERT indexes with IndexUpdater, persist index
  changes safely, coalesce updated artifacts, and expose a lightweight search
  API without import-time side effects."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# ColBERT Index Updates and Serving

Use this sub-skill when the task is to add passages to an existing ColBERT index, remove passage IDs, decide whether changes survive Searcher reloads, persist IndexUpdater changes to disk, coalesce multi-chunk index artifacts, or serve an existing index through a small JSON search API.

## Route the task

- For verified constructor signatures, method semantics, reload behavior, return shapes, and package facts, read `references/api-reference.md`.
- For safe add/remove/persist workflows, disk mutation precautions, coalescing, backup strategy, and reload validation, read `references/index-update-workflows.md`.
- For Flask-style serving, explicit CLI/env configuration, `/api/search` response shape, lazy Searcher creation, and `k <= 100` behavior, read `references/serving-api.md`.
- For install/import, optional dependency, backend, pid, metadata, chunk, mmap, and server configuration failures, read `references/troubleshooting.md`.
- For an editable add/remove/persist command template with no ColBERT import at `--help` time, adapt `scripts/index_update_template.py`.
- For a safe lightweight JSON search service adapted from ColBERT's public server pattern with lazy Searcher creation, adapt `scripts/serve_search_api.py`.

## Core boundaries

- Cover `IndexUpdater(config, searcher, checkpoint=None)`, `Searcher(...)` reload behavior, index artifact mutation, `persist_to_disk()`, coalesced index directories, and lightweight HTTP serving.
- Keep fresh index creation, baseline search, `search_all`, ranking save, and general search tuning in `../indexing-and-search/`.
- Keep TSV/qrels/ranking evaluation, query/collection validation details, and metrics workflows in `../data-and-evaluation/`.
- Keep checkpoint internals, tokenizer/model compatibility, and training/distillation in `../modeling-and-tokenization/` and `../training-and-distillation/`.

## Fast starting point

1. Open an existing index with `Searcher(index=..., checkpoint=..., collection=..., config=..., index_root=...)` and create `IndexUpdater(config, searcher, checkpoint=...)` when adding passages.
2. Use `remove([pid, ...])` for in-memory removal; use `add([passage, ...])` for in-memory append; call `persist_to_disk()` only after backing up or writing to a disposable copy of the index.
3. Reload a fresh `Searcher` after `persist_to_disk()` to prove changes survived disk mutation; without persistence, changes affect only the current `Searcher` instance.
4. Serve search through `scripts/serve_search_api.py` with explicit `--index-name` and either `--index-root` or a compatible ColBERT config; do not create a `Searcher` at module import time.

## Verified package facts

- Distribution: `colbert-ai` 0.2.22; import package: `colbert`.
- Verified imports include `colbert`, `colbert.infra`, `colbert.data`, `colbert.modeling.checkpoint`, `utility`, and `baleen`.
- CPU import inspection works and CPU search can work, but practical indexing, training, and passage encoding for updates usually require CUDA/GPU-capable PyTorch.
- Important signatures: `Indexer(checkpoint, config=None, verbose=3)`, `Searcher(index, checkpoint=None, collection=None, config=None, index_root=None, verbose=3)`, `IndexUpdater(config, searcher, checkpoint=None)`, `Collection(path=None, data=None)`, `Queries(path=None, data=None)`, and `Ranking(path=None, data=None, metrics=None, provenance=None)`.
