# DVC Experiments API Reference

## Purpose

Use this reference when a future agent needs the public Python API for saving or inspecting experiments. These APIs require `dvc` to be importable and an accessible DVC repository; they do not configure remotes, credentials, stages, metrics, params, or plots.

## `dvc.api.exp_save`

Signature verified for this package version:

```python
dvc.api.exp_save(name=None, force=False, include_untracked=None)
```

Behavior:

- Creates a new DVC experiment from the current workspace, equivalent to using `dvc exp save` programmatically.
- `name` is optional; when omitted, DVC generates a human-readable experiment name.
- `force=True` overwrites an existing experiment with the same name.
- `include_untracked` accepts a list of untracked file paths to include in the saved experiment.
- Returns the experiment Git revision as a string.
- Raises an experiment-exists error when a duplicate name is used without `force=True`.

Example:

```python
from dvc.api import exp_save

rev = exp_save(name="manual-fix", force=False, include_untracked=["notes/config.yaml"])
print(rev)
```

Use CLI `dvc exp save --json` instead when the user wants command output rather than embedding DVC in Python.

## `dvc.api.exp_show`

Signature verified for this package version:

```python
dvc.api.exp_show(repo=None, revs=None, num=1, param_deps=False, force=False, config=None) -> list[dict]
```

Behavior:

- Returns a `list[dict]`, where each dictionary represents one displayed experiment row after DVC tabulates experiments.
- `repo` defaults to the current project by walking up from the current working directory. It can also be a filesystem path or supported Git URL.
- `revs` accepts one revision string or a list of revision strings used as baseline reference points.
- `num` limits first-parent commits from each baseline; use a negative value to include all first-parent commits.
- `param_deps=True` includes only parameters that are stage dependencies.
- `force=True` ignores cached completed-experiment table data and re-collects rows.
- `config` passes a config dictionary through to the DVC project.

Example:

```python
from dvc.api import exp_show

rows = exp_show(repo=".", revs=["HEAD"], num=3, param_deps=True, force=True)
for row in rows:
    print(row)
```

Use the bundled helper for shell-friendly JSON:

```bash
python scripts/inspect_experiments.py --repo . --rev HEAD --num 3 --param-deps --force
```

## Choosing API Or CLI

- Use the CLI when mutating experiments (`run`, `apply`, `branch`, `push`, `pull`, `remove`, `rename`, `clean`) unless the user specifically asks for Python API usage.
- Use `exp_show()` or `scripts/inspect_experiments.py` for read-only JSON inspection in automation.
- Use `exp_save()` for a Python workflow that must capture the current workspace as an experiment and then consume the returned revision.
- Route metrics/params/plots interpretation to `metrics-params-plots`; `exp_show()` only surfaces the values in experiment rows.
