# Mars Troubleshooting

## Purpose

Read this for cross-cutting install, import, build, and environment failures that
can affect multiple Mars workflows.

## 1) Editable install fails with `build_editable`

**Symptom**
- `pip install -e` reports that the build backend does not support the
  `build_editable` hook.

**Likely cause**
- The project uses a build backend that does not expose a PEP 660 editable
  install path in the current packaging stack.

**Recovery**
- Use a normal install from a checkout instead of editable mode.
- If the checkout should avoid the optional web UI build, set `NO_WEB_UI=1`
  before installation.

**Next check**
- `python -m pip check`
- `python -I -c "import mars; print(mars.__version__)"`

## 2) `mars.dataframe` import trips over `ray`

**Symptom**
- Importing `mars.dataframe` fails with an error around `ray.__version__` or a
  partially initialized `ray` module.

**Likely cause**
- A shadowed `ray` directory/module on the current path, or a partial optional
  Ray install that does not look like the real package.

**Recovery**
- Run from a neutral directory with `python -I`.
- Remove the shadowing path from `PYTHONPATH` or the working directory.
- If you truly want the Ray route, install the real optional `ray` dependency
  and use the backend sub-skill.

**Next check**
- `python -I -c "import mars.dataframe as md; print(md.__name__)"`

## 3) Web UI build is unwanted or unavailable

**Symptom**
- Installation tries to build the web UI or asks for Node/npm tools.

**Likely cause**
- The source checkout contains the web UI bundle and `setup.py` will try to
  build it unless told otherwise.

**Recovery**
- Set `NO_WEB_UI=1` for the install command when you only need package usage.
- This is usually enough for skill creation and local inspection.

## 4) `pip check` shows NumPy / pandas / SciPy / scikit-learn mismatch

**Symptom**
- `pip check` reports incompatibilities after installation.

**Likely cause**
- The environment has newer scientific stack packages than Mars expects.

**Recovery**
- Align the environment with the package metadata and reinstall the package.
- If you are reusing an existing environment, avoid mutating unrelated packages
  without permission; create a private prefix instead.

## 5) Optional backend or integration import fails

**Symptom**
- A learn integration, Ray route, GPU path, or cluster helper raises
  `ImportError` or a missing package message.

**Likely cause**
- The required optional dependency or backend is intentionally not installed.

**Recovery**
- Read the owning sub-skill's troubleshooting page.
- Install only the specific optional extra needed for that route.
- Do not treat the CPU baseline as proof of GPU/Ray/Kubernetes/YARN support.

## 6) `mars-supervisor` or `mars-worker` help works but runtime startup fails

**Symptom**
- CLI help succeeds, but an actual service startup hits port, cluster, or module
  loading issues.

**Likely cause**
- Missing supervisors, invalid ports, bad config, or unsupported backend tool
  availability.

**Recovery**
- Use the deployment sub-skill references for backend-specific prerequisites.
- Check that the command line matches the documented flags.
- Confirm the service/tooling dependencies before trying a real cluster.

## 7) Local session or remote smoke emits cleanup noise

**Symptom**
- A small smoke reports `status: ok` but stderr includes warnings about server
  shutdown, client cleanup, `Actor caller has created too many clients`,
  `Failed to upload node info`, or leaked shared-memory resources.

**Likely cause**
- Mars's local service is starting and stopping quickly during a tiny smoke, or
  the process was interrupted near shutdown.

**Recovery**
- Treat the warning as non-fatal when the helper JSON reports `status: ok` and
  all asserted results match.
- Always call `mars.stop_server()` in smoke snippets and cleanup blocks.
- Re-run the smoke from a neutral directory if there is any path shadowing or an
  import failure, not just cleanup warnings.
