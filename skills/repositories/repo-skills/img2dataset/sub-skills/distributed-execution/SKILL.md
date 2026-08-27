---
name: distributed-execution
description: "Choose and debug img2dataset distributed execution, throughput
  tuning, logging, and large-scale operations."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# distributed-execution

Use this sub-skill when an img2dataset task depends on execution scale rather than on URL-table schema, image transforms, or core downloader options: choosing a distributor, preparing PySpark or Ray, tuning throughput, reading speed/status logs, enabling W&B, or debugging slow and failed distributed shards.

## Triggers

- The user asks which `--distributor` to use. The supported values are exactly `multiprocessing`, `pyspark`, and `ray`.
- The user mentions PySpark, SparkSession, Java, Spark clusters, Ray clusters, or distributed workers.
- The user needs to tune `processes_count`, `thread_count`, `subjob_size`, `number_sample_per_shard`, or `max_shard_retry` for a large run.
- The user has low images/sec, many failed shards, W&B/account issues, DNS bottlenecks, object-store filesystem questions, or wants to interpret stats and status logs.

## Route elsewhere

- Core command construction, HTTP retries, SSL, hash verification, incremental mode, user-agent, and X-Robots-Tag handling: route to `../core-download/SKILL.md`.
- Input formats, URL/caption/additional columns, output layouts, shard metadata schemas, and TFRecord writer details: route to `../input-output-formats/SKILL.md`.
- Resize modes, encoding, interpolation, image filters, `skip_reencode`, `disable_all_reencoding`, and bbox blurring: route to `../image-processing/SKILL.md`.

## Short workflow

1. Confirm the target scale and runtime: single host, Spark cluster, or Ray cluster. If optional backends are uncertain, run `python scripts/check_distributed_backends.py --json` from this sub-skill directory.
2. Choose one exact distributor value using `references/distributed-execution.md`.
3. Size local work with `processes_count` and `thread_count`; size PySpark dispatch with `subjob_size`; choose a retry policy with `max_shard_retry` and a restartable output folder.
4. Prefer `webdataset` for large datasets unless another sibling sub-skill's format contract requires a different output format.
5. Enable observability deliberately: stats files are always written; `--enable_wandb=True` adds W&B metrics/status tables when account or anonymous logging is acceptable.
6. If throughput or failures are poor, use `references/performance-tuning.md` first, then `references/troubleshooting.md` for backend-specific errors.

## Critical gotchas

- PySpark requires `pyspark` and a Java runtime. If no active `SparkSession` exists, img2dataset creates a local session with `local[processes_count]` and stops it afterward; if a session already exists, img2dataset uses it and leaves ownership to the caller.
- Ray is optional. In the current implementation, missing Ray can make the Ray distributor a no-op, so verify Ray before selecting `--distributor ray`.
- Avoid outdated Ray `local_mode=True` guidance; use current `ray.init(...)` patterns such as `ray.init(num_cpus=1)` for a short local smoke or `ray.init(address="auto")` for a cluster.
- `max_shard_retry` is an end-of-run shard retry loop for multiprocessing and PySpark. The current Ray path does not apply that retry loop.

## References and scripts

- `references/distributed-execution.md` — mode decision tree, PySpark/Ray/SparkSession behavior, self-contained command templates.
- `references/performance-tuning.md` — process/thread/shard sizing, bottleneck diagnosis, W&B/stat usage, filesystem and benchmark guidance.
- `references/troubleshooting.md` — missing optional dependencies, Java/Spark/Ray/W&B/DNS/filesystem failure modes.
- `scripts/pyspark_download_template.py` — dry-run-first PySpark download template; only imports Spark/img2dataset for `--run` or `--check-backends`.
- `scripts/check_distributed_backends.py` — safe optional-backend checker for PySpark, Java, Ray, TensorFlow/TFIO, W&B, and fsspec.
