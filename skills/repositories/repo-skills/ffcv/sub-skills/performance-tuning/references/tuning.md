# Cache, order, and loader tuning

This reference turns FFCV's cache and traversal implementation into bounded
configuration choices. Keep cache mode and traversal order as a pair: the
right choice depends on the dataset's relationship to RAM, the number of
processes sharing the file, and whether distributed sampling is required.

## Cache selection

### OS cache: `os_cache=True`

`Loader` selects `OSCacheManager` when `os_cache=True` (the default unless the
environment variable `FFCV_DEFAULT_CACHE_PROCESS` changes the default). Its
context opens a read-only `numpy.memmap` of the `.beton` file and the compiled
reader slices that mapping using the allocation pointer/size tables. The
operating system decides which pages remain resident.

Use it first when:

- the dataset fits in available memory and repeated epochs should become warm;
- multiple training processes on the same host can share the OS page cache; or
- distributed jobs need a supported order and shared file access is valuable.

Expect the first epoch to be slower while pages are fetched. A memmap is a
virtual mapping, not a promise that the complete file is resident; monitor
actual host memory and disk wait rather than assuming `os_cache=True` is free.

### Process cache: `os_cache=False`

`Loader` selects `ProcessCacheManager`, which maps every sample to the pages it
uses. At epoch start `ProcessCacheContext` derives the pages needed by each
batch, calls `compute_schedule`, allocates `num_slots * page_size` bytes, and
starts `ScheduleExecutor` page-reader threads. Pages can be prefetched up to
three batches before their first use (the schedule's fixed
`prefetch_ahead=3`), then released/reused according to page lifetime.

Use it when the dataset is larger than RAM or when whole-file OS caching would
compete with other workloads. It is not a full in-memory copy: its peak process
buffer is determined by page overlap in the epoch schedule. However, a bad
order can increase overlap and therefore the number of slots. The current
`ScheduleExecutor` default is 12 page-reader threads; this is separate from
`Loader.num_workers`, which configures compiler threads.

Process-cache setup can raise `MemoryError` while an `EpochIterator` enters its
memory context. Reduce page overlap by changing the order, reduce batch size,
or return to OS cache if the dataset actually fits and sharing is preferable.
Do not hide the error by silently switching order: record the change because it
changes sampling behavior.

## OrderOption tradeoffs

### `SEQUENTIAL`

- Returns the loader's indices in order in non-distributed mode.
- Uses `torch.utils.data.DistributedSampler(shuffle=False, drop_last=False)`
  when `distributed=True`, and calls `set_epoch(epoch)`.
- Is the lowest-randomness baseline and often minimizes storage movement.
- Is useful for isolating decoder/transform or model bottlenecks.

Use it to establish a deterministic I/O baseline, for validation-like passes,
or when distributed quasi-random sampling is unavailable.

### `RANDOM`

- In a non-distributed loader, creates a NumPy permutation of `indices` using a
  generator seeded with `seed + epoch` (or an unseeded generator only if the
  loader supplied no seed).
- In distributed mode, uses PyTorch `DistributedSampler(shuffle=True,
  seed=seed, drop_last=False)` and calls `set_epoch(epoch)`.
- Provides the strongest ordinary shuffle semantics among the built-in orders,
  but can make a process-cache schedule touch pages with little locality. The
  tuning guide warns that random ordering is a poor fit when the dataset cannot
  be cached; measure before using it at that scale.

If `distributed=True`, `order=OrderOption.RANDOM`, and no seed was given,
`Loader` prints a warning and sets the seed to `0` to match the PyTorch sampler.
Do not rely on an implicitly generated seed for reproducible experiments.

### `QUASI_RANDOM`

- Uses the reader's `page_to_samples` map to group samples by storage page.
- Shuffles samples inside pages, randomly chooses among a bounded active page
  set, and uses a buffer of `2 * batch_size` active pages in the generated
  order.
- Is designed to retain useful randomness while reducing page reads, and is
  especially useful with `os_cache=False` when a dataset is larger than RAM.
- Raises `ValueError` when the reader has no page-to-sample mapping that would
  benefit from this order.
- Raises `NotImplementedError("distributed Not implemented yet for
  QuasiRandom")` when `distributed=True`. This is a hard unsupported case, not
  a performance warning; choose `SEQUENTIAL` or `RANDOM` for distributed jobs.

The current implementation also prepares arrays sized by the largest page and
highest page id. Treat its setup memory as part of the budget, especially for
unusual files or heavily filtered `indices`.

## Distributed configurations

For a distributed loader, use one of these explicit combinations:

```python
from ffcv.loader import Loader, OrderOption

# Supported deterministic baseline.
loader = Loader(
    "train.beton", batch_size=64, distributed=True,
    os_cache=True, order=OrderOption.SEQUENTIAL, seed=0,
)

# Supported shuffled baseline; seed all ranks consistently.
loader = Loader(
    "train.beton", batch_size=64, distributed=True,
    os_cache=True, order=OrderOption.RANDOM, seed=0,
)
```

If the dataset is larger than RAM, repeat the supported distributed baseline
with `os_cache=False` and compare storage wait/throughput. Do **not** substitute
`QUASI_RANDOM`: the constructor rejects it before iteration. For non-distributed
large datasets, the difficult-case configuration is:

```python
loader = Loader(
    "large.beton", batch_size=64, distributed=False,
    os_cache=False, order=OrderOption.QUASI_RANDOM, seed=0,
)
```

Keep `indices` identical across comparisons. The traversal tests establish that
sequential/random distributed runs preserve the selected index set; the skipped
quasi-random distributed tests are evidence of the unsupported boundary rather
than passing coverage.

## `num_workers`, `batches_ahead`, and `recompile`

### `num_workers`

`Loader` treats `num_workers < 1` as the number of CPUs in the current
`sched_getaffinity(0)` set. It calls `Compiler.set_num_threads` during
construction and again at iteration, setting both Numba and PyTorch thread
counts. Start with physical cores available to the loader, not automatically
with every hyperthread. If all CPUs are at 100% while the GPU waits, try fewer
workers if scheduling/oversubscription is visible; if CPU capacity is idle,
try a larger value one step at a time.

This is not a multiprocessing worker count. The FFCV epoch iterator is a
thread-based producer, and process-cache page loading currently has its own
12-thread `ScheduleExecutor` default.

### `batches_ahead`

The default is `3`. `EpochIterator` uses it for a bounded output queue and
allocates rotating operation/shared buffers and CUDA streams for
`batches_ahead + 2` batch slots. Larger values may hide disk/transform latency
but increase host/device memory and can make a bad pipeline harder to diagnose.
Lower it when memory pressure, allocator failures, or excessive queued work is
observed. Increase it only when the consumer repeatedly waits and the memory
budget is explicit. Keep batch size fixed while comparing this parameter.

The process-cache schedule's page prefetch look-ahead is independently fixed at
three batches; changing `batches_ahead` is not a direct change to that constant.
It changes downstream queue/ring-buffer capacity, not the process-cache page
schedule or the grouping of samples into batches.

### `recompile`

`Loader` generates the graph code at construction and compiles it for the
first iteration. With `recompile=False`, later epochs reuse that generated
code. With `recompile=True`, `__iter__` regenerates it every epoch; the loader
docstring says this is needed when an augmentation implementation is expected
to change during training. Keep it false for ordinary fixed pipelines. If an
experiment changes transform state, enable it deliberately and include compile
time in the epoch accounting or warm up before measuring steady state.

## Compiler behavior

`Compiler.set_enabled(True)` is the package default. `Compiler.compile`:

- returns the original Python function when disabled;
- otherwise applies `numba.njit` with `fastmath=True`, `nogil=True`, and
  `error_model='numpy'`;
- enables Numba's `parallel` mode only when the function has `is_parallel` and
  `Compiler.num_threads > 1`;
- exposes `prange` through `get_iterator` only when the configured thread count
  is greater than one; otherwise it returns `range`.

The first call can include JIT compilation. Separate first-call cost from
steady-state throughput, and never claim that disabling the compiler is a
normal optimization. The memory-reader tests include both uncompiled reads
and a compiled many-sample case, so those are suitable small checks when
changing compiler/thread settings.

## Evidence anchors

- `ffcv/memory_managers/base.py`, `common.py`, `os_cache.py`, and
  `process_cache/{context,manager,page_reader,schedule}.py`: allocation maps,
  memmap reader, scheduled process pages, fixed three-batch page prefetch, and
  page-reader implementation.
- `ffcv/loader/loader.py` and `ffcv/loader/epoch_iterator.py`: defaults, order
  map, seed/distributed handling, compiler-thread setup, recompile, queue,
  ring-buffer, and CUDA stream behavior.
- `ffcv/traversal_order/{base,sequential,random,quasi_random}.py`: exact order
  generation and distributed/quasi-random rejection.
- `ffcv/pipeline/compiler.py`: thread and Numba/PyTorch compiler behavior.
- `docs/performance_guide.rst`, `docs/parameter_tuning.rst`, and
  `docs/bottleneck_doctor.rst`: resource-oriented recommendations.
- `tests/test_traversal_orders.py`, `tests/test_memory_reader.py`, and
  `tests/test_memory_allocation.py`: ordering/distributed assertions and
  compiled/uncompiled memory-reader/allocation ground truth.
