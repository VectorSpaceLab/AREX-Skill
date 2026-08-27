# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of BlenderGIS. If the current repo commit, dirty state, package version, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-13T17:00:32Z",
  "repository": {
    "name": "BlenderGIS",
    "remote_url": "https://github.com/domlysz/BlenderGIS.git",
    "vcs": "git",
    "branch": "master",
    "tag": "2215",
    "commit": "2add45ffec547f419cc77563a7fe976fd6c8f0c4",
    "working_tree": "dirty",
    "dirty_paths": ["skills/"],
    "dirty_note": "The runtime skill and review artifacts live under skills/ and were excluded from source behavior evidence."
  },
  "packages": [
    {
      "name": "BlenderGIS",
      "version": "2.2.14",
      "import_names": ["BlenderGIS"]
    }
  ],
  "evidence": {
    "source_roots": ["__init__.py", "prefs.py", "geoscene.py", "core/", "operators/"],
    "docs": ["README.md"],
    "examples": [],
    "tests": [],
    "configs": ["core/settings.json"],
    "runtime_assets": ["icons/", "operators/rsrc/gradients/"],
    "excluded": [".git/", "skills/tests/", "skills/BlenderGIS.log", "clients/QtMapServiceClient.py"]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as potentially stale and run `refresh-repo-skill`.
- If the current working tree has source changes outside `skills/`, run `refresh-repo-skill`.
- If BlenderGIS `bl_info.version`, operator IDs, feature flags, public menu layout, optional dependency checks, or major evidence paths changed, run `refresh-repo-skill`.
- If Blender major-version support changes beyond the recorded `bl_info.blender` guard, refresh before relying on version-specific UI/operator behavior.
