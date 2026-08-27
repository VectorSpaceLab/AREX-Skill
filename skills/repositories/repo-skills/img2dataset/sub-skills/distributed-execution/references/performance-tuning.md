# Performance tuning and large-scale operations

img2dataset stresses network, DNS, CPU, disk/object storage, and scheduler overhead at the same time. Tune one bottleneck at a time and keep every experiment reproducible by recording the exact distributor, process/thread counts, shard sizing, output format, and logging mode.

## First-pass tuning checklist

1. Prefer `output_format=webdataset` for large datasets. Plain `files` output is convenient for small local jobs but becomes hard for standard filesystems once the dataset approaches millions of files.
2. Start `processes_count` near the number of CPU cores when resizing is enabled. If CPU stays below saturation and disk is healthy, increase cautiously.
3. Increase `thread_count` until bandwidth is saturated or the host starts showing CPU, DNS, timeout, or remote-server failure pressure.
4. Use `number_sample_per_shard` to control output shard size and restart granularity; keep it stable across incremental reruns.
5. In PySpark, use `subjob_size` to balance Spark scheduler overhead against driver preparation time and failure isolation.
6. Turn on W&B only when account, anonymous, or offline logging behavior is acceptable; stats JSON files are still written without W&B.
7. For diagnosis-only benchmarks, remove bottlenecks deliberately: `output_format=dummy` removes storage writes; `disable_all_reencoding=True` removes resize/reencode CPU work. Do not use those settings for final datasets unless the sibling image/output contracts allow it.

## Parameter sizing guide

| Parameter | Applies to | What it controls | Starting point | When to increase | When to decrease |
| --- | --- | --- | --- | --- | --- |
| `processes_count` | multiprocessing, default PySpark local session | Local process count or `local[N]` Spark master if img2dataset creates the session | CPU core count for resizing; smaller on memory-limited hosts | CPU/network idle, one output shard per process is healthy | CPU pegged, memory pressure, too many open files, disk seeks high |
| `thread_count` | downloader workers | Concurrent image downloads inside each worker | 32-256 depending on bandwidth and remote hosts | Bandwidth low and CPU/DNS healthy | DNS timeouts, remote throttling, CPU contention, many failed downloads |
| `number_sample_per_shard` | all modes | Samples per output shard and stats file | 10,000 default | Too many tiny output files, scheduler overhead high | Shards are too large to retry, memory/temp writes are painful |
| `subjob_size` | PySpark | Number of reader shards per Spark batch | 1,000 default only after validating scale | Workers idle from scheduler overhead | Driver spends too long staging batches, failures are hard to isolate |
| `max_shard_retry` | multiprocessing, PySpark | End-of-run retry attempts for failed shards | 1 default | Failures are transient network/object-store issues | Failures are deterministic; fix root cause before looping |

## Bottleneck diagnosis

| Symptom | Likely bottleneck | Evidence to collect | Tuning response |
| --- | --- | --- | --- |
| CPU near 100%, network below capacity | Resize/reencode CPU | Host CPU monitor, low images/sec, high worker duration | Lower `processes_count` or `thread_count`, change image-processing choices, benchmark with `disable_all_reencoding=True` to confirm. |
| Network below expected and CPU idle | Thread count, remote servers, DNS, bandwidth | Network monitor, status table, many timeout/name errors | Increase `thread_count` gradually; set up a local caching DNS resolver; confirm upstream bandwidth limits. |
| Many name-resolution errors | DNS resolver saturation | Status table/status_dict contains resolver failures; system resolver logs | Use a high-performance resolver such as knot resolver or bind9 on every busy node; point `/etc/resolv.conf` or host networking to it according to site policy. |
| Disk busy or millions of small files | Output format/filesystem | Disk I/O monitor, inode/file-count pressure | Prefer `webdataset`; use fewer larger shards; write to fast local or properly configured object storage. |
| Spark workers idle, driver busy | PySpark scheduler/staging overhead | Spark UI, long gaps between batches | Increase `subjob_size`, reduce per-batch overhead, ensure temp files and output storage are fast. |
| Spark failures repeat by shard | Data/schema or executor environment | Spark executor logs and `*_stats.json` | Verify every worker can import dependencies and access input/output paths; reduce `subjob_size` to isolate. |
| W&B hangs/prompts unexpectedly | Account/network policy | Console prompt, W&B status | Log in beforehand with `wandb login`, allow anonymous logging, set offline mode, or disable W&B. |

## DNS resolver notes

Large URL lists generate huge numbers of domain lookups. The project documentation recommends an efficient local resolver for high throughput and success rate:

- **knot resolver** can run multiple instances and is a good parallel resolver option.
- **bind9** is a mature resolver; the documentation reports it gave strong results for this workload.

Operational guidance:

- Install and validate the resolver outside img2dataset before scaling downloads.
- Check lookups with a command such as `dig @localhost example.com` according to your site policy.
- On clusters, configure every worker, not just the driver.
- DNS improvements often reduce both low throughput and failed-download ratios.

## Filesystem and fsspec considerations

img2dataset uses fsspec for many input/output paths. Prefixes such as `hdfs://`, `s3://`, `http://`, `gcs://`, `ssh://`, and `hf://` select different filesystem implementations.

Common optional packages:

- `s3fs` for S3-compatible object stores.
- `gcsfs` for Google Cloud Storage.
- `sshfs`/fsspec SSH support for SSH-backed paths.
- `huggingface_hub` for Hugging Face filesystem paths.

Tuning considerations:

- Configure credentials and endpoint options through fsspec's configuration mechanism rather than embedding secrets in commands.
- Object stores may need larger shards and fewer list operations; logger/stat aggregation lists `*.json` stats files repeatedly.
- TFRecord output has different filesystem support than the fsspec-backed writers; route TFRecord layout questions to `../input-output-formats/SKILL.md`.

## W&B and stats usage

Stats files are always the first source of truth:

- `count`: samples attempted in the shard.
- `successes`: successful image outputs.
- `failed_to_download`: network/HTTP/fetch failures.
- `failed_to_resize`: decode/resize/filter failures.
- `duration`, `start_time`, `end_time`: shard timing.
- `status_dict`: frequent statuses/errors useful for triage.

W&B adds live observability when enabled:

```bash
img2dataset ... --enable_wandb=True --wandb_project img2dataset
```

The logger calls W&B with anonymous logging allowed. On first use, users can associate metrics with an account, log anonymously, or log in beforehand with `wandb login`. In restricted environments, disable W&B or use W&B offline mode according to local policy.

## Benchmark script inventory decisions

| Source pattern | Runtime decision | Why |
| --- | --- | --- |
| Small benchmark using `test_10000.parquet` with W&B and multiprocessing | Reference only | Useful parameter example, but tied to repository fixtures and benchmark-specific settings. |
| Distributed PySpark tutorial | Reference only | Valuable cluster prerequisites and SparkSession patterns, but setup is cloud/SSH/site-specific. |
| Large local benchmark scripts | Excluded from runnable skill scripts | They use absolute machine paths, destructive deletes, huge external datasets, and W&B/network assumptions. |
| S3 benchmark script | Excluded from runnable skill scripts | It performs destructive recursive S3 deletion and requires credentials, bucket ownership, and external data. |

## Tuning plans for hard cases

### Low throughput on one large host

1. Baseline with `multiprocessing`, `webdataset`, `processes_count` near core count, and moderate `thread_count`.
2. Watch CPU, network, DNS, and disk while reading `*_stats.json` and speed logs.
3. If CPU-bound, lower threads or relax resize/reencode workload after checking image-processing requirements.
4. If network/DNS-bound, increase threads gradually and deploy a local resolver.
5. If disk-bound or file-count-bound, prefer `webdataset` and larger shards.
6. Compare W&B or stats between runs; change one parameter at a time.

### Many failed shards in PySpark

1. Verify Java, PySpark, and worker package availability.
2. Reduce `subjob_size` to isolate failing batches.
3. Inspect stats/status for deterministic schema, HTTP, DNS, or object-store errors.
4. Use `max_shard_retry` for transient failures; if failures persist, fix root cause before increasing retries.
5. Rerun with the same output folder and stable shard sizing so completed shards are skipped by incremental mode.
