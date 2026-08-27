# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of
Xinference. If the current repo commit, dirty state, package metadata, public
entry points, or major evidence paths differ from this snapshot, run
`refresh-repo-skill` before relying on detailed guidance.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-10T06:27:39Z",
  "repository": {
    "name": "xinference",
    "remote_url": "https://github.com/xorbitsai/inference.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "37c451d57978ec77784996d8c856e05dbe2f0c34",
    "working_tree": "source-clean-before-generated-skill-artifacts",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": "xinference",
      "version": "0.0.1.dev1+unknown.g37c451d57",
      "import_names": ["xinference"]
    }
  ],
  "evidence": {
    "source_roots": ["xinference/"],
    "docs": ["README.md", "READMES/", "doc/source/getting_started/", "doc/source/user_guide/", "doc/source/models/"],
    "tests": ["xinference/api/tests/", "xinference/client/tests/", "xinference/core/tests/", "xinference/model/**/tests/", "xinference/tests/"],
    "configs": ["pyproject.toml", ".github/workflows/python.yaml"],
    "scripts": ["build_backend.py", "build_web.py", "pyproject.toml console scripts"],
    "excluded_or_shallow": ["xinference/thirdparty/", "frontend/", "benchmark/", "monitor/", "doc/source/_static/"]
  }
}
```

## Refresh check

- If `git rev-parse HEAD` differs from the recorded commit, treat the skill as
  potentially stale.
- If public entry points, optional dependency groups, client signatures, API
  route behavior, model schemas, environment variables, or auth defaults change,
  refresh the skill even when the commit is otherwise close.
- Dirty path `skills/` records artifacts created by this construction workflow;
  it is not source evidence. Other dirty source paths should be treated as a
  possible staleness signal.
- If this skill is used with a released PyPI version rather than the recorded
  development version, verify the helper scripts and public signatures before
  applying version-sensitive details.
