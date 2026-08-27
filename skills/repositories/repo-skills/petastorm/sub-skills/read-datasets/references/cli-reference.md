# CLI Reference

## Purpose

Read this when you need the command-line interface for reader benchmarking.
The package currently exposes one read-side console command in this route.

## `petastorm-throughput.py`

### Shape

```text
petastorm-throughput.py DATASET_PATH [options]
```

### Verified options

| Option | Meaning |
| --- | --- |
| `dataset_path` | Petastorm dataset path or URL to benchmark |
| `--field-regex FIELD_REGEX [FIELD_REGEX ...]` | Restrict benchmarked columns to matching fields |
| `-w, --workers-count` | Number of reader workers |
| `-p, --pool-type {thread,process,dummy}` | Worker pool type |
| `-m, --warmup-cycles` | Warmup iterations before timing |
| `-n, --measure-cycles` | Measurement iterations |
| `--profile-threads` | Print thread profiling output if the pool supports it |
| `-d, --read-method {python,tf}` | Benchmark the pure Python or TensorFlow reading path |
| `-q, --shuffling-queue-size` | Size of the shuffling queue used for decorrelation |
| `--min-after-dequeue` | Minimum queue fill level before dequeue |
| `-v` | Info logging |
| `-vv` | Debug logging |

### Behavior notes

- `--read-method python` measures `next(reader)` style reads.
- `--read-method tf` creates a small TensorFlow graph and measures the TensorFlow read path.
- If `--min-after-dequeue` is not supplied, the CLI derives it from the queue size.
- The command is intended for read-path timing and memory footprint checks, not for correctness testing.

### Example

```bash
petastorm-throughput.py file:///tmp/petastorm-dataset \
  --field-regex '^id$' \
  -w 1 -p dummy -m 5 -n 10 -d python
```
