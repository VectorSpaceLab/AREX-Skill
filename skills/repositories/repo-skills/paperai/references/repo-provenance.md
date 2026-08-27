# Repository Provenance

Read this before deciding whether the skill is current for a checkout of
paperai. If the commit, package metadata, or public evidence paths differ,
refresh the repo skill.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-20T17:19:51Z",
  "repository": {
    "name": "paperai",
    "remote_url": "https://github.com/neuml/paperai",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "18306961a6ba5d45551d7e10d9ab3668c6b402b3",
    "working_tree": "dirty",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": "paperai",
      "version": "2.6.0",
      "import_names": ["paperai"]
    }
  ],
  "evidence": {
    "source_roots": ["src/python/paperai"],
    "docs": ["README.md", "setup.py"],
    "examples": ["examples/crc.yml", "examples/search.py", "examples/*.ipynb"],
    "tests": ["test/python"],
    "configs": ["pyproject.toml", "docker/Dockerfile"]
  }
}
```

## Refresh check

- If `git rev-parse HEAD` differs from the snapshot commit, run
  `refresh-repo-skill`.
- This snapshot was generated from a dirty checkout because the output is under
  `skills/`; changes outside that generated tree should trigger a refresh.
- Recheck the public `paperai` entry points and `setup.py` dependencies if the
  package version or source roots change.
