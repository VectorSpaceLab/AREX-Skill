---
name: performance-tuning
description: "Tune FFCV cache, traversal, loader concurrency, compilation, and
  measurement choices; diagnose RAM, disk, CPU, and GPU bottlenecks without
  unsafe benchmark-scale execution."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# FFCV performance tuning

Use this sub-skill when an FFCV `Loader` is correct but throughput, latency,
resource use, or distributed behavior needs diagnosis. It owns cache selection,
`OrderOption` selection, loader concurrency/prefetch knobs, compiler behavior,
small measurements, and resource-bottleneck recovery. It does **not** own
writer format design, decoder/transform semantics, or end-to-end model tuning.

## Fast routing

1. Establish a correct baseline on a tiny or already-available `.beton` dataset.
   Record dataset size, available RAM, storage type, CPU affinity, GPU count,
   batch size, pipeline, and whether the loader is distributed.
2. Choose cache and order together using [tuning.md](references/tuning.md).
   Do not choose `QUASI_RANDOM` before checking `distributed`.
3. Change one of `num_workers`, `batches_ahead`, or `recompile` at a time. Keep
   the same seed, batch size, pipeline, and measurement window.
4. Diagnose the scarce resource with [troubleshooting.md](references/troubleshooting.md).
5. Measure only after the hypothesis is explicit. Start with `python -m
   ffcv.benchmarks --help`; the safe CLI procedure is in
   [benchmarking.md](references/benchmarking.md). Never make the full benchmark
   matrix or a long training run the default validation path.

## Decision rules

| Situation | Starting point | Guardrail |
|---|---|---|
| Dataset fits comfortably in RAM, or several processes share it | `os_cache=True` with `RANDOM` or `QUASI_RANDOM` | The first epoch can be slower while the OS warms its cache. |
| Dataset is larger than RAM and randomness need not be perfectly uniform | `os_cache=False` plus `OrderOption.QUASI_RANDOM` | This combination is specifically for process-level page reuse; it is unavailable with `distributed=True`. |
| Dataset is larger than RAM and exact distributed sampling is required | `os_cache=False` with `SEQUENTIAL` or `RANDOM`, `distributed=True` | `QUASI_RANDOM` raises `NotImplementedError` in distributed mode. Test the I/O cost of `RANDOM` before adopting it. |
| Dataset order must be repeatable | `SEQUENTIAL`, or seeded `RANDOM` | In non-distributed mode random order uses `seed + epoch`; in distributed mode PyTorch `DistributedSampler` is used. |
| CPU is saturated and the GPU is idle | Start at the physical-core count or fewer for `num_workers`; prefer FFCV JIT transforms | `num_workers` controls compiler thread counts, not a pool of Python worker processes. |
| Prefetch causes memory pressure or no overlap benefit | Lower `batches_ahead` from its default of 3 | It sizes the output queue/ring buffers; lowering trades overlap for RAM/GPU headroom. |
| An augmentation implementation changes between epochs | `recompile=True` | It recompiles generated pipeline code each epoch; otherwise keep the default `False`. |

These are starting hypotheses, not throughput guarantees. Validate on the
actual storage and pipeline. `os_cache=True` uses a read-only `numpy.memmap`
backed by the operating system; `os_cache=False` creates a process-level page
schedule for each epoch and prefetches pages into reusable slots. The process
cache is not a second full-dataset cache.

## Loader knobs that interact

- `num_workers=-1` resolves to the process CPU affinity. A positive value is
  passed to `Compiler.set_num_threads`, which sets both Numba and PyTorch thread
  counts. FFCV is thread-based; do not interpret it as PyTorch's process worker
  count. More threads can hurt when JIT operations are already efficient.
- `batches_ahead` defaults to `3`. `EpochIterator` uses it for the bounded
  result queue, CUDA stream count (`batches_ahead + 2`), and rotating operation
  buffers. Increase only when the consumer is waiting for data and memory is
  available; decrease when host/device buffers or latency variance is the
  problem.
- `recompile=False` compiles the graph when the loader is constructed and on
  the first iteration. With `True`, `Loader.__iter__` regenerates code each
  epoch. Use it only when a stateful/dynamic augmentation really changes its
  implementation or generated code.
- `seed` is part of the reproducibility contract. With distributed random order
  and no seed, `Loader` warns and sets the seed to `0` to match PyTorch's
  sampler. For other missing-seed cases it generates a seed, so record the
  resulting loader configuration if comparing runs.
- `Compiler` is enabled by default. When enabled, `Compiler.compile` wraps
  functions with Numba `njit(fastmath=True, nogil=True, error_model='numpy')`;
  parallel functions use `prange` only when they advertise `is_parallel` and
  the configured thread count is greater than one. Disabling compilation is a
  diagnostic/benchmark comparison, not a normal performance fix.

## Safe operating procedure

1. Verify the loader configuration and that all requested samples are seen.
   Do not use throughput changes to excuse ordering or distributed correctness
   failures.
2. Capture one baseline with a bounded warm-up and a small number of timed
   iterations. Avoid comparing a cold OS cache to a warm process cache without
   labeling the state.
3. Look for the symptom class: disk wait/GPU idle, CPU saturation, host RAM
   growth, GPU memory pressure, or model-side GPU saturation.
4. Apply one reversible change, rerun the same bounded measurement, and retain
   the configuration plus result. If the change does not target the scarce
   resource, revert it.
5. For a dataset larger than RAM, explicitly try the difficult-case baseline:
   `os_cache=False`, `order=OrderOption.QUASI_RANDOM`, `distributed=False`.
   For distributed training, explicitly use `SEQUENTIAL` or `RANDOM` instead.

## Verification boundary

The repository evidence supports CPU smoke checks, memory-reader/allocation
checks, traversal-order tests, and a tiny CUDA allocation probe. Full benchmark
matrices, ImageNet benchmark reproduction, and long training are excluded from
routine verification. See the references for source anchors and hard cases.
