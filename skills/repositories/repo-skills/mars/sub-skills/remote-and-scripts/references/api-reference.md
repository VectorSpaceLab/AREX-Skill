# Remote API Reference

## Purpose

Read this when you need the verified Mars remote signatures and the function-
dependency contract for local or distributed task graphs.

## Verified APIs

| API | Verified signature or behavior | Use |
| --- | --- | --- |
| `mars.remote.spawn(func, args=(), kwargs=None, retry_when_fail=False, resolve_tileable_input=False, n_output=None, **kw)` | Wraps a Python callable as a Mars object without running it immediately. | Start a remote DAG, pass results between remote calls, or request multiple outputs. |
| `mars.remote.ExecutableTuple([...])` | Bundles several spawned Mars objects so they can execute together. | Fan-in a list of remote tasks. |
| `result.execute()` | Executes a spawned remote object. | Start work on the cluster or local session. |
| `result.fetch()` | Fetches the concrete result after execution. | Return the actual Python value or collection. |
| `result.fetch_log(offsets=0)` | Retrieves logs for distributed execution when the runtime supports log retrieval. | Pull worker-side output back to the client. |
| `mars.remote.run_script(script, data=None, n_workers=1, command_argv=None, session=None, retry_when_fail=False, run_kwargs=None)` | Runs a Python script or file-like object through the Mars remote script contract. | Use for script-style execution; Mars sets `WORLD_SIZE`/`RANK` for workers and injects `session` into the script namespace. |

## Behavioral notes

- `spawn` does not execute immediately; the returned object can be passed as an
  input to another `spawn` call.
- `ExecutableTuple([...]).execute().fetch()` is the cleanest explicit fan-in
  pattern when several remote tasks should complete together.
- `fetch_log()` is most useful in a distributed session; on a tiny local smoke
  it may not show much.
- `run_script` is the workflow contract for script-style execution; Mars sets
  `WORLD_SIZE`/`RANK` for workers and injects `session` into the script
  namespace. The skill's bundled smoke helper focuses on safe spawn/fan-in
  behavior instead of relying on the original repo's sample script.

## Typical script contract signals

The script-run contract is easiest to recognize when the user mentions:

- `WORLD_SIZE`
- worker fan-out
- a script that should run on Mars workers rather than on the client
- environment propagation or command-argument forwarding

If the user wants to inspect script-run behavior, read the troubleshooting page
before trying a real cluster.
