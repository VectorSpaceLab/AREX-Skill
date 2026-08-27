# Profiling and debugging

Use these patterns when Jittor is importable but behavior is unclear: wrong traceback, NaN/Inf, memory growth, or performance measurements that look too good or too bad.

## Timing rules

Jittor is asynchronous and JIT-based, so performance timing must separate compilation from execution.

### Correct timing checklist

1. Use a small warmup loop first.
2. Synchronize after the warmup.
3. Synchronize every measured iteration or every result you read.
4. Synchronize again before stopping the timer.
5. Do not include the first JIT compile in the measured window.

### Minimal timing pattern

```python
import time
import jittor as jt

x = jt.random((8, 256))
w = jt.random((256, 256))

jt.sync_all(True)
for _ in range(2):
    y = jt.matmul(x, w)
    y.sync()
jt.sync_all(True)

start = time.perf_counter()
for _ in range(5):
    y = jt.matmul(x, w)
    y.sync()
jt.sync_all(True)
elapsed = time.perf_counter() - start
print(elapsed)
```

## Profiling scope

`jt.profile_scope` is the safest built-in profiler entry point for short, synchronized probes.

```python
import jittor as jt

a = jt.rand(1000, 1000)
b = jt.rand(1000, 1000)
jt.sync_all()

with jt.profile_scope(2, 5, profiler_record_peek=1) as rep:
    jt.matmul(a, b).sync()

print(rep[-1])
```

Good uses:

- check whether a repeated op regressed after a backend change
- compare two alternative `jt.flag_scope(...)` settings
- confirm that a suspected bottleneck is actually the hot path

Avoid:

- wrapping a huge training loop
- profiling without synchronization
- treating the first compile as part of the runtime number

## Memory debugging

When memory grows or a run dies with OOM, first decide whether the failure is:

- a single-step memory blow-up, or
- a leak-like growth across iterations.

### Helpful tools

- `jt.display_memory_info()` — current memory and graph pressure summary.
- `jt.display_max_memory_info()` — report the peak memory picture.
- `jt.get_max_memory_treemap()` — tree view of the peak allocation path.
- `jt.gc()` — force cleanup between iterations when you are isolating a reproducer.
- `jt.sync_all()` — ensure all pending work is visible before reading memory state.

### Useful memory flags

- `profile_memory_enable=1` — enable the memory profiler.
- `trace_py_var=3` — enrich stack provenance for memory attribution.
- `JT_SAVE_MEM=1` — enable the memory-saving swap workflow when appropriate.
- `cpu_mem_limit` / `device_mem_limit` — bound memory usage for swap-based runs.
- `jt.cudnn.set_max_workspace_ratio(0.0)` — reduce CUDA convolution workspace pressure when workspace growth is the problem.

### Memory triage pattern

```python
import jittor as jt

with jt.flag_scope(trace_py_var=3, profile_memory_enable=1):
    y = jt.random((1, 3, 224, 224))
    # run the smallest reproducer you can
    jt.display_memory_info()
```

## Lazy execution and trace quality

Lazy execution improves throughput but can blur the place where a failure originated.

### Better traceback localization

- Set `lazy_execution=0` or `jt.flags.lazy_execution = 0`.
- Raise `trace_py_var` to `3` for the richest trace context.
- Reproduce with a tiny input and as few layers or ops as possible.

### When to use eager mode

- the traceback points at the wrong line
- a bad op only appears after several unrelated ops
- the failure disappears when you inspect intermediate values

### Debugging pattern

```python
import jittor as jt
jt.flags.lazy_execution = 0
with jt.flag_scope(trace_py_var=3):
    # tiny reproducer
    pass
```

If the trace is still unclear, add `debug=1` or `gdb_attach=1` for a local-only reproducer.

## NaN/Inf localization

If the run becomes numerically unstable:

- set `JT_CHECK_NAN=1`
- set `trace_py_var=3`
- rerun the smallest possible input

That mode is slow and may recompile, so use it only on a narrow reproducer.

## Performance health checks

A healthy performance workflow usually looks like this:

- import once
- warm up once
- synchronize before and after the measured block
- compare against the same batch shape and the same backend flag set
- confirm the output is still numerically sensible

If a timing result looks suspiciously fast, check whether you accidentally timed queued work without synchronization.

## Practical debug order

1. Confirm the import.
2. Run a tiny synchronized CPU smoke.
3. Disable lazy execution if the traceback is misleading.
4. Add `trace_py_var=3`.
5. Add memory or NaN/Inf guards if the failure is still unclear.
6. Only then compare alternate backend or performance settings.
