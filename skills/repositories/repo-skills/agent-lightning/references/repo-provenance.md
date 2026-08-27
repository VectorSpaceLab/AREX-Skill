# Repository Provenance

## Purpose

Read this before deciding whether this skill matches a checkout of the Agent Lightning repository. If the commit, working tree state, package metadata, or key evidence roots differ from this snapshot, refresh the skill instead of assuming it is current.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-11T15:49:54Z",
  "repository": {
    "name": "agent-lightning",
    "remote_url": "https://github.com/microsoft/agent-lightning.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "f0a77cfad71e6222a3edb7dfc7a0f611bd231364",
    "working_tree": "dirty",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": "agentlightning",
      "version": "0.3.1",
      "import_names": ["agentlightning"]
    }
  ],
  "evidence": {
    "source_roots": ["agentlightning"],
    "docs": ["README.md", "docs"],
    "examples": ["examples"],
    "tests": ["tests"],
    "configs": ["pyproject.toml", "uv.lock", "mkdocs.yml"]
  }
}
```

## Refresh check

- If the repository commit changes, refresh this skill.
- If the checkout becomes clean or acquires different dirty paths than this snapshot, refresh this skill.
- If the public package version or entry points change, refresh this skill.
- If the bundled evidence roots move or are renamed, refresh this skill.

## Notes

- The working tree was dirty during generation because generated skill artifacts were created under `skills/`.
- This snapshot intentionally omits local absolute paths, virtualenv names, cache directories, and activation commands.
