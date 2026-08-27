# Safe FFCV micro-benchmarking

The bundled benchmark command is a measurement aid, not a default smoke test.
Its suites construct temporary datasets and can run many configurations. The
repository's benchmark documentation reports large ImageNet and end-to-end
training experiments; those are historical results, not a local verification
requirement for this skill.

## Start with help

Always inspect the installed command before running a suite:

```bash
python -m ffcv.benchmarks --help
```

The CLI exposes:

- `--runs` / `-n`: median timing repetitions, default `3`;
- `--warm-up` / `-w`: warm-up executions per configuration, default `1`;
- `--pattern` / `-p`: glob-style benchmark-suite name filter, default `*`;
- `--output` / `-o`: optional CSV destination instead of tables on stdout.

The decorator registers a Cartesian product of every parameter list on each
suite. Therefore `-n 1 -w 0` reduces repetition cost but does **not** shrink a
suite's internal dataset or parameter matrix. A narrow pattern is safer than
the default wildcard, but it is still an optional experiment that may allocate
or generate data.

## Bounded invocation guidance

After `--help`, select exactly one suite name shown by the installed package and
run one low-repetition pattern, for example:

```bash
python -m ffcv.benchmarks \
  --pattern 'JPEGDecodeBenchmark' \
  --runs 1 --warm-up 0
```

Use a pattern that matches the actual suite name; do not assume a name after a
package upgrade. The current source includes `JPEGDecodeBenchmark`,
`ImageReadBench`, and `MemoryReadBytesBench`. The JPEG suite is a relatively
narrow diagnostic for compiled JPEG decode, but it still evaluates its declared
width/quality product. The image and memory suites construct larger matrices
and should not be selected casually.

Write a CSV only when the output is needed for later comparison:

```bash
python -m ffcv.benchmarks \
  --pattern 'JPEGDecodeBenchmark' \
  --runs 1 --warm-up 0 --output ./ffcv-jpeg-smoke.csv
```

Do not run `python -m ffcv.benchmarks` with its default `--pattern '*'` as a
routine check. Do not use benchmark-scale dataset generation, full matrices,
ImageNet downloads, or long training to validate a generated repo skill. If a
suite is still too expensive, stop; use a tiny synthetic Loader test with a
fixed `.beton` fixture instead.

## Measurement protocol

1. Record commit/package version, CPU affinity, GPU visibility, storage path,
   dataset size, `os_cache`, order, distributed flag, seed, batch size,
   `num_workers`, `batches_ahead`, and `recompile`.
2. Keep the fixture and pipeline constant. Change one tuning variable per
   comparison.
3. Separate cold and warm states. `OSCacheManager` uses a read-only memmap and
   can become faster after the OS has populated pages; process-cache schedules
   and fills its own page slots at epoch entry.
4. Warm up at least once for code that may be JIT compiled. The CLI's
   `--warm-up` controls suite repetitions, but a generated Loader pipeline may
   also compile on first use; report which costs were included.
5. Use a median over a small bounded number of runs, as `run_all` does. Report
   samples/second only with the same `n`, batch, and pipeline; a faster number
   with fewer decoded samples is not an apples-to-apples result.
6. Measure end-to-end batch consumption as well as any isolated decoder/memory
   test. A memory-reader result cannot prove that a model is input-bound.
7. Stop on OOM, runaway temporary files, excessive disk pressure, or a shared
   GPU conflict. Preserve the last known configuration and classify the
   blocker rather than retrying a larger benchmark.

## Interpreting the bundled runner

`ffcv/benchmarks/__main__.py` parses arguments, calls `run_all`, prints a table,
or writes a CSV. `ffcv/benchmarks/decorator.py` filters registered suite names
with `PurePath.match(pattern)`, expands each decorator's Cartesian product,
runs warm-ups, takes `numpy.median`, and derives throughput from an `n` argument.
This explains why:

- a narrow pattern is essential;
- low `-n`/`-w` bounds timing repetitions but not fixture construction;
- suites without a meaningful common `n` should not be compared by displayed
  throughput alone; and
- a CLI result is not a Loader correctness test.

The benchmark suite source uses temporary files and fixed synthetic sizes. It
is useful for a focused regression hypothesis (for example compiled versus
uncompiled JPEG decode), but the full matrix is excluded from the installed
facts for this skill: CPU smoke passed, CUDA tiny allocation passed, and full
benchmark matrices/long training were not run.

## Safer alternative: tiny synthetic comparison

For a tuning decision, prefer a small existing `.beton` fixture or a temporary
indexed dataset with enough samples for a few batches. Compare two Loader
configurations with identical `seed`, `indices`, pipeline, and batch size. Check
that the consumed index set is unchanged before reading timing. Use a short
bounded loop and delete the temporary file in `finally`/a context manager.

For a CPU-only measurement, hide or reserve shared GPUs rather than treating
CUDA availability as proof of a GPU result. A CUDA tiny-allocation smoke pass
only proves that the environment can make that allocation; it does not validate
throughput, multi-GPU behavior, or the full benchmark suites.

## Evidence anchors

- `ffcv/benchmarks/__main__.py`: CLI flags, defaults, stdout/CSV behavior.
- `ffcv/benchmarks/decorator.py`: suite filtering, Cartesian expansion,
  warm-up, median, and throughput calculation.
- `ffcv/benchmarks/benchmark.py` and `ffcv/benchmarks/suites/*.py`: lifecycle,
  temporary-fixture construction, and declared matrix sizes.
- `docs/benchmarks.rst`: scope and hardware-bound ImageNet/data-loading and
  training reports; it is not a local smoke-test recipe.
- `docs/performance_guide.rst`: links the performance, tuning, and bottleneck
  guidance used to choose a focused hypothesis.
