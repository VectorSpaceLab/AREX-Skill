# Repository Provenance

## Purpose

Read this before deciding whether this skill still matches the current Promptify checkout. If the repository commit, dirty state, package version, or major evidence paths differ from this snapshot, refresh the skill.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-15T19:40:49Z",
  "repository": {
    "name": "Promptify",
    "remote_url": "https://github.com/promptslab/Promptify.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "bc5ed081a7a4d7be90e798dd48c324fd4c57bd2a",
    "working_tree": "clean",
    "dirty_paths": []
  },
  "packages": [
    {
      "name": "promptify",
      "version": "3.0.0",
      "import_names": ["promptify"]
    }
  ],
  "evidence": {
    "source_roots": ["promptify"],
    "docs": ["README.md", "docs"],
    "examples": ["examples"],
    "tests": ["tests"],
    "configs": ["pyproject.toml", "MANIFEST.in"]
  }
}
```

## Refresh check

- If the current `git rev-parse HEAD` differs from the commit above, refresh the skill.
- If the working tree is dirty and this snapshot was clean, refresh the skill.
- If the package version or public import surface changes, refresh the skill.
