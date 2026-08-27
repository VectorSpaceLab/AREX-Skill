# Repository Provenance

## Purpose

Read this before deciding whether the skill matches the current `opyrator` repository checkout. If the commit, branch, package version, or evidence paths differ materially, refresh the skill.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-17T19:47:38Z",
  "repository": {
    "name": "opyrator",
    "remote_url": "omitted-private-or-unknown",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "3f443f05b6b21f00685c2b9bba16cf080edf2385",
    "working_tree": "clean",
    "dirty_paths": []
  },
  "packages": [
    {
      "name": "opyrator",
      "version": "0.0.12",
      "import_names": ["opyrator"]
    }
  ],
  "evidence": {
    "source_roots": ["src/opyrator"],
    "docs": ["README.md", "docs"],
    "examples": ["examples"],
    "tests": ["tests"],
    "configs": ["pyproject.toml", "setup.py", "setup.cfg", "Pipfile"]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from the recorded commit, refresh the skill.
- If the branch or package version changes materially, refresh the skill.
- If the package surface changes so that CLI commands, service helpers, or UI helpers no longer match the references, refresh the skill.
- If new evidence paths become the primary source of truth, refresh the skill.
