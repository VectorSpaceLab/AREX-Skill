# Repository provenance

`schema: disco.repo-provenance.v1`

- Project: NVIDIA cuRobo (cuRoboV2)
- Distribution/import: `nvidia-curobo` / `curobo`
- Source commit: `8e734f3ced1df898990bcd92de40abce475907db`
- Branch: `main`
- Exact tag: none
- Working tree when extraction began: clean
- Inspected package version: `0.0.post1.dev1`
- Public repository: `https://github.com/NVlabs/curobo`

## Evidence baseline

- Packaging and scope: `pyproject.toml`, `setup.py`, `README.md`, `CHANGELOG.md`
- Public modules: `curobo/*.py`
- Implementation evidence: `curobo/_src/{robot,state,types,geom,collision,cost,solver,motion,graph_planner,optim,rollout,transition,perception,util}/`
- Bundled configuration: `curobo/content/configs/`
- Workflow intent: `curobo/examples/`, `docs/getting-started/`, `docs/guides/`, `docs/concepts/`, `docs/reference/`
- Behavior evidence: representative files under `curobo/tests/`

Refresh this skill if the commit/package version changes materially, public v2
modules or config factories change, task YAMLs are reorganized, or solver/result
contracts diverge from the signatures recorded in the bundled API references.
