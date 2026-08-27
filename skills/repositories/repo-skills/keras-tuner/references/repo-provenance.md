# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of the
repository. If the current repo commit, dirty state, package version, or major
evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-19T05:46:07Z",
  "repository": {
    "name": "keras-tuner",
    "remote_url": "omitted-private-or-unknown",
    "vcs": "git",
    "branch": "master",
    "tag": "v1.4.8",
    "commit": "48f671490201f6b873e4d27dee8df6f406256ca4",
    "working_tree": "dirty",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": "keras-tuner",
      "version": "1.4.8",
      "import_names": ["keras_tuner"]
    }
  ],
  "evidence": {
    "source_roots": ["keras_tuner"],
    "docs": ["README.md", "docs/site"],
    "tests": ["keras_tuner/*_test.py", "keras_tuner/integration_tests"],
    "configs": ["pyproject.toml", "setup.cfg", "setup.py"]
  }
}
```
The snapshot intentionally records a dirty working tree because the generated
runtime output under `skills/` was present when this skill was produced. The
`dirty_paths` value is relative to the repository root; do not treat the
presence of this skill's own generated files as source-package drift by itself.
Refresh only when the commit, package/public-entry-point evidence, or the
relevant dirty paths no longer match this snapshot.

## Refresh Check


- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as
  potentially stale and run `refresh-repo-skill`.
- If the current working tree is dirty and this snapshot was clean, or the
  snapshot was dirty and the current dirty paths differ, run
  `refresh-repo-skill`.
- If package metadata or public entry points changed even on the same commit,
  run `refresh-repo-skill`.
