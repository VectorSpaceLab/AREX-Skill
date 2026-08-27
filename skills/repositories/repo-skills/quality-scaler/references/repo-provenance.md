# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of QualityScaler. If the commit, dirty state, package version, or evidence paths differ from this snapshot, refresh the skill.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-17T19:18:14Z",
  "repository": {
    "name": "QualityScaler",
    "remote_url": "https://github.com/Djdefrag/QualityScaler.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "884f42b9b7150b9f7f6d9ffda8c93d561d63a696",
    "working_tree": "dirty",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": "QualityScaler",
      "version": "2026.3",
      "import_names": ["QualityScaler"]
    }
  ],
  "evidence": {
    "source_roots": ["QualityScaler.py"],
    "docs": ["README.md"],
    "examples": ["README.md"],
    "tests": [],
    "configs": ["requirements.txt", "AI-onnx/", "Assets/"]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as potentially stale and refresh it.
- If the working tree dirty paths differ materially from this snapshot, refresh it.
- If public runtime dependencies, supported assets, or entry-point behavior change, refresh it even on the same commit.
