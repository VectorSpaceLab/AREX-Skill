# SwanLab `Api` Reference

This reference covers the object-oriented query/admin surface. It intentionally
excludes credential storage, experiment logging, local run sync, and converter
workflows.

## Construction and response model

```python
import os
import swanlab

api = swanlab.Api(
    api_key=os.environ.get("SWANLAB_API_KEY"),
    host=os.environ.get("SWANLAB_API_HOST"),  # optional API host
)
```

Credential resolution is: explicit `api_key`/`host`, then any in-process login
state, then configured settings. Missing or blank API keys raise an
authentication error. Blank hosts raise a host validation error. The `Api`
constructor may authenticate immediately to discover current user metadata, so
do not use it as an offline validation helper.

Most entity methods return lazy handles. A remote request usually happens when
you access a property, iterate the object, or call `.wrapper()`:

```python
project_resp = api.project("alice/demo").wrapper().json()
if not project_resp["ok"]:
    raise RuntimeError(project_resp["errmsg"])
print(project_resp["data"]["name"])
```

The common response envelope is:

```text
{"ok": bool, "errmsg": str, "data": object | null}
```

Lazy properties generally return empty/default values after HTTP failures and
record errors internally; `.wrapper().json()` is the safest way to surface those
errors in user-facing code. Mutating helpers often return `False`, `None`, or an
`ok=False` response on 4xx/5xx failures instead of crashing.

## Path and name validation

Use these public path shapes exactly:

| Target | Shape | Example |
| --- | --- | --- |
| Workspace/user | one segment | `alice` |
| Project | two segments | `alice/demo` |
| Run/experiment | three segments | `alice/demo/run-abc123` |

Rules:

- Paths must be strings with no leading/trailing whitespace.
- Empty segments and doubled slashes are invalid.
- `Api.project()` requires a project path; `Api.run()` requires a run path;
  `Api.runs()` and `Api.runs_get()` require a project path.
- Project names for creation are 1-100 characters and may contain only
  `0-9`, `a-z`, `A-Z`, `-`, `_`, `.`, and `+`.
- Visibility is `PUBLIC` or `PRIVATE`.

## Pagination

`PaginatedQuery` validates page and size before the request:

- `page >= 1`
- `size` must be one of `10, 12, 15, 20, 24, 27, 50, 100`
- `all=True` is a client-side auto-pagination flag; it is not sent as a backend
  query parameter.

When `all=False`, paginated iterators stop after the requested page. When
`all=True`, they continue until the backend reports the final page.

## User and workspace metadata

```python
user = api.user()
print(user.username, user.name, user.email)

workspace = api.workspace("alice")       # defaults to current user if omitted
print(workspace.name, workspace.role, workspace.workspace_type)

for ws in api.workspaces("alice"):
    print(ws.username, ws.workspace_type)
```

Workspace properties include `name`, `username`, `workspace_type`, `profile`,
`comment`, and `role`.

Create projects through a workspace or through `Api.create_project()`:

```python
project = api.create_project(
    username="alice",
    name="demo-1.0+cpu",
    visibility="PRIVATE",
    description="short description",
)
if project is None:
    raise RuntimeError("project creation failed")
```

## Project metadata and run lists

```python
project = api.project("alice/demo")
print(project.name, project.visibility, project.url, project.count)

for project in api.projects("alice", search="demo", sort="update", size=20, all=True):
    print(project.path)
```

Project properties include `project_id`, `name`, `path`, `url`, `description`,
`visibility`, timestamps, `labels`, and aggregate `count`.

Run listing has two modes:

```python
# GET mode: standard pagination, compact run data.
for run in api.runs_get("alice/demo", page=1, size=20, all=False):
    print(run.name, run.state)

# POST mode: complex filters, groups, and sorts.
filters = [{"key": "state", "type": "STABLE", "op": "EQ", "value": ["RUNNING"]}]
groups = [{"key": "cluster", "type": "STABLE"}]
sorts = [{"key": "createdAt", "type": "STABLE", "order": "DESC"}]
for run in api.project("alice/demo").runs(filters=filters, groups=groups, sorts=sorts):
    print(run.name, run.group)
```

`Api.runs(path, filters=...)` supports filter lists directly. `Project.runs(...)`
is the route when you also need `groups` or `sorts`.

Filter item schema:

```python
{"key": "state", "type": "STABLE", "op": "EQ", "value": ["RUNNING"]}
```

Group item schema:

```python
{"key": "cluster", "type": "STABLE"}
```

Sort item schema:

```python
{"key": "createdAt", "type": "STABLE", "order": "DESC"}
```

Allowed values:

- `type`: `SCALAR`, `CONFIG`, or `STABLE`
- Stable keys: `state`, `name`, `description`, `show`, `pin`, `baseline`,
  `colors`, `cluster`, `job`, `createdAt`, `updatedAt`, `finishedAt`,
  `pinnedAt`, `labels`
- Filter `op`: `EQ`, `NEQ`, `GTE`, `LTE`, `IN`, `NOT IN`, `CONTAIN`
- Sort `order`: `ASC` or `DESC`
- Filter `value` must be a list.

Validated filters/groups/sorts are sent with `active: True` added to each item.

Deletion helpers are dry-run by default:

```python
api.project("alice/demo").delete(commit=False)       # prints pending delete
api.run("alice/demo/run-abc123").delete(commit=False)
```

Use `commit=True` only when the user explicitly asks for deletion.

## Run/experiment metadata

```python
run = api.run("alice/demo/run-abc123")
print(run.name, run.state, run.url, run.profile)
```

Run properties include `project_id`, `run_id`, `name`, `description`, `type`,
`state`, `url`, `show`, `labels`, `group`, `job_type`, root clone identifiers,
`user`, timestamps, and `profile`.

Run paths accept a visible slug, but metric payloads are sent with the backend
run CUID after lazy resolution.

## Metric keys, scalar metrics, summaries, media, and logs

Prefer `series()` over deprecated column APIs:

```python
series = run.series(metric_type="SCALAR", metric_class="CUSTOM", search="loss")
print(series.total)
for key in series:
    print(key.key, key.key_class)

availability = series.availability(["train/loss", "eval/acc"])
```

`metric_type` is `SCALAR` or `MEDIA`; `metric_class` is `CUSTOM` or `SYSTEM`.
Scalar system keys are identified by SwanLab's internal system-key prefix.

Scalar metric data:

```python
metrics = run.metrics(
    keys=["train/loss", "eval/acc"],
    sample=1500,
    ignore_timestamp=False,
    all=False,
)
```

Rules:

- `keys` must be a non-empty list of non-blank strings.
- `sample` is capped at 1500 for sampled scalar queries.
- `all=True` fetches full-resolution scalar data through the export path.
- `range_query` is scalar-only and can select by step or timestamp.

Range query examples:

```python
run.metrics(keys=["loss"], range_query={"start": 0, "end": 500})
run.metrics(keys=["loss"], range_query={"type": "timestamp", "start": 1715769600})
run.metrics(keys=["loss"], range_query={"last": 300_000, "tail": 50})
```

Range constraints:

- `head` and `tail` are mutually exclusive.
- `last` is mutually exclusive with `start`/`end`.
- `start <= end` when both are provided.
- Timestamp values may be integer milliseconds or shorter numeric timestamps;
  shorter positive values are padded to milliseconds.

Summaries:

```python
all_summaries = run.summary()
loss_summary = run.summary(keys=["train/loss"])
```

Media metrics:

```python
current = run.medias(keys=["sample/image"], step=0)
all_media = run.medias(keys=["sample/image"], all=True)
```

Media responses may include presigned URLs for stored media items.

Logs:

```python
logs = run.logs(offset=0, level="INFO", ignore_timestamp=False)
export_resp = run.export_logs(start=0, rows=500_000).json()
```

Log levels are `DEBUG`, `INFO`, `WARN`, and `ERROR`. `export_logs()` returns a
response whose `data` contains a downloadable log URL when the backend succeeds.

## CSV export behavior

Scalar CSV export is available from metric key objects:

```python
key = next(iter(run.series(metric_type="SCALAR", search="loss")))
resp = key.export_csv().json()
if resp["ok"]:
    print(resp["data"]["url"])
```

CSV export is scalar-only. Media keys return `ok=False` for CSV export. The older
`Column.export_csv()` compatibility path is deprecated with the column API.

## Deprecated column compatibility

`Api.column()`, `Api.columns()`, `Experiment.column()`, and
`Experiment.columns()` still exist for compatibility but are deprecated. They do
fuzzy lookup/listing of column metadata and then route metric data through the
current metric implementation. Prefer `series()` for key listing and
`metrics()`/`medias()` for data.

## Self-hosted metadata and admin operations

```python
sh = api.self_hosted()
print(sh.enabled, sh.expired, sh.root, sh.plan, sh.seats)
```

Info properties include `enabled`, `expired`, `root`, `plan`, and `seats`.
Root-only helpers validate both expiration and root permission before making the
request:

```python
for user in sh.get_users(page=1, size=20, all=True):
    print(user)

for project in sh.get_projects(search="demo", creator="alice", all=True):
    print(project)

for group in sh.get_groups(search="team", all=True):
    print(group)

summary_resp = sh.get_usage_summary().json()
```

`create_user(username, password)` requires non-blank strings and root permission.
If the self-hosted instance is expired or the caller is not root, these helpers
raise a `ValueError` before the network operation.
