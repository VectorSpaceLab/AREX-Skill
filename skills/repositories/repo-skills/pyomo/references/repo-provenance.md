# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of the
repository. If the current repo commit, dirty state, package version, or major
evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-18T22:26:22Z",
  "repository": {
    "name": "pyomo",
    "remote_url": "omitted-private-or-unknown",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "2744a2446cc58598fb9bb53d41ad1b4bc5e86183",
    "working_tree": "dirty",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": "pyomo",
      "version": "6.10.2.dev0",
      "import_names": ["pyomo", "pyomo.environ"]
    }
  ],
  "evidence": {
    "source_roots": ["pyomo"],
    "docs": ["README.md", "doc/OnlineDocs"],
    "examples": ["examples"],
    "tests": ["pyomo/core/tests", "pyomo/scripting/tests", "pyomo/version/tests", "pyomo/contrib/*/tests"],
    "configs": ["pyproject.toml", "setup.py"]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as
  potentially stale and run `refresh-repo-skill`.
- If the current working tree is dirty and this snapshot was clean, or the
  snapshot was dirty and the current dirty paths differ, run
  `refresh-repo-skill`.
- If package metadata or public entry points changed even on the same commit,
  run `refresh-repo-skill`.
