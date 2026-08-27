# Mars Workflow Map

## Purpose

Read this when you know the task family but want the shortest path to the right
Mars route. Each workflow points to the owning sub-skill and its bundled helper
scripts.

## Workflow families

### Local tensor and DataFrame compute
- Owning sub-skill: `sub-skills/tensor-dataframe-core/`
- Use when the user wants a local session, small tensor math, DataFrame
  transformations, eager mode, `execute`/`fetch`, or tiny file-backed IO.
- Typical commands:
  - `import mars`
  - `mars.new_session()`
  - `import mars.tensor as mt`
  - `import mars.dataframe as md`
- Read `sub-skills/tensor-dataframe-core/references/workflows.md` for step-by-step
  examples and `sub-skills/tensor-dataframe-core/scripts/check_tensor_dataframe.py`
  for a safe smoke helper.

### Remote functions and script execution
- Owning sub-skill: `sub-skills/remote-and-scripts/`
- Use when the user wants `mars.remote.spawn`, nested remote DAGs, logs, or
  run-script style execution.
- Typical commands:
  - `import mars.remote as mr`
  - `mr.spawn(func, args=(...))`
  - `mr.ExecutableTuple([...]).execute().fetch()`
- Read `sub-skills/remote-and-scripts/references/workflows.md` and run
  `sub-skills/remote-and-scripts/scripts/check_mars_remote.py` for a tiny smoke.

### Mars Learn and optional integrations
- Owning sub-skill: `sub-skills/learn-and-integrations/`
- Use when the user wants Mars Learn estimators or optional integration
  packages such as Dask, PyTorch, TensorFlow, XGBoost, LightGBM, Statsmodels,
  Joblib, or Proxima.
- Typical commands:
  - `from mars.learn.cluster import KMeans`
  - `from mars.learn.decomposition import PCA`
  - `from mars.learn.neighbors import NearestNeighbors`
- Read `sub-skills/learn-and-integrations/references/workflows.md` and run
  `sub-skills/learn-and-integrations/scripts/check_mars_learn.py` for a small CPU
  smoke.

### Backend, CLI, and deployment workflows
- Owning sub-skill: `sub-skills/deployment-and-backends/`
- Use when the user wants `mars-supervisor`, `mars-worker`, Ray sessions, GPU
  placement, Kubernetes, or YARN.
- Typical commands:
  - `mars-supervisor --help`
  - `mars-worker --help`
  - `mars.new_session(backend='ray')`
  - `mt.random.rand(..., gpu=True)`
- Read `sub-skills/deployment-and-backends/references/backends.md`,
  `cli-reference.md`, and `troubleshooting.md` before attempting any real
  backend startup.

## Shared checks

- Run bundled Python helpers with the same Python environment where `pymars` is
  installed, for example `python scripts/check_mars_install.py --json`; do not
  rely on a script shebang if it may resolve to a different system Python.
- `scripts/check_mars_install.py` verifies the package import and base runtime
  facts from a clean shell.
- `python -m pip check` should pass after installation.
- Use `references/troubleshooting.md` when a result looks like a package,
  optional-dependency, or path-shadowing problem instead of a Mars API issue.
