# Runner API

## Verified constructor

```python
Runner(flow_file, show_output=True, profile=None, env=None, cwd=None, file_read_timeout=3600, **kwargs)
```

Use `Runner` as a context manager so temporary files and subprocesses are cleaned up:

```python
from metaflow import Runner

with Runner("train_flow.py", show_output=False, pylint=False, env={"USERNAME": "disco"}) as runner:
    executing = runner.run(max_workers=1)
    assert executing.status == "successful"
    run = executing.run
```

## Returned objects

`runner.run(...)` returns an `ExecutingRun` with:

- `status`: `running`, `successful`, `failed`, or `timeout`.
- `returncode`: subprocess return code.
- `stdout` and `stderr`: captured streams.
- `run`: a `metaflow.Run` object for artifact and metadata inspection.
- `wait(timeout=None, stream=None)` and `stream_log(stream, position=None)` on async paths.

`runner.spin(...)` returns an `ExecutingTask` with the same process surface and a `task` object.

## Kwargs split

`Runner` builds a Click API from the flow script. Put arguments before the flow command into `Runner(...)`; put arguments after `run`/`resume` into the method call.

Correct:

```python
with Runner("flow.py", pylint=False, env={"USERNAME": "disco"}) as runner:
    runner.run(max_workers=1, tags=["smoke"])
```

Incorrect:

```python
runner.run(pylint=False)  # Unknown argument: pylint
```

## Artifact readback

Returned `Run` objects are standard Client API objects:

```python
end = executing.run["end"].task
print(end.data.some_artifact)
```

For richer pathspec, namespace, or metadata behavior, read `client-and-data`.
