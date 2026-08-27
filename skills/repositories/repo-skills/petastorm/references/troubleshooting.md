# Troubleshooting

## Purpose

Read this first when a Petastorm task fails in a way that looks like an environment, URL, or runtime mismatch.

## Cross-cutting failure map

| Symptom | Likely cause | Next step |
| --- | --- | --- |
| PyTorch crashes or behaves strangely after import | `torch` was imported before `pyarrow` | Import `pyarrow` first and re-run `scripts/check_install.py` |
| Spark session cannot start | Java or Spark is missing | Run `scripts/smoke_spark_session.py` and fix the local Spark install |
| URL parsing fails for local data | Path is missing `file://` | Fix the URL using `references/filesystems-and-paths.md` |
| `make_reader` warns about a non-Petastorm Parquet store | The dataset lacks Petastorm metadata | Use `make_batch_reader` or repair metadata in `create-datasets` |
| Optional codec or backend import fails | The matching extra is missing | Install the relevant extra or backend package |
| Historical TensorFlow-dependent tests fail with `inspect.getargspec` | A legacy helper still uses a Python 3.11-removed API | Use the bundled smoke scripts instead of the old test helper, or reproduce the historical test under an older Python if you specifically need it |
| `Unknown cache_type` or `Unknown reader_pool_type` | A value outside the documented set was passed | Use the values from the read-datasets API reference |
| TensorFlow warns about repeated iterations | A `tf.data.Dataset` repeat path is being used directly | Prefer reader epochs or cache before repeat |
| PyTorch rejects strings or `None` values | The selected fields are not torch-friendly | Drop or transform those fields before building the loader |

## Recovery habits

- Re-run `scripts/check_install.py` after changing the environment.
- Re-run `scripts/smoke_spark_session.py` after changing Java or Spark.
- If the failure is about a dataset URL, fix the scheme and bucket/netloc before opening the reader or writing the dataset.
- If the failure is about metadata, decide whether the dataset should be read as a plain Parquet store or repaired as a Petastorm dataset.

## Where to look next

- Reader and adapter failures: `sub-skills/read-datasets/references/troubleshooting.md`
- Schema, metadata, and write failures: `sub-skills/create-datasets/references/troubleshooting.md`
- Spark cache conversion failures: `sub-skills/spark-converter/references/troubleshooting.md`
