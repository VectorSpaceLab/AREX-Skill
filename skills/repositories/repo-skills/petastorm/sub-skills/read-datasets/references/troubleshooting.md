# Troubleshooting

## Purpose

Read this when a read-side workflow fails because of missing metadata, a wrong reader type, a backend mismatch, or an adapter-specific limitation.

## Failure map

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| PyTorch segfaults or imports behave oddly after `torch` import | `torch` was imported before `pyarrow` | Import `pyarrow` first, then re-run the smoke script |
| `make_reader` warns about non-Petastorm data | The store lacks Petastorm metadata | Switch to `make_batch_reader` or repair metadata in `create-datasets` |
| `Unknown cache_type` | A cache type outside the documented set was passed | Use `null` or `local-disk` |
| `Unknown reader_pool_type` | A pool name outside `thread`, `process`, or `dummy` was passed | Use a documented pool name |
| TensorFlow repeat warnings appear | The dataset is being repeated instead of using reader epochs or cache | Prefer `num_epochs` or cache before repeat |
| `tf_tensors` rejects a shuffling queue with batched output | The reader already emits batches | Set `shuffling_queue_capacity=0` or use a non-batched reader |
| PyTorch rejects `None` or string arrays | The selected fields are not torch-friendly | Drop or transform those fields before batching |
| `WeightedSamplingReader` raises schema or ngram errors | Readers do not match on schema, batching, or ngram state | Rebuild the inputs so they share the same shape contract |
| NGram logic errors out on ordering | Rows are not sorted by the timestamp field | Sort the upstream dataset or widen the generation path |
| `dataset_as_rdd` fails on a path | The dataset URL or filesystem backend is wrong | Fix the URL family and confirm the backend support |
| Very old legacy Petastorm fixtures fail with `Can't get attribute '_restore' on pyspark.serializers` | The fixture predates the current PySpark serializer format | Treat the fixture as archival, use `make_batch_reader` for plain Parquet, or regenerate metadata from a current write path |

## Recovery steps

1. Run `scripts/check_install.py` to confirm the import surface and optional extras.
2. If Spark is part of the failure, run `scripts/smoke_spark_session.py`.
3. If the dataset URL is suspect, read `references/filesystems-and-paths.md`.
4. If the dataset is not Petastorm-formatted, decide whether to read it as plain Parquet or regenerate metadata.
5. If the issue is adapter-specific, rerun the corresponding read smoke script:
   - `scripts/smoke_read_minimal_dataset.py`
   - `scripts/smoke_read_plain_parquet.py`
   - `scripts/smoke_read_tensorflow.py`
   - `scripts/smoke_read_torch.py`

## Practical notes

- `make_reader` is the Petastorm-first path.
- `make_batch_reader` is the plain-Parquet path.
- PyTorch users should always import `pyarrow` before `torch`.
- TensorFlow users should prefer the reader epoch controls rather than repeated dataset loops when they want a clean smoke test.
