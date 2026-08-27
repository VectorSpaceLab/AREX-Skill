# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a Darkflow checkout. If the commit, branch, dirty state, or major evidence paths differ from this snapshot, regenerate the skill with refreshed evidence.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-15T06:28:42Z",
  "repository": {
    "name": "darkflow",
    "remote_url": "https://github.com/thtrieu/darkflow",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "eb7e830393f24233032b8578737141528be01d65",
    "working_tree": "dirty",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": "darkflow",
      "version": "1.0.0",
      "import_names": ["darkflow"]
    }
  ],
  "evidence": {
    "source_roots": ["darkflow"],
    "docs": ["README.md"],
    "examples": ["sample_img"],
    "tests": ["test"],
    "configs": ["cfg"]
  }
}
```

## Refresh check

- If `git rev-parse HEAD` changes, treat this skill as potentially stale.
- If the dirty paths change, recheck the skill before using it in a new checkout.
- If the package version or entry points change, refresh the skill even if the commit is the same.

## Evidence notes

- The repository exposes the `flow` CLI through `setup.py`.
- The public Python entry point verified during inspection is `darkflow.net.build.TFNet`.
- The package version is stored in `darkflow/version.py`, not re-exported from `darkflow.__init__`.
