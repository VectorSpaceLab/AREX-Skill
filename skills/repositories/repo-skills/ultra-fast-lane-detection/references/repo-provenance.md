# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of Ultra-Fast-Lane-Detection. If the current commit, dirty state, or key evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-18T14:31:16Z",
  "repository": {
    "name": "Ultra-Fast-Lane-Detection",
    "remote_url": "https://github.com/cfzd/Ultra-Fast-Lane-Detection.git",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "353df107756b8c03c22c27201e33fc63d84ecfe6",
    "working_tree": "dirty",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": null,
      "version": null,
      "import_names": ["model", "data", "utils", "evaluation"]
    }
  ],
  "evidence": {
    "source_roots": ["model", "data", "utils", "evaluation", "configs"],
    "docs": ["README.md", "INSTALL.md"],
    "examples": ["demo.py", "speed_simple.py", "speed_real.py", "export.py"],
    "tests": ["test.py"],
    "configs": ["configs/culane.py", "configs/tusimple.py"]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` changes, treat this skill as potentially stale and refresh it.
- If the working tree dirty paths change in a way that affects the repository workflows above, refresh it.
- If public config names, entry scripts, or import behavior change, refresh it even when the commit is unchanged.
