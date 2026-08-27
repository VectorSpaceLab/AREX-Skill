# Repository Provenance

## Purpose

Read this before deciding whether the skill is current for a checkout of the repository. If the current repo commit, dirty state,
package version, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-18T19:03:25Z",
  "repository": {
    "name": "petastorm",
    "remote_url": "omitted-private-or-unknown",
    "vcs": "git",
    "branch": "master",
    "tag": "v0.13.1",
    "commit": "01ba9cb7da8d8a6937e177aee39e241e10569d29",
    "working_tree": "dirty",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": "petastorm",
      "version": "0.13.1",
      "import_names": ["petastorm"]
    }
  ],
  "evidence": {
    "source_roots": ["petastorm/"],
    "docs": ["README.rst", "docs/"],
    "examples": ["examples/"],
    "tests": ["petastorm/tests/", "examples/*/tests/"],
    "configs": ["setup.py", "setup.cfg", ".github/workflows/unittest.yml"]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as potentially stale and run `refresh-repo-skill`.
- If the current working tree is dirty and this snapshot was clean, or the snapshot was dirty and the current dirty paths differ,
  run `refresh-repo-skill`.
- If package metadata or public entry points changed even on the same commit, run `refresh-repo-skill`.
