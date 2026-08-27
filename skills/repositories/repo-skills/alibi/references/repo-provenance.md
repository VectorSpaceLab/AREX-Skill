# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of the repository. If the current repo commit, dirty state, package version, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-18T18:55:45Z",
  "repository": {
    "name": "alibi",
    "remote_url": "https://github.com/SeldonIO/alibi.git",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "99c3421d7c971c85893625e37da1133e7ddf1779",
    "working_tree": "dirty",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": "alibi",
      "version": "0.9.7.dev0",
      "import_names": ["alibi"]
    }
  ],
  "evidence": {
    "source_roots": ["alibi"],
    "docs": ["README.md", "docs-gb/source", "doc/source"],
    "examples": ["examples"],
    "tests": ["alibi/**/tests"],
    "configs": ["setup.py", "setup.cfg", "MANIFEST.in", "requirements/"]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as potentially stale and run `refresh-repo-skill`.
- If the current working tree is dirty and this snapshot was clean, or the snapshot was dirty and the current dirty paths differ, run `refresh-repo-skill`.
- If package metadata or public entry points changed even on the same commit, run `refresh-repo-skill`.
