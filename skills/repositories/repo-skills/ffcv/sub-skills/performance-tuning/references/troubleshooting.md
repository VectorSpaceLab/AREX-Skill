# Performance troubleshooting

Diagnose the scarce resource before changing knobs. FFCV performance changes
can trade disk traffic for RAM, CPU work for GPU work, or overlap for memory;
there is no universally fastest setting.

## Symptom matrix

| Observation | Confirm with | First reversible action | Avoid |
|---|---|---|---|
| GPU is idle while storage is busy or batches arrive late | Disk wait/throughput, loader-only timing, and cold/warm distinction | If the dataset fits/shared, try `os_cache=True`; if it does not, try `os_cache=False` plus non-distributed `QUASI_RANDOM` | Running full benchmark matrices before confirming the loader is the bottleneck |
| Dataset larger than RAM causes host memory pressure or OOM | Dataset/file size versus available RAM; process RSS and the failing epoch-entry allocation | Use `os_cache=False`; for a non-distributed randomized loader use `QUASI_RANDOM`; lower batch size if the process schedule still needs too many slots | `RANDOM` as the first large-dataset choice; assuming a memmap means all data is resident |
| Distributed loader rejects startup with quasi-random | `distributed=True` and `order=OrderOption.QUASI_RANDOM` | Use `SEQUENTIAL` or `RANDOM`; seed all ranks consistently | Retrying the same unsupported combination or treating it as a transient I/O error |
| CPU cores are saturated and GPU is waiting | CPU utilization, compiler/transform timing, and affinity | Prefer built-in JIT transforms; try physical-core count or one lower `num_workers`; move suitable preprocessing to CPU only if it reduces GPU contention | Increasing workers blindly; confusing FFCV threads with process workers |
| CPU is mostly idle but batches still starve the GPU | Loader-only timing and per-stage/profile evidence | Increase `num_workers` one step, then `batches_ahead` one step if memory allows; check disk/cache mode first | Raising both knobs together or blaming the GPU without a data-path measurement |
| Host RAM grows or allocation fails after increasing prefetch | RSS, `batches_ahead`, batch size, process-cache slot count, and graph buffers | Reduce `batches_ahead` and/or batch size; use OS cache only when its sharing/fit assumptions hold | Treating `batches_ahead` as a free latency knob |
| GPU memory pressure or CUDA allocation failure appears | GPU memory before/after iterator creation; batch slot count | Lower `batches_ahead` (which creates `batches_ahead + 2` CUDA/buffer slots), lower batch size, and reserve the device | Claiming that CPU smoke or a tiny allocation validates this configuration |
| First iteration/epoch is much slower | JIT compilation and cold OS-cache state | Warm up separately; report cold and steady-state numbers | Averaging compilation/cold-cache startup into a steady-state claim without labeling it |
| Changing an augmentation between epochs has no effect | Whether generated code was rebuilt; `recompile` setting | Set `recompile=True` only for the dynamic implementation and account for compile cost | Leaving recompilation on for every fixed pipeline |
| CPU utilization is high but throughput does not improve with threads | `Compiler.num_threads`, Numba/PyTorch thread pools, transform type, and storage wait | Reduce `num_workers` to remove oversubscription; keep JIT compiler enabled; compare one variable | Assuming more threads always improve a thread-based pipeline |
| Random configuration is fast on a small fixture but stalls at scale | Fixture/file size, page locality, and process-cache slot schedule | Retest large-file behavior; choose `os_cache=False` + quasi-random when non-distributed and randomness tolerance allows | Extrapolating RAM-cached small-fixture results to a file larger than RAM |

## Failure recovery

### `QUASI_RANDOM` fails in distributed mode

This is expected from `QuasiRandom.__init__`, which raises
`NotImplementedError` when `loader.distributed` is true. Change the order to
`SEQUENTIAL` or `RANDOM`; do not catch and downgrade the exception silently.
Keep `os_cache` as a separate variable in the comparison. If the job needs a
large-dataset distributed configuration, measure process caching with a
supported order rather than pretending quasi-random semantics are present.

### Process-cache epoch entry raises `MemoryError`

`EpochIterator` enters the process cache before starting its producer thread.
The context has already computed page overlap and attempted to allocate its
slot buffer. Reduce the schedule's demand by using a more locality-friendly
order, smaller batches, or a narrower index set. Lowering `batches_ahead` can
reduce downstream buffers, but the process schedule's own page prefetch constant
is fixed at three, so do not promise that it alone fixes the allocation. If the
dataset fits in RAM, compare with `os_cache=True` and document the tradeoff.

### Results are not reproducible

Check `seed`, `distributed`, `indices`, `drop_last`, and epoch number. For
non-distributed `RANDOM`, the order generator uses `seed + epoch`. For
`SEQUENTIAL` and `RANDOM` distributed orders, PyTorch's `DistributedSampler`
receives the seed and is advanced with `set_epoch`. If a distributed random
loader was created without a seed, the loader warns and sets seed `0`; record
that explicit result in experiment metadata. Never compare two runs with
implicit randomly generated seeds as if they were identical.

### More `num_workers` makes the run slower

`Loader` sets Numba and PyTorch thread counts from `num_workers`, and the epoch
iterator sets them again in its producer thread. JIT transforms may already
parallelize efficiently, so additional threads can introduce scheduling and
cache contention. Use CPU affinity rather than host-wide core count, compare
physical-core-sized values, and inspect whether storage—not CPU—is the actual
wait source. Remember that process-cache page readers use a separate fixed
12-thread executor in the current implementation.

### `recompile=True` appears to erase gains

This setting calls `generate_code()` at every `__iter__` when the code exists.
It is correct only for a pipeline whose implementation changes during training.
Turn it off for a fixed graph, warm up the first iteration, and report compile
cost separately. If a dynamic transform still does not change, verify that the
changed object actually participates in graph code generation; this skill does
not redesign custom operations.

### Benchmark command is too expensive

Stop the command rather than increasing resources. First run:

```bash
python -m ffcv.benchmarks --help
```

Then select one actual suite with `--pattern`, `--runs 1`, and `--warm-up 0`.
Remember that the pattern narrows suites but not each suite's internal product
of configurations. Prefer a tiny synthetic Loader comparison if temporary
fixture creation or the declared matrix is still too large. Full benchmark
matrices and long training are outside this skill's verification boundary.

## Bottleneck-specific actions

### Disk / storage

- If the file fits in memory or is shared by concurrent processes, try OS-level
  caching and distinguish the cold first epoch from warm epochs.
- If the file does not fit, use process-level cache (`os_cache=False`) so FFCV
  schedules pages instead of asking the OS to retain the entire dataset.
- For a non-distributed randomized workload, use quasi-random order to reduce
  page reads while preserving useful randomness. It is not valid in distributed
  mode.
- For image workloads, storage/compute can also be changed upstream by storing
  appropriately resized images or choosing JPEG/raw/mixed storage. Treat that
  as a dataset-writing change and revalidate accuracy; do not use it as a
  loader-only knob.

### CPU

Use FFCV's pre-made JIT transforms where applicable. The bottleneck guide notes
that these use preallocated pinned memory and compiled/fused code. If a needed
operation is custom, profile it before changing cache mode. Reduce thread count
when all cores are busy but throughput is flat; increase only when CPU capacity
is available. `Compiler` is enabled by default and uses Numba `njit` settings
that are part of the normal path.

### GPU

FFCV transfers data asynchronously and uses CUDA streams in the epoch iterator,
so a GPU-side bottleneck is not automatically a loader defect. First determine
whether the GPU is saturated or waiting. If GPU compute is saturated, loader
knobs may not improve end-to-end throughput; if it waits for data, return to the
disk/CPU branches. If multiple models share a GPU, prefer one process per GPU
with threads as documented; reserve the device and beware concurrent BatchNorm
issues. Do not infer multi-GPU correctness from a tiny CUDA allocation smoke
pass.

## Minimal recovery record

For each attempted fix, record:

```text
symptom:
resource evidence:
file/dataset size and storage:
loader config (cache, order, distributed, seed, workers, batch, ahead, recompile):
change:
result (cold/warm, samples or batches, median):
correctness/index-set check:
remaining limitation:
```

## Evidence anchors

- `ffcv/memory_managers/*.py`: OS memmap versus scheduled process pages,
  allocation slots, page prefetch, and page-reader lifecycle.
- `ffcv/traversal_order/*.py` and `ffcv/loader/loader.py`: order semantics,
  seeds, distributed sampler behavior, and the explicit quasi-random error.
- `ffcv/loader/epoch_iterator.py`: memory-entry failure boundary, queue and
  ring-buffer sizing, async CUDA streams, and per-epoch pipeline execution.
- `ffcv/pipeline/compiler.py`: Numba/PyTorch thread settings and compilation.
- `docs/parameter_tuning.rst` and `docs/bottleneck_doctor.rst`: fit/RAM,
  multi-GPU, disk, CPU, and GPU recovery recommendations; `docs/performance_guide.rst`
  is the navigation entry for these guides.
- `ffcv/benchmarks/__main__.py`, `ffcv/benchmarks/decorator.py`, and
  `docs/benchmarks.rst`: bounded CLI behavior and the excluded benchmark-scale
  context.
- `tests/test_traversal_orders.py`: sequential/random coverage, selected-index
  preservation, and skipped distributed quasi-random cases.
- `tests/test_memory_reader.py` and `tests/test_memory_allocation.py`: OS-cache
  read correctness, compiled/uncompiled reads, and allocation-table checks.
