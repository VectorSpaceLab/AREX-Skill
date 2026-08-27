---
name: mars
description: "Routes Mars and pymars users to the right local compute, remote
  execution, learning, and deployment workflows with verified install, import,
  and backend guidance."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Mars

Use this skill for the `mars` / `pymars` package when a user asks about
Mars tensor, DataFrame, remote functions, Mars Learn, local sessions,
cluster/back-end startup, or optional Ray / GPU / Kubernetes / YARN paths.

Mars is a tensor-based unified framework for large-scale data computation that
scales NumPy-, pandas-, and scikit-learn-style workflows. The package exposes
`mars`, `mars.tensor as mt`, `mars.dataframe as md`, `mars.remote as mr`, and
`mars.config.options` as the main public entry points.

## Start here

- Install the public package with `pip install pymars`.
- If you are working from a local checkout, use `NO_WEB_UI=1 python -m pip install .`
  to avoid the optional web UI build.
- Minimal import check: `python -I -c "import mars; print(mars.__version__)"`.
- Use `python -m pip check` after installation.

Read `references/repo-provenance.md` if you need to know whether this skill is
current for the active checkout, or before refreshing it against a newer commit.

## Route map

### `sub-skills/tensor-dataframe-core/`
Use this for local Mars sessions, lazy/eager execution, tensor and DataFrame
creation, execute/fetch patterns, and small file-backed IO workflows.
Typical signals: `new_session`, `execute`, `fetch`, `stop_server`, `mt.*`,
`md.*`, `option_context`, `eager_mode`, `read_csv`, `to_pandas`, `to_numpy`.

### `sub-skills/remote-and-scripts/`
Use this for `mars.remote.spawn`, `ExecutableTuple`, nested remote DAGs,
`fetch_log`, and script-run workflows.
Typical signals: remote fan-out/fan-in, dependency passing, log retrieval, or
`run_script`.

### `sub-skills/learn-and-integrations/`
Use this for Mars Learn estimators and optional integrations such as Dask,
PyTorch, TensorFlow, XGBoost, LightGBM, Statsmodels, Joblib, and Proxima.
Typical signals: `KMeans`, `PCA`, `NearestNeighbors`, `make_blobs`, `fit`,
`predict`, `mars_scheduler`, or integration import questions.

### `sub-skills/deployment-and-backends/`
Use this for `mars-supervisor`, `mars-worker`, Ray sessions, CUDA/GPU notes,
`mars.deploy.kubernetes`, and `mars.deploy.yarn`.
Typical signals: CLI flags, cluster endpoints, `backend='ray'`, `gpu=True`,
`to_gpu`, `to_cpu`, Kubernetes, YARN, or service prerequisites.

## Shared references

- `references/workflows.md` for the high-level workflow map.
- `references/troubleshooting.md` for cross-cutting install/import/build issues.
- `scripts/check_mars_install.py` for a safe import and smoke helper.

## Quick usage rules

- Prefer CPU/local guidance unless the user explicitly asks for Ray, GPU,
  Kubernetes, YARN, or an external ML framework.
- Do not tell future agents to run original repo tests, notebooks, or scripts
  that are not bundled in this skill tree.
- Keep path references inside this skill tree only.
- Optional backends may be documented even when uninstalled, but do not claim
  them as verified unless a backend-specific smoke has passed.

## Common failures

- Editable installs may fail on newer packaging backends because the project
  does not expose a PEP 660 `build_editable` hook. Use a normal install from a
  checkout instead.
- `mars.dataframe` import can trip over a shadowed or partial `ray` module;
  run from a neutral directory and check the optional Ray path if that happens.
- Set `NO_WEB_UI=1` when the checkout does not have the web UI toolchain.

For deeper guidance, open the sub-skill that matches the user’s request.
