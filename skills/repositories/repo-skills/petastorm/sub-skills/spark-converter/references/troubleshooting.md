# Troubleshooting

## Purpose

Read this when a Spark converter workflow fails because Spark cannot start, the cache path is wrong, optional backends are missing,
or cleanup behavior is not what you expected.

## Failure map

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Spark session will not start | Java or PySpark is missing | Run `scripts/smoke_spark_session.py` first |
| `Please set the spark config petastorm.spark.converter.parentCacheDirUrl` | The converter cache directory was not configured | Set the Spark config before calling `make_spark_converter` |
| DBFS or path normalization looks wrong | The cache URL needs normalization for the target environment | Check the URL family and normalize the path before converting |
| File availability waits time out | The cached parquet files are not yet visible to the consumer | Confirm the cache path is shared and accessible from the reader context |
| TensorFlow loader creation fails | TensorFlow is missing or the loader settings are invalid | Install the TF extra and retry the smoke script |
| PyTorch loader creation fails | `torch` is missing or import order is wrong | Import `pyarrow` before `torch` and retry |
| Cleanup leaves cache files behind | The delete handler is not appropriate for the filesystem | Use `register_delete_dir_handler` or call `converter.delete()` after fixing the path |
| Horovod warnings appear | `cur_shard` and `shard_count` do not match the Horovod environment | Align the reader kwargs with the rank and size that the environment exposes |
| Vector columns fail on old Spark versions | The Spark build is too old for the vector conversion path | Upgrade Spark or avoid that path in the smoke case |

## Recovery checklist

1. Run `scripts/check_install.py`.
2. Run `scripts/smoke_spark_session.py`.
3. Confirm the cache directory config is set on the Spark session.
4. Retry with `scripts/smoke_spark_converter.py`.
5. If the failure is filesystem-specific, test a local `file://` cache path first.

## Practical tips

- Keep the smoke path local and tiny until the converter is stable.
- Delete the converter cache explicitly after a successful run.
- Prefer the default loader path before experimenting with custom loader factories.
