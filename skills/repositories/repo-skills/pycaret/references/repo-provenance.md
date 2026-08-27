# Repository Provenance

This file records the source snapshot used to build the generated PyCaret repo skill.

- schema: `disco.repo-provenance.v1`
- repository: `pycaret`
- vcs: `git`
- source_commit: `5ec8f6622bff8a9089f8b2434ac0cd3809f9d65d`
- branch: `main`
- exact_tag: `none`
- remote_url: `https://github.com/pycaret/pycaret.git`
- working_tree_state: `dirty`
- dirty_summary: `untracked skills/ subtree containing the generated skill files`
- package_versions:
  - `pycaret`: `4.0.0a8`
  - `pycaret-server`: `0.1.0a0`

## Evidence paths

All paths below are relative to the repository root and were used as evidence while building this skill.

- `README.md`
- `INSTALL.md`
- `OPERATIONS.md`
- `TEST_PLAN.md`
- `packages/engine/pyproject.toml`
- `packages/engine/pycaret/`
- `packages/engine/tests/`
- `services/api/pyproject.toml`
- `services/api/pycaret_server/`
- `services/api/tests/`
- `apps/web/package.json`
- `apps/web/src/`
- `docs/for_agents/`
- `docs/for_developers/`
- `docs/revamp/VISION.md`
- `docs/revamp/CONTROL_PLANE_SPEC.md`
- `docs/revamp/ARCHITECTURE.md`
- `docs/revamp/ARCHITECTURE_ENGINE.md`
- `docs/revamp/ROADMAP.md`
- `docs/revamp/STATUS.md`
- `docs/revamp/DECISIONS.md`
- `docs/revamp/KILL_LIST.md`
- `infra/docker/`
- `notebooks/`
- `scripts/`

## Refresh baseline

Use this snapshot to decide whether the generated skill should be refreshed after the repository changes. If the package versions, public APIs, route shapes, or workflow docs diverge meaningfully from the evidence above, rebuild the relevant sub-skill or the whole skill.
