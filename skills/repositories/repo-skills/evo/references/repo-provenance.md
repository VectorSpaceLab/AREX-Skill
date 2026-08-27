# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of the repository. If the current repo commit, dirty state, package version, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-16T12:19:58Z",
  "repository": {
    "name": "evo",
    "remote_url": "https://github.com/MichaelGrupp/evo.git",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "2a48b608db14e3dc84aebdf3b1b2478c5ae3ff47",
    "working_tree": "dirty",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": "evo",
      "version": "1.37.0",
      "import_names": ["evo"]
    }
  ],
  "evidence": {
    "source_roots": ["evo"],
    "docs": ["README.md", "doc"],
    "examples": ["examples"],
    "tests": ["test"],
    "configs": ["pyproject.toml", ".github/workflows/ci.yml"]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as potentially stale and run `refresh-repo-skill`.
- If the current working tree is dirty and this snapshot was clean, or the snapshot was dirty and the current dirty paths differ, run `refresh-repo-skill`.
- If package metadata or public entry points changed even on the same commit, run `refresh-repo-skill`.
