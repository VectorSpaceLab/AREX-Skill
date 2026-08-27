# API Reference

This file records the verified read-side surface for WebDataset 1.0.2 / module 1.0.2.
It focuses on loading, transforming, decoding, batching, and loader integration.

## Core objects

| API | Verified signature | Notes |
| --- | --- | --- |
| `DataPipeline.__init__` | `(self, *args, **kwargs)` | Ordered stage list. |
| `DataPipeline.compose` | `(self, *args)` | Copy-on-write stage addition. |
| `WebDataset.__init__` | `(self, urls, handler=reraise_exception, mode=None, resampled=False, repeat=False, shardshuffle=None, cache_size=-1, cache_dir=None, url_to_name=pipe_cleaner, detshuffle=False, nodesplitter=single_node_only, workersplitter=split_by_worker, select_files=None, rename_files=None, empty_check=True, verbose=False, seed=None)` | Main read entry point. `resampled=True` forces `mode="resampled"`. `shardshuffle=None` warns. |
| `WebLoader.__init__` | `(self, *args, **kw)` | Thin wrapper around `torch.utils.data.DataLoader`. |
| `FluidInterface.decode` | `(self, *args, pre=None, post=None, only=None, partial=False, handler=reraise_exception)` | String args become `ImageHandler(...)`. |
| `FluidInterface.shuffle` | `(self, size, **kw)` | `size < 1` returns `self`. |
| `FluidInterface.to_tuple` | `(self, *args, **kw)` | Forwards to `filters.to_tuple`. |

### Important defaults

- `nodesplitter=single_node_only` raises on multi-node input unless you override it.
- `workersplitter=split_by_worker` is the default DataLoader split.
- `empty_check=True` appends a final emptiness check.
- `shardshuffle=True` is normalized to `100`.
- `cache_dir` is validated when present.
- `with_length()` only sets `__len__`; it does not change how many samples are yielded.

## Filters and transforms

| API | Signature | Notes |
| --- | --- | --- |
| `map` | `(data, f, handler=reraise_exception)` | Drops `None` results. Dict-to-dict results keep `__key__`. |
| `map_dict` | `(data, handler=reraise_exception, **kw)` | Applies one function per key. |
| `select` | `(data, predicate)` | Keeps matching samples. |
| `rename` | `(data, handler=reraise_exception, keep=True, **kw)` | Lookup-based rename. Missing keys raise unless handled. |
| `rename_keys` | `(source, *args, keep_unselected=False, must_match=True, duplicate_is_error=True, **kw)` | Glob rename on sample keys. |
| `extract_keys` | `(source, *patterns, duplicate_is_error=True, ignore_missing=False)` | Optional field extraction is supported with `ignore_missing=True`. |
| `to_tuple` | `(data, *args, handler=reraise_exception, missing_is_error=True, none_is_error=None)` | Space-separated and semicolon-separated key specs are both supported. |
| `rsample` | `(data, p=0.5)` | Random sample drop. |
| `slice` | `(data, *args)` | Wraps `itertools.islice`. |
| `batched` | `(data, batchsize=20, collation_fn=default_collation_fn, partial=True)` | `partial=False` drops the last short batch. |
| `unbatched` | `(data)` | Expands batch structures back to samples. |
| `repeat` | `(self, nepochs=-1, nbatches=-1)` | Repeats iteration; unlimited when `nepochs <= 0`. |
| `with_epoch` | `(self, nsamples=-1, nbatches=-1)` | Controls effective epoch length. |
| `with_length` | `(self, n, silent=False)` | Declares a length without changing sample count. |

### Batch notes

- `default_collation_fn` checks that keys match across samples.
- Scalars become NumPy arrays, and tensors stack when shapes match.
- `unbatched` handles tuple/list batches and dict batches with equal-length values.
- Nested dicts with inconsistent lengths are a known failure mode.

### Loader-side wrappers

The package also exports loader-side wrappers in `webdataset.pytorch`:

- `with_epoch(dataset, length)` — wraps an `IterableDataset` and yields exactly `length` samples per epoch.
- `with_length(dataset, length)` — declares a length without changing the underlying sample stream.
- `repeatedly(source, nepochs=None, nbatches=None, nsamples=None, batchsize=guess_batchsize)` — repeat helper used by the loader-side wrappers.

Prefer the fluent `DataPipeline` methods when you are already inside a pipeline; use the wrappers when a caller specifically wants an `IterableDataset` object.

## Decoding notes

- `decode()` uses `autodecode.Decoder`.
- Default pre-handler: gzip decompression.
- Default post-handler: extension-based basic decoding.
- `partial=False` means non-bytes fields are not silently passed through.
- `DecodingError` includes `key`, `url`, `k`, and `sample`.
- `decode("pil")`, `decode("rgb")`, and `decode("torchrgb")` are backed by `ImageHandler`.

## Shards, splitting, and mixing

| API | Signature | Notes |
| --- | --- | --- |
| `SimpleShardList` | `(urls, seed=None)` | Expands brace notation, `::` lists, and environment substitutions. |
| `ResampledShards` / `ResampledShardList` | `(urls, nshards=sys.maxsize, seed=0, worker_seed=None, deterministic=False, max_urls=1e6, empty_check=True)` | Samples shards with replacement. |
| `DirectoryShardList` | `(path, pattern='*.{tar,tgz,tar.tgz}', poll=1, timeout=1e12, mode='resample', select='random', fate=None)` | Requires a directory path ending in `/`. |
| `split_by_node` | `(src, group=None)` | Distributed rank striding. |
| `split_by_worker` | `(src)` | DataLoader worker striding. |
| `single_node_only` | `(src, group=None)` | Raises when `world_size > 1`. |
| `RoundRobin` | `(datasets, longest=False)` | Alternates between datasets. |
| `RandomMix` | `(datasets, probs=None, longest=False)` | Probability-weighted sampling. |

## Tar-file read helpers

| API | Signature | Notes |
| --- | --- | --- |
| `tarfile_to_samples` | `(src, handler=reraise_exception, select_files=None, rename_files=None)` | Opens URLs, expands tar members, and groups files into samples. |
| `tar_file_iterator` | `(fileobj, skip_meta=r"__[^/]*__($|/)", handler=reraise_exception, select_files=None, rename_files=None)` | Applies file-level selection/renaming before grouping. |
| `group_by_keys` | `(data, keys=base_plus_ext, lcase=True, suffixes=None, handler=reraise_exception)` | Emits `__key__`, `__url__`, and optionally `__local_path__`. |

## Practical rules

- Set `shardshuffle` explicitly; do not rely on the warning default.
- Apply `select_files` / `rename_files` before grouping when you want to trim member sets.
- Use `empty_check=False` only when you intentionally allow empty workers or inner column readers.
- Use `compose()` for reusable pipelines.
- Use `batched(...).unbatched()` when you need loader-level rebatching.

## Cross-links

- For read-after-write validation, go to the sibling [shard-writing](../../shard-writing/SKILL.md) skill.
- For `gopen`, cache, and secure-mode behavior, go to the sibling [io-caching-security](../../io-caching-security/SKILL.md) skill.
