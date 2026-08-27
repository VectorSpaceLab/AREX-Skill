# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of PyMC. If the current repo commit, package version, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-13T00:00:00Z",
  "repository": {
    "name": "pymc",
    "remote_url": "https://github.com/pymc-devs/pymc.git",
    "vcs": "git",
    "branch": "main",
    "tag": "v6.3.0",
    "commit": "6b4b6771bd2685638dd0499e240c3d5b90f95e2d",
    "working_tree": "dirty-generated-skill-and-inspection-artifacts",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {"name": "pymc", "version": "6.3.0", "import_names": ["pymc"]},
    {"name": "pytensor", "version": "3.2.4", "import_names": ["pytensor"]}
  ],
  "evidence": {
    "source_roots": ["pymc/"],
    "docs": ["README.rst", "docs/source/installation.md", "docs/source/learn/usage_overview.rst", "docs/source/api/"],
    "tests": ["tests/test_data.py", "tests/distributions/test_custom.py", "tests/sampling/test_mcmc.py", "tests/ode/test_ode.py", "tests/variational/test_inference.py"],
    "configs": ["pyproject.toml", "setup.py", "requirements.txt", "requirements-dev.txt", "conda-envs/environment-test.yml", "conda-envs/environment-alternative-backends.yml"],
    "scripts_inventory": ["scripts/"]
  }
}
```

## Refresh check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as potentially stale and run `refresh-repo-skill`.
- If non-skill source, docs, tests, dependencies, examples, or public API signatures changed, run `refresh-repo-skill`.
- If only generated skill review artifacts changed under `skills/`, this provenance remains aligned with the same source snapshot.
