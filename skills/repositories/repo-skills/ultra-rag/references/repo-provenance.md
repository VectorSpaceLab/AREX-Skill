# Repository Provenance

## Purpose

Read this before deciding whether this skill matches a checkout of UltraRAG.
If the commit, dirty state, package version, or major evidence paths differ from
this snapshot, run a refresh pass.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-15T07:39:24Z",
  "repository": {
    "name": "UltraRAG",
    "remote_url": "omitted-private-or-unknown",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "055ade445a100a9c43b215d5b17802672564574b",
    "working_tree": "dirty",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": "ultrarag",
      "version": "0.3.0.2",
      "import_names": ["ultrarag"]
    }
  ],
  "evidence": {
    "source_roots": ["src/ultrarag", "servers", "ui/backend"],
    "docs": ["README.md", "docs/README_zh.md", "docs/debug_rag_workflows_zh.md", "docs/llms.txt"],
    "examples": ["examples/demos", "examples/experiments"],
    "scripts": ["script"],
    "configs": ["pyproject.toml", ".github/workflows/ci-smoke.yml"]
  }
}
```

## Refresh check

- If the current `git rev-parse HEAD` differs from the commit above, refresh
  this skill.
- If the working tree dirty paths no longer look like a generated skill tree,
  refresh the skill before trusting it.
- If the package version or public entry point changes, refresh the skill even
  if the commit stays the same.
