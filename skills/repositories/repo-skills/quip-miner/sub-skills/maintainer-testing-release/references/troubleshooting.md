# Maintainer Troubleshooting

## Hung Python process: get tracebacks

`SIGINT` only helps when the main thread is executing Python bytecode. For a process wedged in C, a lock, `join`, `wait`, or blocking syscall, pre-arm faulthandler and use SIGABRT:

```bash
PYTHONFAULTHANDLER=1 python <long-running-script>.py ...
# from another shell:
kill -ABRT <pid>
```

SIGABRT makes faulthandler dump every thread stack to stderr and then abort with exit 134. For non-fatal dumps, code can register SIGUSR1 with faulthandler, or use `py-spy dump --pid <pid>`.

Inspect process trees first:

```bash
ps -o pid,ppid,stat,command -p <pid>
pgrep -P <pid>
```

Stuck shutdowns often involve unjoined children or multiprocessing queue feeder threads.

## New threads introduced

Repo policy: new background work should be a multiprocessing process or asyncio task, not a new `threading.Thread`. Threads can starve CPU-bound siblings and previously stalled QPU stream pumping. Locks are fine; new thread workers are not.

Third-party/internal threads may exist; document exceptions inline when they are relevant and unavoidable.

## Inline sampling lint fails

The code reintroduced a deleted inline sampling path. Do not just rename the symbol to bypass the lint. Route the work through stream-driver subprocesses and the shared-memory ring.

## Optional backend test skips

If CuPy, Metal, Modal, or QPU credentials/hardware are unavailable, record a skip or backend block explicitly. Do not mark a CUDA/QPU runtime claim verified from CPU-only tests.

## PyInstaller selftest fails

Likely missing package data such as scalecodec type-registry presets or topology assets. Inspect the frozen bundle data collection and rerun `quip-miner selftest` after fixing packaging hooks/manifests.

## QPU benchmark pressure

Never run QPU benchmarks in the background from a maintenance task. Provide the command and let the operator execute it with explicit cost/runtime awareness.
