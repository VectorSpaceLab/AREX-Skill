# Repository Provenance

## Purpose

Read this before deciding whether the DeepXiv SDK skill is current for a
checkout of the repository. If the current commit, dirty state, package version,
or public evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-23T08:52:08Z",
  "repository": {
    "name": "deepxiv_sdk",
    "remote_url": "https://github.com/qhjqhj00/deepxiv-sdk",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "b89034a037e027df9037e8344ee957eb0244e2d8",
    "working_tree": "clean",
    "dirty_paths": []
  },
  "packages": [
    {
      "name": "deepxiv-sdk",
      "version": "1.0.0",
      "import_names": ["deepxiv_sdk"]
    }
  ],
  "evidence": {
    "source_roots": ["deepxiv_sdk", "deepxiv_sdk/agent"],
    "docs": ["README.md", "USAGE.md", "README.zh.md", "USAGE.zh.md"],
    "examples": ["examples"],
    "tests": ["tests"],
    "configs": ["setup.py", "pyproject.toml", "MANIFEST.in"]
  }
}
```

## Refresh check

- If `git rev-parse HEAD` differs from the recorded commit, treat the skill as
  potentially stale and run `refresh-repo-skill`.
- If the current working tree is dirty and this snapshot was clean, or the
  changed paths differ from a future recorded baseline, refresh the skill.
- If `setup.py`, `pyproject.toml`, the `deepxiv_sdk` public exports, CLI entry
  points, or major Reader/Agent evidence paths change, refresh even when the
  commit comparison is unavailable.

The generated graph is self-contained: the evidence paths above identify the
source baseline only. They are not runtime dependencies and are not paths to
open during ordinary Researcher execution.
