# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of DeepSearcher. If the repo commit, dirty state, package version, or major evidence paths differ from this snapshot, refresh the skill.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-14T17:18:56Z",
  "repository": {
    "name": "deep-searcher",
    "remote_url": "omitted-private-or-unknown",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "d89e37cdfbbef5e44ae6162ce9cc2c627a69b7e1",
    "working_tree": "dirty",
    "dirty_paths": [
      "skills/disco/deep-searcher",
      "skills/tests/deep-searcher"
    ]
  },
  "packages": [
    {
      "name": "deepsearcher",
      "version": "0.0.2",
      "import_names": ["deepsearcher"]
    }
  ],
  "evidence": {
    "source_roots": ["deepsearcher"],
    "docs": ["README.md", "docs"],
    "examples": ["examples"],
    "tests": ["tests"],
    "configs": ["deepsearcher/config.yaml", "pyproject.toml", "uv.lock"]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat this skill as potentially stale and refresh it.
- If the current working tree dirtiness differs materially from this snapshot, refresh it.
- If the package version or console script changes, refresh it even if the commit stays the same.
- If the public provider names, loader names, or evaluation entry points change, refresh it.
