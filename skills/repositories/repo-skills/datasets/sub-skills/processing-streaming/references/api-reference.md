# Processing API Reference

This reference summarizes high-value transformation parameters and return semantics for `datasets` 5.0.1.dev0 behavior verified during skill generation.

## Container Semantics

`Dataset` is Arrow-backed, eager, randomly indexable, and cache/fingerprint-aware. Most processing methods return a new `Dataset`; `set_format` mutates formatting state in place.

`IterableDataset` is lazy and stream-oriented. Transform calls return another iterable pipeline and execute as examples are pulled. It does not support arbitrary row indexing or map-style processing cache reuse.

`DatasetDict` and `IterableDatasetDict` apply many operations split-by-split and return dictionary containers. When combining or interleaving, pick individual splits first; composition functions expect a list of datasets, not a dictionary with multiple splits.

## `Dataset.map`

Important parameters:

- `function`: callable that returns a dictionary of new or updated columns. `None` can be used for cache/materialization-style operations.
- `with_indices`: passes example indices to the function.
- `with_rank`: passes multiprocessing worker rank to the function when relevant.
- `input_columns`: passes only selected column values instead of full examples.
- `batched`: when `True`, the function receives batches and may return a different number of rows.
- `batch_size`: input batch size for batched mapping; defaults to `1000`.
- `drop_last_batch`: drops a final short input batch when batching.
- `remove_columns`: removes columns before writing outputs; essential when batched output row count differs from input row count.
- `keep_in_memory`: keeps processed data in memory instead of writing cache files.
- `load_from_cache_file`: controls whether a matching cache fingerprint can be reused.
- `cache_file_name`: explicit cache file path for map-style output; avoid in portable public examples unless user owns the path.
- `writer_batch_size`: controls Arrow writer batch size; reduce for memory pressure, increase for throughput.
- `features`: explicit output schema; use when output types should be stable or row-count-changing maps create new columns.
- `disable_nullable`: request non-nullable output fields where possible.
- `fn_kwargs`: serializable extra keyword arguments for the function.
- `num_proc`: process count for multiprocessing map.
- `suffix_template`: filename suffix template for per-rank cache files when multiprocessing.
- `new_fingerprint`: explicit fingerprint override; use sparingly because it can force cache identity.
- `desc`: progress description.
- `try_original_type`: attempts to preserve existing feature types when possible.
- `on_mixed_types`: controls handling of mixed Python value types; `use_json` stores mixed values through a JSON-compatible representation.

Checklist for row-count-changing batched maps:

1. Set `batched=True`.
2. Ensure all returned columns have equal lengths in each output batch.
3. Pass `remove_columns` for all old columns whose original batch length no longer matches.
4. Pass `features` when the new schema must be explicit.
5. Assert `len(output)` and `output.column_names` after the map.

## `Dataset.filter`

`Dataset.filter` keeps rows for which the predicate is true. It supports similar execution controls to map, including `with_indices`, `with_rank`, `input_columns`, `batched`, `batch_size`, `keep_in_memory`, `load_from_cache_file`, `cache_file_name`, `fn_kwargs`, `num_proc`, `suffix_template`, `new_fingerprint`, and `desc`.

For `batched=True`, return a list or array of booleans matching the input batch length. Use `with_indices=True` for index-dependent filters.

## Row Selection and Splits

`select(indices)` returns rows at specific indices. Contiguous ranges preserve efficient access better than arbitrary index lists. Non-contiguous selections use an indices mapping and may be slower.

`shuffle(seed=..., generator=...)` creates an exact shuffled index mapping for map-style datasets. Use a fixed seed for reproducibility. If repeated reads become slow, consider `flatten_indices()` after the shuffle.

`train_test_split(test_size=..., train_size=..., shuffle=True, stratify_by_column=None, seed=None)` returns a `DatasetDict` with train/test splits. Use `stratify_by_column` for class-balanced splits when the column supports it. Set `shuffle=False` only when preserving original order matters.

`shard(num_shards, index, contiguous=...)` returns one shard. Use for distributed processing or deterministic partitioning.

## Iterable Transforms

`IterableDataset.map` and `IterableDataset.filter` mirror the conceptual API of map-style transforms but remain lazy and do not create reusable Arrow cache files. Use them for streaming cleanup, tokenization, filtering, and formatting at consumption time.

`IterableDataset.shuffle(seed=None, buffer_size=1000, ...)` is approximate. It samples from a buffer and can shuffle shard order. Larger `buffer_size` improves randomness and memory use. Use `set_epoch(epoch)` between epochs so the effective seed changes.

`take(n)` returns the first `n` examples; `skip(n)` skips the first `n`. Apply `shuffle` before `take` or `skip` because these operations lock shard order.

`shard(num_shards, index)` partitions iterable shards. `reshard(...)` can increase shard count for supported formats such as Parquet row groups, improving parallel loading and shuffle quality.

## Convert Map-Style to Iterable

`Dataset.to_iterable_dataset(num_shards=1)` creates an `IterableDataset` over local Arrow data. This is useful when a dataset has already been downloaded or built and the next step is training with streaming-like iteration, approximate shuffle, or DataLoader worker sharding.

Choose `num_shards` based on expected parallelism. For example, with many PyTorch DataLoader workers or distributed workers, create more shards than workers so work can be balanced.

## Formatting APIs

`set_format(type=None, columns=None, output_all_columns=False, **format_kwargs)` mutates a dataset so indexing returns formatted values. `reset_format()` returns to Python objects.

`with_format(type=None, columns=None, output_all_columns=False, **format_kwargs)` returns a copy with formatting applied. Prefer this in reusable code because it avoids surprising callers.

Common format types include `python`, `numpy`/`np`, `torch`/`pytorch`, `tensorflow`/`tf`, `jax`, `pandas`, `polars`, and `arrow`. Optional packages must be installed for non-core formatters.

`set_transform` and `with_transform` can apply custom formatting transforms at access time. Keep transforms deterministic and lightweight; use `map` for persistent preprocessing.

Conversion helpers include `to_pandas`, `to_polars`, `to_tf_dataset`, and batched `iter(batch_size=...)`. Some helpers are available only on particular dataset types or require optional dependencies.

## Combine APIs

`concatenate_datasets(dsets, axis=0)` appends rows by default. With `axis=1`, it combines columns by row position. All inputs must be the same dataset kind: all `Dataset` or all `IterableDataset`. For iterable inputs, vertical concatenation sums shard counts; horizontal concatenation uses one shard to avoid row misalignment.

`interleave_datasets(datasets, probabilities=None, seed=None, stopping_strategy="first_exhausted")` alternates examples from sources. With probabilities, sources are sampled randomly according to weights. For iterable inputs, the resulting `num_shards` is limited by the minimum input shard count to preserve parallelism.

## Cache and Fingerprints

Map-style transforms update fingerprints from the previous fingerprint plus transform identity and parameters. Hashable, picklable functions make cache reuse stable across sessions. Non-hashable transforms receive random fingerprints and force recomputation.

Formatting operations also affect fingerprints/format state. If a cached result appears stale or unexpectedly reused, inspect the transform function, parameters, `load_from_cache_file`, `new_fingerprint`, and whether caching is enabled.

Iterable transforms are not materialized into the map-style Arrow cache. If a streaming transform is expensive and needs reuse, materialize intentionally in an application-controlled output format or convert to a map-style dataset where appropriate.
