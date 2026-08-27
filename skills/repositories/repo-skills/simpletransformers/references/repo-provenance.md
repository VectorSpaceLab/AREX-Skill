# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of Simple Transformers. If the current repo commit, dirty state, package version, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-16T12:25:23Z",
  "repository": {
    "name": "simpletransformers",
    "remote_url": "https://github.com/ThilinaRajapakse/simpletransformers.git",
    "vcs": "git",
    "branch": "master",
    "tag": "v0.70.8",
    "commit": "d0e35ee1d732100ee85bea7c3ddbf13b0e0879eb",
    "working_tree": "generated-skill-output-dirty",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": "simpletransformers",
      "version": "0.70.8",
      "import_names": ["simpletransformers"]
    }
  ],
  "evidence": {
    "source_roots": ["simpletransformers/"],
    "docs": ["README.md", "docs/_docs/"],
    "examples": ["examples/"],
    "tests": ["tests/"],
    "scripts": ["bin/simple-viewer"]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from the commit above, treat this skill as potentially stale and run `refresh-repo-skill`.
- If package metadata, public imports, task model constructors, or docs/examples/tests changed, refresh the skill even on the same commit.
- If dependency compatibility with Hugging Face Transformers changes, refresh the troubleshooting and environment guidance.
