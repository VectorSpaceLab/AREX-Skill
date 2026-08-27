# Repository Provenance

## Purpose

Read this before deciding whether this skill matches a checkout of the Janus repository. If the commit, dirty state, package version, or major evidence paths differ from this snapshot, refresh the skill.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-11T13:58:11Z",
  "repository": {
    "name": "Janus",
    "remote_url": "https://github.com/deepseek-ai/Janus.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "1daa72fa409002d40931bd7b36a9280362469ead",
    "working_tree": "clean-before-skill-generation",
    "dirty_paths": []
  },
  "packages": [
    {
      "name": "janus",
      "version": "1.0.0",
      "import_names": ["janus"]
    }
  ],
  "evidence": {
    "source_roots": ["janus/models", "janus/janusflow/models", "janus/utils"],
    "docs": ["README.md", "pyproject.toml", "requirements.txt"],
    "examples": ["inference.py", "generation_inference.py", "interactivechat.py", "demo"],
    "tests": [],
    "configs": ["pyproject.toml", "requirements.txt"]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from the commit above, run a refresh.
- If the current checkout is dirty in a way that affects the public APIs or demos, run a refresh.
- If package metadata, optional dependencies, or public entry points change, run a refresh.
