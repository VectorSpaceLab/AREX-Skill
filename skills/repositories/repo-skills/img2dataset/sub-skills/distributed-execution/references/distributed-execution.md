# Distributed execution for img2dataset

This reference helps choose and operate img2dataset's execution backends. It assumes the caller already knows the input table and desired output format; use sibling sub-skills for schema, output layout, image processing, or downloader safety flags.

## Mode decision tree

1. **Start with `multiprocessing` on one machine** when the dataset fits a single host's CPU, disk, and network budget. It is the default and has the most direct retry behavior.
2. **Use `pyspark`** when a Spark cluster is available or when a local Spark session is required for parity with a cluster workflow. PySpark is the main multi-node path described by the project documentation.
3. **Use `ray`** only when Ray is installed and initialized for the target cluster. The Ray path is optional and needs preflight checks because missing Ray can make the selected distributor do no useful work.

The only valid `distributor` values are:

| Value | Best use | Main prerequisites | Important behavior |
| --- | --- | --- | --- |
| `multiprocessing` | Single host, default production baseline | Python package and local resources | Creates a spawn process pool with `processes_count`; applies `max_shard_retry` after the first pass. |
| `pyspark` | Local Spark or multi-node Spark cluster | `pyspark`, Java, compatible Python/package on workers | Uses an active `SparkSession` if one exists; otherwise creates `local[processes_count]`; batches reader shards by `subjob_size`; applies `max_shard_retry`. |
| `ray` | Existing Ray cluster or Ray-managed local execution | `ray`, initialized cluster/session for non-local jobs | Imports Ray only if installed; current implementation launches one remote task per shard and does not apply `subjob_size` or `max_shard_retry`. |

## Preflight before expensive runs

Run the checker when a user asks for PySpark, Ray, TFRecord, W&B, or non-local filesystems:

```bash
python scripts/check_distributed_backends.py --json
```

For tiny local backend smokes without any image download:

```bash
python scripts/check_distributed_backends.py --spark-smoke --ray-smoke --tfrecord-smoke
```

Generation-time backend evidence showed that PySpark local mode can work with Java 17, Ray works with current `ray.init(...)` APIs, and TensorFlow CPU can write a tiny TFRecord. Treat those as dependency patterns to reproduce, not as guaranteed availability in the user's runtime.

## Multiprocessing mode

Use this as the default baseline:

```bash
img2dataset \
  --url_list urls.parquet \
  --input_format parquet \
  --url_col URL \
  --caption_col TEXT \
  --output_folder out-webdataset \
  --output_format webdataset \
  --distributor multiprocessing \
  --processes_count 16 \
  --thread_count 64 \
  --number_sample_per_shard 10000 \
  --max_shard_retry 1
```

Operational notes:

- `processes_count` controls the local process pool size. Start near the number of CPU cores when resizing; reduce if disk or memory is saturated.
- `thread_count` controls concurrent downloads inside each shard-processing worker. Increase until network is saturated or CPU/DNS failures rise.
- The pool uses spawn semantics and recycles workers after a small number of tasks, so avoid relying on fork-only global state.
- Multiprocessing reports failed shards and retries them at the end up to `max_shard_retry` times.

## PySpark local and cluster mode

### SparkSession ownership

The PySpark distributor obtains a Spark session as follows:

1. For Spark 3+, it first checks `SparkSession.getActiveSession()`.
2. For older Spark, it checks the instantiated session.
3. If no session exists, it creates one with driver memory `16G`, master `local[processes_count]`, and app name `spark-stats`; this auto-created session is stopped when the distributor exits.
4. If a session already exists, img2dataset uses it and does **not** stop it. The caller owns lifecycle, master URL, worker package distribution, memory, and executor settings.

### Dry-run-first PySpark template

Use the bundled template to avoid hard-coded paths and to keep imports deferred until needed:

```bash
python scripts/pyspark_download_template.py \
  --url-list urls.parquet \
  --output-folder out-webdataset \
  --input-format parquet \
  --url-col URL \
  --caption-col TEXT \
  --image-size 256 \
  --processes-count 16 \
  --thread-count 32 \
  --subjob-size 1000 \
  --master 'local[16]' \
  --dry-run
```

After reviewing the dry-run plan:

```bash
python scripts/pyspark_download_template.py \
  --url-list urls.parquet \
  --output-folder out-webdataset \
  --input-format parquet \
  --url-col URL \
  --caption-col TEXT \
  --image-size 256 \
  --processes-count 16 \
  --thread-count 32 \
  --subjob-size 1000 \
  --master 'local[16]' \
  --run
```

For a cluster, replace the master value with a Spark URL such as `spark://master-node:7077` and make sure every worker can import img2dataset and its dependencies. Common deployment patterns include installing the same environment on all nodes or setting `PYSPARK_PYTHON` to a packaged Python executable that workers can access.

### What `subjob_size` really controls

The public API describes `subjob_size` as the size of a PySpark subjob. Source behavior batches the **reader shards** emitted by img2dataset and sends each batch to Spark via `parallelize(batch, len(batch))`. The approximate number of images in one Spark batch is:

```text
subjob_size * number_sample_per_shard
```

Practical tuning:

- Increase `subjob_size` when Spark scheduler overhead dominates and workers are idle.
- Decrease `subjob_size` when the driver takes too long preparing batches, object-store temporary files are slow, or failures are hard to isolate.
- Keep `number_sample_per_shard` stable across restarts when using incremental output, otherwise shard completion detection becomes harder to reason about.

### PySpark cluster prerequisites

- Java runtime available on the driver and workers; OpenJDK 11 or 17 is a common choice.
- Compatible `pyspark` package on the driver.
- Network routes and Spark UI/driver ports open as required by the cluster.
- img2dataset and dependencies available on executors.
- Shared or remote storage for input, output, and temporary shard files when workers run on separate machines.
- A high-performance DNS resolver on each node for large internet URL lists.

## Ray mode

Ray is selected with `distributor="ray"`, but it should be guarded by checks:

```python
import ray
from img2dataset import download

ray.init(address="auto")  # or ray.init(num_cpus=8) for a small local run

download(
    url_list="urls.parquet",
    input_format="parquet",
    url_col="url",
    caption_col="caption",
    output_folder="out-webdataset",
    output_format="webdataset",
    distributor="ray",
    processes_count=1,
    thread_count=32,
    number_sample_per_shard=10000,
)
```

Ray gotchas:

- Do not use deprecated `local_mode=True` guidance with recent Ray versions.
- For a cluster, call `ray.init(address="auto")` or the cluster-specific address before `download(...)`.
- The current Ray distributor ignores `subjob_size` and `max_shard_retry`; it launches one remote task per reader shard and waits for the returned object refs.
- If Ray is not importable, the package's fallback Ray distributor returns without running useful work. Always preflight Ray before using this mode.

## Shard retry behavior

`max_shard_retry` is an end-of-run shard retry loop. The distributor collects shards whose downloader returned `False`, prints retry progress, and calls the same shard runner again. If shards still fail after the configured attempts, img2dataset prints that the command can be restarted to retry again.

Use it this way:

- `max_shard_retry=0`: no end-of-run shard retry; rely on per-image retries and future reruns.
- `max_shard_retry=1`: default; one extra pass over failed shards.
- Higher values: useful for transient network or object-store failures, but diagnose persistent DNS, SSL, disk, or schema problems instead of looping indefinitely.

For Ray, use output stats plus incremental reruns as the practical retry mechanism because the current Ray path does not run the shared shard retry loop.

## Observability hooks

- Each finished shard writes a `*_stats.json` file into the output folder. These files contain counts, successes, download failures, resize failures, duration, and status frequencies.
- The logger process aggregates stats and prints worker/total speed lines such as success ratio, failed-to-download ratio, failed-to-resize ratio, images/sec, and count.
- With `--enable_wandb=True`, the logger initializes W&B with `anonymous="allow"`, logs total/worker metrics, and publishes a status table of frequent error statuses.
