# Bag and Bytes API Reference

## Imports and Collection Model

```python
import dask.bag as db
from dask.bytes import read_bytes
```

A `dask.bag.Bag` is a lazy, partitioned, unordered collection of Python objects. It is a good fit for text lines, log events, dictionaries, tuples, JSON-like records, and custom Python objects. It is less appropriate for relational analytics that need joins, sorted indexes, typed columns, or repeated shuffles; convert to `dask.dataframe` for those.

By default, Bag computation uses the process-based scheduler when available, which helps pure-Python functions bypass the GIL. Users can still pass `scheduler=` to `compute()` or configure schedulers globally.

## Creation APIs

| API | Use for | Important notes |
| --- | --- | --- |
| `db.from_sequence(seq, partition_size=None, npartitions=None)` | Small in-memory sequences or lists of filenames | The sequence is materialized as a list; avoid using it to load large data into memory first. |
| `db.read_text(urlpath, blocksize=None, compression="infer", encoding=..., errors="strict", linedelimiter=None, collection=True, storage_options=None, files_per_partition=None, include_path=False)` | Text files, line-delimited records, local/cloud paths | `blocksize=None` streams one partition per file by default. Set `blocksize` to split large uncompressed files. `files_per_partition` groups many small files but is mutually exclusive with `blocksize`. |
| `db.read_avro(urlpath, blocksize=100000000, storage_options=None, compression=None)` | Avro records as dictionaries | Requires `fastavro`. Use `blocksize=None` for externally compressed Avro files. |
| `db.from_delayed(values)` | Existing delayed objects where each delayed value is a partition sequence | Each delayed object should compute to a concrete sequence such as a list. |
| `db.concat(bags)` | Union many bags into one bag | Concatenates partitions; does not sort records. |
| `db.range(...)` | Lazy integer ranges | Useful for synthetic or index-like workloads. |
| `db.from_url(urls)` | Simple URL byte-line reads | Uses URL opening directly; prefer fsspec-backed IO for production storage workflows. |

## Transformation APIs

| API | Pattern | Notes |
| --- | --- | --- |
| `bag.map(func, *args, **kwargs)` / `db.map` | Elementwise transformation | Bag arguments must have compatible partitioning. `Item` and delayed arguments can be embedded into one graph. |
| `bag.starmap(func, **kwargs)` | Tuple records as function arguments | Useful after `.str.split()` or parsing structured tuples. |
| `bag.filter(predicate)` / `bag.remove(predicate)` | Keep or drop records | Empty partitions are allowed. |
| `bag.map_partitions(func, *args, **kwargs)` | Partition-level batching | `func` receives an iterator/iterable and should return an iterable. All Bag inputs must be partitioned identically. |
| `bag.pluck(key, default=...)` | Extract dict keys or tuple/list positions | Pass `default` for missing keys/positions when records are irregular. |
| `bag.flatten()` | Flatten nested iterables one level | Common after parsing files that produce lists of records per line. |
| `bag.repartition(npartitions=...)` | Change number of partitions | `partition_size=` estimates memory and triggers computation; use knowingly. |

## Reduction and Grouping APIs

| API | Result | Prefer when |
| --- | --- | --- |
| `bag.count()`, `sum()`, `min()`, `max()`, `mean()`, `var()`, `std()` | `dask.bag.Item` | Simple global reductions. |
| `bag.frequencies(split_every=None, sort=False)` | Bag of `(value, count)` pairs | Counting hashable items. `sort=True` sorts by count descending within the final result. |
| `bag.fold(binop, combine=None, initial=..., split_every=None)` | `Item` by default | Custom associative reductions. Provide `combine` when partition totals have a different shape from raw elements. |
| `bag.foldby(key, binop, initial=..., combine=None, combine_initial=..., split_every=None)` | Bag of `(key, aggregate)` | Efficient per-key reductions; avoids full `groupby` shuffle. String/non-callable keys are treated as record index/key selectors. |
| `bag.groupby(grouper, shuffle=None, npartitions=None, blocksize=..., max_branch=None)` | Bag of `(key, list_of_records)` | Only when all grouped records are needed. It performs a full shuffle; use `foldby` when reducing per key. |
| `bag.distinct(key=None)` | Unique values or unique records by key | Output order is not a stable contract. |
| `bag.topk(k, key=None)` | Largest `k` values | `key` may be callable or an item selector. |

`split_every` controls tree-reduction fan-in. Smaller values create deeper reduction trees with lower per-task fan-in; larger values reduce graph depth but combine more data per task.

## Output and Interop APIs

| API | Use for | Notes |
| --- | --- | --- |
| `bag.take(k, npartitions=1, compute=True, warn=True)` | Peek at a small prefix | Reads only the first partition by default. Use `npartitions=-1` to search all partitions. Because bags are unordered, this is a diagnostic sample, not a deterministic global first unless input partition order is controlled. |
| `bag.compute()` / `list(bag)` | Local Python results | Materializes the full result; safe only when it fits memory. |
| `bag.to_textfiles(path, name_function=None, compression="infer", encoding=..., compute=True, storage_options=None, last_endline=False)` | One text file per partition | Map records to strings first, for example with `json.dumps`. `path` may contain `*`; `name_function` output must preserve partition order. |
| `bag.to_avro(filename, schema, ..., compute=True)` | One Avro file per partition | Requires `fastavro` and a complete schema dictionary. |
| `bag.to_dataframe(meta=None, columns=None, optimize_graph=True)` | Convert records to Dask DataFrame | Provide `meta` for reliable dtypes/columns. If `meta` is missing, Dask computes one record from the first partition to infer metadata and may fail on empty first partitions. `columns` and `meta` are mutually exclusive. |
| `bag.to_delayed(optimize_graph=True)` | Custom sinks or delayed interop | Returns one delayed object per partition. Use `db.from_delayed` to reconstruct a bag. |

## `dask.bytes.read_bytes`

`read_bytes(urlpath, delimiter=None, not_zero=False, blocksize="128 MiB", sample="10 kiB", compression=None, include_path=False, **storage_options)` returns lazy byte blocks rather than decoded strings.

- Without `include_path`, it returns `(sample, blocks)` where `blocks` is a list per file and each nested item is a delayed byte block.
- With `include_path=True`, it returns `(sample, blocks, paths)`.
- `delimiter=b"\n"` makes block boundaries align with delimiters, useful for line-based formats.
- `sample=False` disables the leading sample; string sizes such as `"40 B"` are parsed.
- `blocksize=None` returns one delayed block per file.
- Chunked reads on compressed files raise because common compression formats do not support efficient random access.
