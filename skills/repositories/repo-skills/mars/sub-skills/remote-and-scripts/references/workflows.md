# Remote Workflows

## Purpose

Read this when the user wants a concise recipe for Mars remote execution,
fan-out/fan-in, logs, or script-style workflows.

## 1) Fan out a small function

```python
import mars.remote as mr

r = mr.spawn(lambda x: x + 1, args=(10,))
value = r.execute().fetch()
```

Use this when the task is a single remote callable and the user wants the result
back as an ordinary Python value.

## 2) Fan in several results

```python
import mars.remote as mr

results = [mr.spawn(lambda x: x + 1, args=(i,)) for i in range(3)]
values = mr.ExecutableTuple(results).execute().fetch()
```

Use this when the task should launch several remote callables together and then
retrieve the combined results.

## 3) Pass one remote result into another

```python
import mars.remote as mr

def inc(x):
    return x + 1

def total(xs):
    return sum(xs)

values = [mr.spawn(inc, args=(i,)) for i in range(3)]
combined = mr.spawn(total, args=(values,)).execute().fetch()
```

Use this when a later Mars task depends on earlier remote work.

## 4) Retrieve logs from a distributed session

```python
print(r.fetch_log())
print(r.fetch_log(offsets=0))
```

Use `fetch_log()` when the runtime is distributed and the user expects worker
output to come back to the client. If no log appears, check whether the session
is actually distributed and whether the task has completed.

## 5) Script-style execution

`run_script` is the right contract when the user wants to launch a script on the
Mars side rather than a single callable.

Typical signals:
- a script needs worker-side environment variables
- multiple workers should run the same script
- the user thinks in terms of a batch script rather than a function

The bundled smoke helper does not attempt to mimic a full cluster script run; it
stays in the safe local spawn path and leaves real `run_script` runs for a
proper runtime.
