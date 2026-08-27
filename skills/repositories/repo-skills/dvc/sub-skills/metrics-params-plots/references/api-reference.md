# API Reference for Metrics and Params

This checkout exposes public read-style helpers in `dvc.api.show`. They open a DVC repo, collect tracked or targeted data, flatten the result for easy use, and return plain dictionaries.

## `dvc.api.metrics_show`

Verified signature:

```python
dvc.api.metrics_show(*targets, repo=None, rev=None, config=None) -> dict
```

Arguments:

- `*targets`: metric file paths to inspect. If omitted, DVC reads tracked metric files from `dvc.yaml` / stage outputs. Explicit target files do not need to be declared as metrics.
- `repo`: local path or Git URL for the DVC repository. If omitted, DVC searches upward from the current working directory.
- `rev`: Git revision, branch, tag, commit hash, or experiment name. If omitted, the current workspace is used.
- `config`: optional DVC config dictionary passed to `Repo.open()`.

Return shape:

- Returns `{}` when no metrics are found.
- Returns the selected revision's metrics as one flat dictionary.
- If one metric file contributes a key, the key is returned as-is.
- If multiple metric files contain the same top-level key, DVC prefixes ambiguous keys as `<file>:<key>`.
- Nested metric dictionaries remain nested in `metrics_show`; metric diff CLI flattens nested paths for display.

Example:

```python
import json
import dvc.api

metrics = dvc.api.metrics_show("reports/metrics.json", repo=".", rev="HEAD")
print(json.dumps(metrics, indent=2, sort_keys=True))
```

Duplicate-key example:

```python
# reports/train.json and reports/test.json both contain {"accuracy": ...}
metrics = dvc.api.metrics_show("reports/train.json", "reports/test.json")
# Expected keys look like:
# {
#   "reports/train.json:accuracy": 0.91,
#   "reports/test.json:accuracy": 0.87,
# }
```

## `dvc.api.params_show`

Verified signature:

```python
dvc.api.params_show(*targets, repo=None, stages=None, rev=None, deps=False, config=None) -> dict
```

Arguments:

- `*targets`: params files to inspect, such as `params.yaml`, `params.json`, `params.toml`, or `params.py`. Explicit target files do not need to be declared as params.
- `repo`: local path or Git URL for the DVC repository. If omitted, DVC searches upward from the current working directory.
- `stages`: one stage name or an iterable of stage names. For stages in nested `dvc.yaml` files, use `{relpath-to-dvc.yaml}:{stage}`.
- `rev`: Git revision, branch, tag, commit hash, or experiment name. If omitted, the current workspace is used.
- `deps`: when `True`, limit returned params to stage dependency params.
- `config`: optional DVC config dictionary passed to `Repo.open()`.

Return shape:

- Returns `{}` when no params are found.
- Returns the selected revision's params as one flat dictionary.
- If one params file contributes a key, the key is returned as-is.
- If multiple params files contain the same top-level key, DVC prefixes ambiguous keys as `<file>:<key>`.
- Stage filtering returns only params used by those stages unless explicit targets broaden what is read.
- Python params files can expose constants and class attributes selected by dotted key paths such as `Config.foo`.

Examples:

```python
import dvc.api

all_params = dvc.api.params_show(repo=".")
train_params = dvc.api.params_show(stages="train", deps=True)
nested_stage = dvc.api.params_show(stages="pipelines/train/dvc.yaml:train")
selected_file = dvc.api.params_show("configs/train.toml", rev="HEAD~1")
```

Duplicate-key example:

```python
# params.yaml and configs/prod.yaml both contain {"lr": ...}
params = dvc.api.params_show("params.yaml", "configs/prod.yaml")
# Expected keys look like:
# {
#   "params.yaml:lr": 0.001,
#   "configs/prod.yaml:lr": 0.0005,
# }
```

## Helper Script Contract

The bundled `scripts/summarize_metrics_params.py` wraps these APIs and prints JSON:

```bash
python scripts/summarize_metrics_params.py \
  --repo . \
  --rev HEAD \
  --metrics-target reports/metrics.json \
  --params-target params.yaml \
  --stage train \
  --deps
```

Output shape:

```json
{
  "ok": true,
  "repo": ".",
  "rev": "HEAD",
  "metrics": {"ok": true, "data": {}},
  "params": {"ok": true, "data": {}},
  "warnings": []
}
```

If DVC cannot find a repository, cannot parse a target file, or cannot import `dvc.api`, the helper returns `ok: false` and records the exception type/message under the affected section instead of raising a traceback.

## Error and No-Data Semantics

- API helpers use `on_error="raise"` internally, so malformed files or missing targets raise exceptions to callers.
- The bundled helper catches exceptions and turns them into JSON result objects.
- Empty data is not necessarily an error: an initialized repo with no tracked metrics or params returns `{}`.
- If a target path is supplied and does not exist, expect a file-not-found style exception.
- If duplicate metric/param keys appear, expect file-prefixed keys rather than a nested per-file result.

## Safe Use Rules

- These APIs read repository metadata and files; they do not run pipeline commands.
- Passing a remote Git URL as `repo` may require network access and credentials. Prefer local paths for agent automation unless the user explicitly asked for a remote repo.
- `rev` accepts experiment names, but experiment table interpretation belongs to the experiments sub-skill.
- Do not rely on local checkout paths in reusable examples; pass `--repo` or `repo=` from the current task context.
