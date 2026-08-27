# Distributed execution troubleshooting

Use this matrix after confirming the basic command and data schema with sibling sub-skills. It focuses on backend availability, scheduling, throughput, logging, and large-scale operations.

## Backend and cluster errors

| Symptom | Likely cause | Checks | Fix |
| --- | --- | --- | --- |
| `ModuleNotFoundError: No module named 'pyspark'` | PySpark not installed in the active environment | `python scripts/check_distributed_backends.py --json` | Install `pyspark` in the driver environment; ensure executors use a compatible Python environment. |
| PySpark reports Java gateway failure or no Java | Java runtime missing or not on `PATH` | `java -version`; checker Java section | Install OpenJDK 11 or 17, set `JAVA_HOME` if site policy requires it, and verify both driver and workers. |
| Console says no PySpark session found and creates one | Expected behavior when no active session exists | Look for local master and app name `spark-stats` | For local runs this is fine. For a cluster, create your own `SparkSession` before calling `download(...)` or use `scripts/pyspark_download_template.py --master spark://... --run`. |
| Spark local works but cluster workers fail | Workers cannot import img2dataset/dependencies or access paths | Spark executor logs; worker environment; fsspec credentials | Install the same package set on workers, use a packaged Python executable, or configure Spark files/env; put input/output on shared or remote storage. |
| Spark driver stalls before work starts | Large shard staging or object-store temp writes | Spark UI, driver logs, temp filesystem latency | Reduce `subjob_size`; check object-store/fsspec config; consider larger local driver resources. |
| Repeated Spark task failures | Bad shard data, environment mismatch, remote host errors, or too-large batches | Spark task logs, `*_stats.json` status_dict | Lower `subjob_size`, verify schema and worker dependencies, and separate deterministic failures from transient network errors. |

## Ray errors

| Symptom | Likely cause | Checks | Fix |
| --- | --- | --- | --- |
| `--distributor ray` finishes without useful output | Ray is not importable; fallback distributor returns without work | `python scripts/check_distributed_backends.py --json` | Install `ray` and verify import before selecting Ray. Prefer multiprocessing or PySpark when unsure. |
| Ray uses local resources instead of cluster | Ray was not initialized with the cluster address | In wrapper script, check `ray.is_initialized()` and `ray.init(...)` arguments | Call `ray.init(address="auto")` or the cluster-specific address before `download(...)`. |
| Code examples using `local_mode=True` fail | Deprecated/removed Ray API in recent versions | Ray version in checker output | Do not use `local_mode=True`. Use `ray.init(num_cpus=1)` for a short local smoke or `ray.init(address="auto")` for clusters. |
| Failed shards are not retried in Ray | Current Ray distributor does not call the shared retry loop | Compare Ray behavior with multiprocessing/PySpark docs | Inspect stats, fix root causes, and rerun incrementally. Use multiprocessing or PySpark when `max_shard_retry` semantics are required. |

## W&B and logging issues

| Symptom | Likely cause | Checks | Fix |
| --- | --- | --- | --- |
| W&B asks for login or account choice | First run with `--enable_wandb=True` | Console prompt | Run `wandb login` before production, choose anonymous logging if acceptable, or disable W&B. |
| W&B cannot reach service | Network/firewall/account restrictions | W&B error output; network policy | Disable W&B, use W&B offline mode, or run where outbound access is allowed. Stats JSON files still provide local observability. |
| No W&B status table appears | W&B disabled or no frequent statuses yet | Command flags; W&B run page | Confirm `--enable_wandb=True` and wait for logger intervals; inspect `*_stats.json` directly. |
| Speed logs look stale | Logger waits for new stats files and periodic intervals | Output folder contains new `*_stats.json` files | Check worker progress, filesystem listings, and object-store latency. Logger aggregation depends on discovering stats JSON files. |

## Throughput and failure loops

| Symptom | Likely cause | Checks | Fix |
| --- | --- | --- | --- |
| Images/sec far below expected, CPU idle | Too few threads, DNS bottleneck, network cap, remote throttling | Network monitor, status_dict, DNS errors | Increase `thread_count` gradually; deploy knot resolver or bind9; confirm upstream bandwidth and remote server limits. |
| CPU saturated, network idle | Resize/reencode CPU bottleneck | CPU monitor; speed logs; failed resize ratio | Lower `thread_count` or `processes_count`; review image-processing settings; benchmark with CPU work disabled only for diagnosis. |
| Disk saturated or many tiny files | Output format or shard sizing | Disk monitor, inode/file count, output layout | Use `webdataset`; increase shard size if safe; avoid `files` output for large datasets. |
| Object-store writes/listing are slow | fsspec backend configuration, too many stats/shards | Object-store logs, fsspec package/credential checks | Install required fsspec backend package, configure endpoints/credentials via fsspec config, use fewer/larger shards. |
| `Retrying N shards` repeats with no improvement | Persistent deterministic failure | Stats status_dict, sample failed shard, dependency/schema checks | Do not keep increasing `max_shard_retry`; fix DNS, SSL, schema, filesystem, or remote-host problem. Then rerun with the same output folder and stable shard sizing. |
| Completed shards are redownloaded after restart | Output folder or shard sizing changed | Compare output folder, `number_sample_per_shard`, input ordering, incremental mode | Reuse the same output folder, input ordering, and `number_sample_per_shard`; let incremental mode skip existing stats. |

## Filesystem and optional dependency issues

| Symptom | Likely cause | Checks | Fix |
| --- | --- | --- | --- |
| `s3://`, `gcs://`, `ssh://`, or `hf://` path fails | Missing fsspec backend or credentials | Checker output for fsspec; package imports; credential config | Install packages such as `s3fs`, `gcsfs`, SSH fsspec support, or `huggingface_hub`; configure credentials outside the command. |
| S3-compatible endpoint cannot connect | fsspec endpoint config missing | fsspec config files and object-store policy | Configure endpoint URL and credentials through fsspec configuration; avoid embedding secrets in examples. |
| TFRecord path or TensorFlow warnings appear during distributed run | TFRecord writer/backend issue rather than distribution itself | Checker TensorFlow/TFIO sections; writer logs | Route layout and writer behavior to `../input-output-formats/SKILL.md`. CPU-only TensorFlow messages and non-fatal TFIO plugin warnings can be harmless if a tiny TFRecord write succeeds. |

## Safety reminders

- Do not run large benchmark or S3 benchmark scripts as user-facing helpers; they are unsafe because they depend on external datasets, credentials, absolute machine paths, or destructive deletes.
- Do not leak private environment paths into commands or handoffs. Describe prerequisites such as Java, PySpark, Ray, TensorFlow, W&B, and fsspec packages instead.
- Prefer reproducible dry-runs and backend checks before cluster downloads.
