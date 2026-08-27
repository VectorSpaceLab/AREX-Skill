---
name: processing-streaming
description: "Transform map-style and iterable datasets with
  map/filter/batching, formatting, caching, combining, and streaming-aware
  workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Processing and Streaming

Use this sub-skill when a task is about preparing an already-loaded `Dataset`, `IterableDataset`, `DatasetDict`, or `IterableDatasetDict` for analysis, training, export, or further processing.

For initial loading from local files or the Hub, route to `../loading-local-hub/SKILL.md`. For schema declarations, feature casting, and modality feature types, route to `../features-formats/SKILL.md`. For persistent cache locations, offline settings, and CLI environment concerns, route to `../sharing-cli-cache/SKILL.md`.

## What This Covers

- Map-style transforms: `map`, `filter`, `select`, `shuffle`, `sort`, `shard`, `train_test_split`, `flatten_indices`, and `to_iterable_dataset`.
- Iterable/streaming transforms: lazy `map`, `filter`, `shuffle`, `skip`, `take`, `shard`, `reshard`, `set_epoch`, and framework iteration.
- Batching and multiprocessing: batched row-count changes, `remove_columns`, `features`, `num_proc`, `with_indices`, and `with_rank`.
- Formatting and conversions: `set_format`, `with_format`, framework formatters, `iter`, `to_pandas`, `to_polars`, and TensorFlow/PyTorch handoff patterns.
- Dataset composition: `concatenate_datasets`, `interleave_datasets`, map-style versus iterable shard behavior.
- Cache/fingerprint behavior for Arrow-backed processing and why iterable processing does not reuse map-style cache files.

## Reference Routing

- Read `references/processing-workflows.md` for practical decision trees and end-to-end patterns for map-style, streaming, batching, framework handoff, and combining datasets.
- Read `references/api-reference.md` for concrete parameter guidance, return semantics, and method differences across `Dataset`, `IterableDataset`, and dictionary containers.
- Read `references/troubleshooting.md` when processing fails with Arrow length/schema errors, multiprocessing pickling issues, cache reuse surprises, shuffle limitations, formatter dependency errors, or mixed type failures.
- Run `scripts/processing_smoke.py --help` to see a self-contained smoke check. Run it without arguments to verify local `datasets` processing behavior without downloading data.

## Quick Guidance

Prefer map-style `Dataset` when you need random access, exact length, deterministic splits, cached Arrow transforms, or repeated inspection. Prefer `IterableDataset` when data is too large to materialize, when streaming from files or the Hub, or when fast approximate shuffling is sufficient for training.

For batched `map`, every returned column must have the same length within a batch. If the function changes row counts, overwrite existing columns or pass `remove_columns` for columns whose old length no longer matches. If the output type should be stable, pass explicit `features`; for mixed Python types, review `on_mixed_types` in `references/api-reference.md`.

Use `with_format(...)` for non-mutating formatting and `set_format(...)` for in-place formatting. Framework formatters may require optional packages such as PyTorch, TensorFlow, JAX, pandas, polars, image, or audio extras; do not assume those are installed.
