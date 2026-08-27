# Bag and Bytes Troubleshooting

## Partition Sizing

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Too many tiny tasks | Many small files or tiny partitions | Use `files_per_partition=` for `read_text`, choose a larger `partition_size` in `from_sequence`, or group files before `from_delayed`. |
| One partition is too large | `blocksize=None` on a large uncompressed file | Set `blocksize="64 MiB"` or a workload-appropriate size for uncompressed text/bytes. |
| Repartition unexpectedly computes | `Bag.repartition(partition_size=...)` estimates partition memory | Use `npartitions=` when possible, or warn users that size-based repartitioning must inspect partitions. |
| `take(k)` returns fewer rows than expected | It reads only the first partition by default | Use `take(k, npartitions=-1)` for diagnostics or repartition/sample intentionally. |

## Text Blocksize and Delimiters

- `blocksize` is byte-oriented. For text, Dask preserves line or custom delimiter boundaries, but very small blocks can create many tasks.
- `linedelimiter` for `read_text` is a string; `delimiter` for `read_bytes` is bytes.
- Custom delimiters are found by simple delimiter matching. The algorithm does not understand quoting, escaping, or multibyte semantic boundaries inside structured formats.
- `files_per_partition` and `blocksize` cannot both be set for `read_text`; choose grouping many small files or splitting large files.
- If `read_text` raises `ValueError("No files found", urlpath)`, verify the glob, protocol, credentials, and worker-visible path.

## fsspec URLs and `storage_options`

| Symptom | Fix |
| --- | --- |
| Local path works on the client but not workers | Use shared/mounted paths or a remote protocol visible to all workers. Dask normalizes many IO paths, but custom functions may not. |
| Cloud import/backend error | Install the protocol backend such as `s3fs`, `gcsfs`, `adlfs`, or relevant HDFS support. |
| Authentication failure | Pass provider options through `storage_options`, rely on provider environment credentials, or use cluster-managed credentials. Avoid embedding secrets in reusable URLs. |
| `urlpath` with a set fails | Use a string, path-like object, list, or tuple. Sets are unordered and rejected. |
| Unexpected protocol/path parsing | Confirm the URL form is `protocol://path/to/data`; no protocol means local file. |

## Compression Inference and Chunking

| Symptom | Cause | Fix |
| --- | --- | --- |
| `Cannot do chunked reads on compressed files` | `read_bytes` was asked to split compressed streams | Set `blocksize=None` or decompress upstream. |
| Compressed `read_text` fails with block splitting | Common gzip/bz2/xz streams are not safely splittable | Set `blocksize=None` and accept one or grouped file partitions. |
| Compression is not detected | Extension is missing or unusual | Pass `compression="gzip"`, `"bz2"`, `"xz"`, or the registered codec explicitly. |
| Codec name is unknown | Optional compression dependency is missing or not registered with fsspec | Install/register the codec or use a supported format. |

## Avro Optional Dependency

`db.read_avro` and `Bag.to_avro` require `fastavro`. If the user sees an import error mentioning `fastavro`, install that optional dependency in the runtime environment or choose a text/JSON workflow instead.

For externally compressed Avro files, distinguish file-level compression from Avro internal codec:

```python
records = db.read_avro("events/*.avro.gz", blocksize=None, compression="gzip")
```

`to_avro` requires a complete Avro schema. Dask does not infer the schema from bag records.

## Order Non-determinism

Bags are unordered collections. Common surprises:

- `compute()` may produce records in partition order for simple local cases, but workflows should not rely on global ordering semantics.
- `groupby`, `distinct`, `frequencies`, and shuffles can change output order.
- `random_sample(prob, random_state=...)` can be deterministic for a fixed seed and partitioning, but changing partitions changes samples.
- For stable presentation, compute a small result and sort locally, or convert normalized records to dataframe and sort with dataframe semantics.

## `foldby` vs `groupby`

Use `foldby` when the goal is one aggregate per key. It reduces within partitions and combines partial aggregates, avoiding the cost of materializing every group.

Use `groupby` only when the downstream function truly needs the full list of records for each key. If `groupby` is slow, memory-heavy, or creates shuffle errors, rewrite as `foldby` or convert normalized data to dataframe and route the problem to dataframe workflows.

## Converting Irregular Records to DataFrame

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `to_dataframe` fails to infer metadata | First partition is empty or records are irregular | Pass explicit `meta`. |
| Columns are missing or object dtypes are wrong | Metadata inferred from a non-representative row | Normalize records and provide `meta={column: dtype}` or an empty pandas DataFrame. |
| `ValueError` about both `columns` and `meta` | Both parameters were passed | Use `meta` for typed output, or `columns` only for simple tuple/scalar inference. |
| Later dataframe operations fail | Bag records contain nested/heterogeneous values | Flatten or normalize before `to_dataframe`; route dataframe-specific fixes to `dataframe-workflows`. |

## Multiprocessing and Pickling

Bag often defaults to process-based scheduling. Functions passed to `map`, `filter`, `foldby`, and similar operations must be pickleable for the process scheduler. If local lambdas or closures fail under multiprocessing, define top-level functions or use `scheduler="threads"` / `scheduler="single-threaded"` for debugging.
