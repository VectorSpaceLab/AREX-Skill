# Client API

## Object hierarchy

Metaflow Client objects are pathspec-based:

- `Flow("FlowName")`
- `Run("FlowName/RunID")`
- `Step("FlowName/RunID/StepName")`
- `Task("FlowName/RunID/StepName/TaskID")`
- `DataArtifact("FlowName/RunID/StepName/TaskID/ArtifactName")`

Parent objects are iterable and indexable:

```python
from metaflow import Flow, Run, namespace

namespace(None)
flow = Flow("TrainingFlow")
latest = next(iter(flow))
end_task = Run(latest.pathspec)["end"].task
print(end_task.data)
```

## Namespace and metadata

- `namespace("user:alice")` filters visible objects.
- `namespace(None)` disables namespace filtering.
- `default_namespace()` resets to the default identity.
- `metadata("local@/path")`, `metadata("service@https://...")`, and `inspect_spin(...)` switch metadata providers.
- `get_namespace()` and `get_metadata()` are cheap diagnostics before querying a missing run.

## Tags and logs

Use flow-script `tag` commands to add/list/remove/replace run tags. Use `logs show` and `logs scrub` for stdout/stderr associated with tasks or steps. Logs depend on the datastore/metadata path that produced the run.
