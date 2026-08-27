# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of the Koalas repository. If the current repo commit, dirty state, package version, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-17T16:26:44Z",
  "repository": {
    "name": "koalas",
    "remote_url": "https://github.com/databricks/koalas.git",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "476518d0537f5b9fe844276aed3c916f7e945019",
    "working_tree": "dirty",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": "koalas",
      "version": "1.8.2",
      "import_names": ["databricks.koalas"]
    }
  ],
  "evidence": {
    "source_roots": ["databricks/koalas/"],
    "docs": [
      "README.md",
      "docs/source/getting_started/install.rst",
      "docs/source/getting_started/10min.ipynb",
      "docs/source/reference/",
      "docs/source/user_guide/"
    ],
    "examples": ["docs/source/getting_started/10min.ipynb"],
    "tests": ["databricks/koalas/tests/"],
    "configs": ["setup.py", "requirements-dev.txt", ".github/workflows/master.yml"],
    "scripts": ["dev/pytest", "dev/env_setup.sh"]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as potentially stale and run `refresh-repo-skill`.
- If the current working tree dirty paths include source, docs, tests, or package metadata changes not represented above, run `refresh-repo-skill`.
- If package metadata, public imports, optional extras, supported PySpark/Pandas/PyArrow/Numpy ranges, or major docs changed even on the same commit, run `refresh-repo-skill`.
- The dirty path in this snapshot is the generated skills area; it does not indicate uncommitted package source evidence.
