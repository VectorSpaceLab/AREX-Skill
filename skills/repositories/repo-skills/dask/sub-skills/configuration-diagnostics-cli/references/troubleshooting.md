# Configuration, Diagnostics, And CLI Troubleshooting

## Config Value Does Not Take Effect

Check these in order:

1. **Wrong process timing:** Query-planning and backend-selection settings may need to be set before importing `dask.array` or `dask.dataframe`. Start a fresh Python process with YAML or env vars already in place.
2. **Wrong key spelling:** Dask canonicalizes hyphen and underscore forms against existing keys, but nested paths still need the right sections. Compare with `dask config list` or `dask.config.config`.
3. **Override too late:** If graph construction already happened, a config change before `.compute()` may not affect metadata or graph-building choices captured earlier.
4. **Different environment:** Ensure the CLI, notebook kernel, test runner, and Python interpreter import the same installed Dask environment.
5. **Collection-specific ownership:** For array/dataframe keys, confirm collection import timing and route detailed behavior to the owning collection sub-skill.

## `DASK_CONFIG` Path Surprises

Symptoms:

- `dask config set` writes to an unexpected location.
- `dask config find KEY` cannot find a key you expect.
- Python and shell sessions see different values.

Resolution:

- Print active paths with:

```python
import dask.config
print(dask.config.paths)
print(dask.config.PATH)
```

- Remember that `DASK_CONFIG` is appended to the read path list and is also used as the default write directory.
- If changing `DASK_CONFIG` inside a running process, call `dask.config.refresh()` or start a fresh process; module-level `paths` and `PATH` are initialized from environment state.

## YAML Parsing Or Schema Errors

Dask config files must parse as YAML/JSON and have a mapping/dictionary at the top level. Malformed files raise errors that include the failing path. Fix indentation, quoting, and top-level structure first.

Valid shape:

```yaml
optimization:
  fuse:
    active: false
```

Invalid shape:

```yaml
- optimization.fuse.active=false
```

For repository development, the bundled default `dask.yaml` is validated against `dask-schema.yaml`; add schema entries when adding defaults.

## Missing Config Key

- Python: `dask.config.get("missing.key")` raises unless a `default=` is supplied.
- CLI: `dask config get missing.key` exits nonzero and prints `Section not found: missing.key`.
- For optional packages such as `distributed`, import the package first when inspecting defaults contributed by that package.

## `dask config set` Side Effects

`dask config set KEY VALUE` writes persistent YAML. To avoid unintended user config mutation:

- Prefer temporary Python overrides with `with dask.config.set({...}):`.
- For tests or demos, pass `--file` pointing to a temporary file.
- Inspect what will be read with `dask config find KEY` before changing persistent config.

## Optional Diagnostics Dependencies

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `ResourceProfiler` says `psutil` is required | `psutil` missing | Install `psutil` or skip resource profiling |
| `.visualize()` for profilers fails | `bokeh` and/or `jinja2` missing | Install Dask diagnostics extra or inspect `.results` directly |
| `Cache` construction fails | `cachey` missing | Install `cachey` or avoid opportunistic cache |
| Browser does not open from `dask docs` | Headless/noninteractive environment | Print or open `https://docs.dask.org` manually |

The `diagnostics` extra covers visualization dependencies, not every optional tool used by local profiling or caching.

## Distributed Not Installed

Core Dask can still compute with local schedulers and diagnostics:

```python
collection.compute(scheduler="sync")
collection.compute(scheduler="threads")
collection.compute(scheduler="processes")
```

If code imports `distributed`, `Client`, cluster classes, dashboard APIs, or distributed CLI commands, install the compatible `distributed` extra/package or rewrite the workflow to use local schedulers.

## CLI Extension Warnings

Warnings at CLI startup often come from third-party `dask_cli` entry points. Check whether the entry point target imports successfully and returns a `click.Command` or `click.Group`. Name collisions can overwrite existing commands with a warning.

## Warnings As Errors In Tests

Dask's pytest configuration treats warnings as errors with selective ignores. If a local diagnostics or CLI test fails because of a warning:

1. Read the warning category and source.
2. Prefer fixing the warning at its source.
3. Use an existing project warning helper or targeted `pytest.warns` only when the warning is intentional behavior.
4. Do not add broad warning filters for a narrow workflow failure.

## Hard Diagnostic Cases

### Import-Time Query Planning

A user sets `dask.config.set({"dataframe.query-planning": False})` after importing `dask.dataframe` and sees no behavior change. Diagnose by moving the setting into YAML or `DASK_DATAFRAME__QUERY_PLANNING=False` before process start, then re-importing in a fresh process.

### Local Profiling Without Distributed

A user wants a progress bar and task timings on a workstation without `distributed`. Use `ProgressBar` plus `Profiler` around a final `.compute(scheduler="threads")`, inspect `prof.results`, and avoid dashboard-specific instructions.
