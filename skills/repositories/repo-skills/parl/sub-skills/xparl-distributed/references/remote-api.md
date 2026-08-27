# Remote API Reference

## Purpose

Read this when writing or reviewing Python code that uses PARL's distributed
actors. This reference covers `parl.connect`, `@parl.remote_class`,
`distributed_files`, futures, GPU requests, and serialization boundaries.

## Minimal blocking actor

```python
import parl

@parl.remote_class
class Actor:
    def add(self, a, b):
        return a + b

# Start or connect to a trusted xparl cluster before creating Actor().
parl.connect("localhost:6006")
actor = Actor()
assert actor.add(1, 2) == 3
```

Rules:

1. Decorate a **class**, not a function. Non-class decoration raises an
   assertion.
2. Call `parl.connect("HOST:PORT")` before creating any decorated object.
   Creating a remote object without a global client raises an assertion asking
   whether `parl.connect` was called.
3. Remote methods execute on worker processes. `print()` output and tracebacks
   are usually visible through xparl's log service, not the local terminal.

## `parl.connect(master_address, distributed_files=[])`

- `master_address` must have `host:port` format.
- `distributed_files` must be a list.
- The call creates one global client per process. If a new Python process uses
  the global client, PARL creates a new client for that process.
- The client verifies environment consistency with the master: PARL version and
  Python major/minor version must match.
- The client records a log-monitor URL for remote actor logs.

### File distribution defaults

When a client connects, PARL sends all `.py` files in the main script directory
(or the current directory in a notebook-style context) to remote jobs. Use
`distributed_files` for additional files or subdirectories.

```python
parl.connect(
    "localhost:6006",
    distributed_files=["./policy/*.py", "./policy/*.ini", "./configs/*.yaml"],
)
```

`distributed_files` accepts glob patterns, individual files, and directories.
Directories are traversed recursively, including non-Python files and empty
subfolders. If a pattern matches nothing, connection raises a `ValueError`.
Absolute paths are rejected; keep distributed file paths relative to the client
working directory. This is important for modules imported from relative
subdirectories: include the subdirectory or a glob for its files, otherwise the
remote worker may fail to import the module.

Do not distribute credentials, private keys, or very large datasets. Prefer
small code/config payloads and explicit shared storage plans for large data.

## `@parl.remote_class` arguments

Valid keyword arguments are exactly `max_memory`, `wait`, and `n_gpu`.

| Argument | Default | Meaning | Notes |
| --- | --- | --- | --- |
| `max_memory` | `None` | Maximum memory in MB for each remote instance. | Use for actor-level memory guardrails, not as a substitute for host monitoring. |
| `wait` | `True` | Whether remote method calls block until the result is returned. | `False` returns future objects. |
| `n_gpu` | `0` | Number of GPUs requested by each remote instance. | Requires a GPU-mode cluster and enough GPU worker capacity. |

Both decorator forms are accepted:

```python
@parl.remote_class
class BlockingActor:
    ...

@parl.remote_class(max_memory=300, wait=False, n_gpu=1)
class AsyncGpuActor:
    ...
```

Inside an xparl worker process, PARL marks the environment so the decorator
returns the original class locally instead of recursively launching another
remote actor for that class definition.

## `wait=False` futures

Use `wait=False` for a compact parallel style without manually creating Python
threads:

```python
import parl

@parl.remote_class(wait=False)
class Counter:
    def total(self, n):
        return sum(range(n))

parl.connect("localhost:6006")
actors = [Counter() for _ in range(4)]
jobs = [actor.total(1000) for actor in actors]
results = [job.get() for job in jobs]  # get() blocks until each remote call finishes.
```

`job.get()` returns the same value the original method would return in blocking
mode. Remote exceptions surface when creating the actor, calling a method, or
calling `get()`, depending on where the failure occurs.

## GPU actors

Use GPU actors only with a GPU-mode xparl cluster:

```python
import os
import parl

@parl.remote_class(n_gpu=2)
class GpuActor:
    def visible_devices(self):
        return os.environ.get("CUDA_VISIBLE_DEVICES", "")

parl.connect("localhost:8002")
actor = GpuActor()
print(actor.visible_devices())
```

A CPU cluster rejects GPU requests. A GPU cluster can reject CPU-only jobs. If a
user wants mixed CPU and GPU workflows, plan separate clusters or separate code
paths rather than assuming automatic fallback.

## Data and serialization guidance

PARL serializes code, class definitions, initialization arguments, method
arguments, and return values for remote execution. Prefer simple, predictable
payloads:

- Native Python scalars, lists, tuples, and dictionaries.
- NumPy arrays for numerical data.
- Small config files sent through `distributed_files`.

Avoid passing complex custom objects unless they are known to be serializable in
the same package environment on every worker. For large NumPy arrays,
serialization can dominate runtime; Python 3.8+ improves pickle performance, and
`pyarrow` may be used by PARL when installed, but it is optional and should not
be assumed.

## Boundaries with sibling sub-skills

Use this reference for distributed mechanics. For RL algorithm structure,
actor/learner training loops, IMPALA/A2C/PPO-style recipes, and safe example
adaptation, read `algorithm-recipes`. For package imports, backend selection,
model/agent base classes, and save/restore behavior, read `core-framework`.
