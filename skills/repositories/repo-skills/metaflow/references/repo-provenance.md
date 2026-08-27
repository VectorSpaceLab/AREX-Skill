# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of Metaflow. If the current repo commit, dirty state, package version, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-13T16:41:50Z",
  "repository": {
    "name": "metaflow",
    "remote_url": "https://github.com/Netflix/metaflow.git",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "4fce948c811aa4c9b9958f77367d527cf2695921",
    "working_tree": "dirty",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": "metaflow",
      "version": "2.19.37",
      "import_names": ["metaflow"]
    }
  ],
  "evidence": {
    "source_roots": ["metaflow"],
    "docs": ["README.md", "docs", "metaflow/tutorials"],
    "examples": ["metaflow/tutorials"],
    "tests": ["test"],
    "configs": ["setup.py", "setup.cfg", "tox.ini", ".pre-commit-config.yaml"],
    "scripts": ["metaflow-complete.sh", "devtools", "test/core/run_tests.py"]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from the recorded commit, treat the skill as potentially stale.
- If package metadata, public entry points, major decorator names, CLI command groups, or source roots changed, refresh even if the commit is otherwise close.
- The recorded dirty path is the repo-local `skills/` production output area, not evidence of a public package API change by itself.
