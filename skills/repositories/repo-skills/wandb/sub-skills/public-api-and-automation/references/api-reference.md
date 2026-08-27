# Public API Reference

## API construction and auth

- Import as `import wandb`; construct `api = wandb.Api(overrides=None, timeout=None)` for the common case.
- Use `timeout` for long GraphQL or history operations; use `overrides={"base_url": "https://...", "entity": "...", "project": "..."}` for non-default hosts or path defaults.
- Prefer environment/config authentication or `wandb login`; do not embed credentials in generated scripts, docs, notebooks, or skill content.
- `wandb.Api()` requires online access and configured auth. Offline run logging is separate from Public API reads.

## Path shapes

- Project path: `entity/project` for `api.runs(path)`, `api.reports(path)`, and many listing calls.
- Run path: `entity/project/run_id` for `api.run(path)`. If `overrides` set `entity` and/or `project`, shorter paths may resolve, but full paths are safer in automation scripts.
- Sweep path: `entity/project/sweep_id` for `api.sweep(path)`.
- Report path via `api.from_path("entity/project/reports/Report-Name--ID")` or list reports with `api.reports("entity/project")`.

## Common resource access

```python
import wandb

api = wandb.Api(timeout=60)
project = api.project("project", entity="entity")
runs = api.runs(
    "entity/project",
    filters={"state": "finished", "summary_metrics.val_loss": {"$lt": 0.2}},
    order="+created_at",
    per_page=100,
)
for run in runs:
    print(run.id, run.name, run.state, run.url)
```

Important accessors:

- `api.projects(entity)` returns lazy project objects; `api.project(name, entity=...)` returns one project handle.
- `api.runs(path, filters=None, order="+created_at", per_page=50, include_sweeps=False, lazy=True)` returns a lazy iterable of `Run` objects.
- `api.run("entity/project/run_id")` returns one fully loaded run.
- `api.sweep("entity/project/sweep_id")` returns a sweep handle for inspection; sweep execution belongs to the sweeps/launch skill area.
- `api.reports("entity/project", name=None, per_page=50)` returns `BetaReport` objects. `api.from_path(path)` can resolve project, run, report, and other path-like resources.

## Run fields and mutation safety

Typical run fields and properties:

```python
run = api.run("entity/project/run_id")
print(run.id, run.name, run.display_name, run.state, run.created_at)
print(run.config)          # dict, auto-loads full data if needed
print(dict(run.summary))   # HTTPSummary-like mapping of summary metrics
```

- `run.config` is for configuration values recorded with the run.
- `run.summary` is for final/latest summary metrics; convert to `dict(run.summary)` when serializing.
- `run.history(samples=500, keys=None, pandas=True)` returns sampled history and is fast for previews.
- `run.scan_history(keys=None, page_size=1000, min_step=0, max_step=None, use_cache=True)` iterates unsampled history and is the right choice for exports.
- `run.update()` persists mutable run metadata after changes; do not call it for read-only export tasks.
- `run.delete(delete_artifacts=False)` is destructive; require explicit user confirmation before using it.

## Filters and ordering

`api.runs()` filters use MongoDB-like query dictionaries over run properties, config, and summary metrics:

```python
filters = {
    "$and": [
        {"state": "finished"},
        {"config.dataset": "imagenet"},
        {"summary_metrics.accuracy": {"$gte": 0.9}},
        {"tags": {"$in": ["baseline", "prod"]}},
    ]
}
runs = api.runs("entity/project", filters=filters, order="-summary_metrics.accuracy")
```

Supported operators include `$and`, `$or`, `$nor`, `$eq`, `$ne`, `$gt`, `$gte`, `$lt`, `$lte`, `$in`, `$nin`, `$exists`, and `$regex`. Useful sort keys include `created_at`, `heartbeat_at`, `config.*.value`, and `summary_metrics.*`; prefix with `+` or `-`.

## Files and reports

```python
run = api.run("entity/project/run_id")
for file in run.files(pattern="%.json", per_page=50):
    print(file.name, file.size, file.url)
    # file.download(root="downloads", replace=True)

report = next(api.reports("entity/project", name="My Report"))
print(report.display_name, report.url)
print(report.spec)
```

- `run.files(names=None, pattern=None, per_page=50)` lists files associated with a run. `pattern` uses SQL-LIKE syntax such as `%.json`.
- `run.file(name)` fetches a single file handle.
- Download files only into user-approved output directories; avoid destructive overwrite unless requested.
- `BetaReport` exposes `spec`, `sections`, `runs(section)`, and URL/metadata fields. Treat report APIs as beta and subject to change.

## Sweep inspection

```python
sweep = api.sweep("entity/project/sweep_id")
print(sweep.id, sweep.name, sweep.config)
for run in sweep.runs:
    print(run.id, run.summary.get("metric"))
```

Use Public API sweep access to inspect existing sweeps and their runs. Do not create or launch agents from this sub-skill; use the sweep/launch skill area for execution.
