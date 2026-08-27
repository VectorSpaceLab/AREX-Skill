# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of InvokeAI. If the current repo commit, dirty state, package version, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-06-24T00:00:00Z",
  "repository": {
    "name": "InvokeAI",
    "remote_url": "https://github.com/invoke-ai/InvokeAI",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "de66582b91929de0e4220619955ae43c04cd4a6d",
    "working_tree": "dirty",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": "InvokeAI",
      "version": "6.13.0.post1",
      "import_names": ["invokeai"]
    }
  ],
  "evidence": {
    "source_roots": ["invokeai"],
    "docs": ["README.md", "docs/src/generated/settings.json", "docs/src/generated/invocation-context.json"],
    "tests": ["tests"],
    "configs": ["invokeai/configs", "pyproject.toml"],
    "scripts": ["scripts", ".dev_scripts"],
    "excluded_or_deprioritized": ["invokeai/frontend/web", "coverage", "docker", ".github", "large model fixtures", "vendored/external image utility folders"]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as potentially stale and run `refresh-repo-skill`.
- If the current working tree dirty paths differ materially from this snapshot, run `refresh-repo-skill`.
- If `pyproject.toml`, console entry points, public API routers, invocation/node APIs, workflow record/session queue models, model manager taxonomy/configs, or generated docs JSON changed, run `refresh-repo-skill`.
